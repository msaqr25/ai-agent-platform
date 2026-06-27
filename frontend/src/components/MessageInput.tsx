import { useState, useRef, useEffect, useCallback } from 'react'
import { useApp } from '../context/AppContext'

type RecorderState = 'idle' | 'recording' | 'sending'

export function MessageInput() {
  const { state, sendMessage, sendVoiceMessage } = useApp()
  const [text, setText] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const [sending, setSending] = useState(false)
  const [recorderState, setRecorderState] = useState<RecorderState>('idle')
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const streamRef = useRef<MediaStream | null>(null)
  const chunksRef = useRef<Blob[]>([])

  // Release the microphone and MediaRecorder so the mic indicator turns off
  // and resources are freed when the component unmounts or recording ends.
  const cleanupMedia = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop()
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop())
      streamRef.current = null
    }
    mediaRecorderRef.current = null
    chunksRef.current = []
  }, [])

  useEffect(() => {
    return cleanupMedia
  }, [cleanupMedia])

  const canSend = state.selectedSession && text.trim() && !sending && recorderState === 'idle'
  const canRecord = state.selectedSession && recorderState === 'idle' && !sending

  const handleSend = async () => {
    if (!canSend) return
    const content = text.trim()
    setText('')
    setSending(true)
    try {
      await sendMessage(content)
    } finally {
      setSending(false)
      inputRef.current?.focus()
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
      streamRef.current = stream
      chunksRef.current = []

      // Prefer webm (widely supported in Chromium-based browsers);
      // fall back to mp4 for Safari.
      const mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4'
      const recorder = new MediaRecorder(stream, { mimeType })

      // Collect audio chunks as they arrive from the MediaRecorder.
      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) chunksRef.current.push(e.data)
      }

      // When recording stops, assemble chunks into a Blob and send it.
      recorder.onstop = async () => {
        setRecorderState('sending')
        const blob = new Blob(chunksRef.current, { type: mimeType })
        try {
          await sendVoiceMessage(blob)
        } finally {
          setRecorderState('idle')
          inputRef.current?.focus()
        }
      }

      mediaRecorderRef.current = recorder
      recorder.start()
      setRecorderState('recording')
    } catch {
      setRecorderState('idle')
    }
  }

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop()
      cleanupMedia()
    }
  }

  const toggleRecording = () => {
    if (recorderState === 'recording') {
      stopRecording()
    } else {
      startRecording()
    }
  }

  return (
    <div className="border-t border-border bg-dark-800 px-6 py-4">
      <div className="mx-auto flex max-w-3xl items-end gap-3">
        <textarea
          ref={inputRef}
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={handleKeyDown}
          rows={1}
          placeholder={state.selectedSession ? 'Type a message...' : 'Select a session to start chatting'}
          disabled={!state.selectedSession || recorderState === 'recording'}
          className="max-h-32 min-h-[44px] flex-1 resize-none rounded-xl border border-border bg-dark-700 px-4 py-3 text-sm text-text-primary placeholder-text-muted outline-none transition-colors focus:border-accent focus:ring-1 focus:ring-accent disabled:cursor-not-allowed disabled:opacity-50"
        />
        <button
          onClick={toggleRecording}
          disabled={!canRecord && recorderState !== 'recording'}
          className={`flex h-[44px] w-[44px] shrink-0 items-center justify-center rounded-xl transition-colors disabled:cursor-not-allowed disabled:opacity-50 ${
            recorderState === 'recording'
              ? 'bg-danger text-white hover:bg-red-600'
              : 'bg-dark-600 text-text-secondary hover:bg-dark-500'
          }`}
          title={recorderState === 'recording' ? 'Stop recording' : 'Record voice message'}
        >
          {recorderState === 'sending' ? (
            <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : recorderState === 'recording' ? (
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <rect x="6" y="6" width="12" height="12" rx="2" fill="currentColor" />
            </svg>
          ) : (
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-14 0M12 2a4 4 0 00-4 4v5a4 4 0 008 0V6a4 4 0 00-4-4zM8 19h8" />
            </svg>
          )}
        </button>
        <button
          onClick={handleSend}
          disabled={!canSend}
          className="flex h-[44px] w-[44px] shrink-0 items-center justify-center rounded-xl bg-accent text-white transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
          title="Send message"
        >
          {sending ? (
            <svg className="h-5 w-5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
            </svg>
          ) : (
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 12h14M12 5l7 7-7 7" />
            </svg>
          )}
        </button>
      </div>
    </div>
  )
}
