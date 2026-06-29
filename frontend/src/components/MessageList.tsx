import { useEffect, useRef, useState } from 'react'
import { useApp } from '../context/AppContext'

export function MessageList() {
  const { state, consumePendingPlayback, loadMoreMessages } = useApp()
  const bottomRef = useRef<HTMLDivElement>(null)
  const [playingId, setPlayingId] = useState<number | null>(null)
  const audioRef = useRef<HTMLAudioElement | null>(null)
  const prevLastMessageIdRef = useRef<number | null>(null)

  useEffect(() => {
    const lastId = state.messages[state.messages.length - 1]?.id ?? null
    const prevLastId = prevLastMessageIdRef.current
    prevLastMessageIdRef.current = lastId
    if (prevLastId !== null && lastId !== null && lastId !== prevLastId) {
      bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
    }
  }, [state.messages])

  // After a voice message is sent, auto-play the assistant's TTS audio.
  // consumePendingPlayback returns the id once and clears it to prevent repeats.
  useEffect(() => {
    const msgId = consumePendingPlayback()
    if (msgId === null) return
    const msg = state.messages.find((m) => m.id === msgId)
    if (!msg?.audio_file) return
    playAudio(msg.id, msg.audio_file.file_path)
  }, [state.messages, consumePendingPlayback])

  const playAudio = (msgId: number, filePath: string) => {
    if (audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
    }

    const audio = new Audio(filePath)
    audio.onended = () => {
      setPlayingId(null)
      audioRef.current = null
    }
    audio.onerror = () => {
      setPlayingId(null)
      audioRef.current = null
    }
    audio.play()
    audioRef.current = audio
    setPlayingId(msgId)
  }

  const togglePlay = (msgId: number, filePath: string) => {
    if (playingId === msgId && audioRef.current) {
      audioRef.current.pause()
      audioRef.current = null
      setPlayingId(null)
      return
    }

    playAudio(msgId, filePath)
  }

  if (!state.selectedSession) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-sm text-text-muted">
          {state.selectedAgent ? 'Create a new session to begin' : 'Select an agent to get started'}
        </p>
      </div>
    )
  }

  if (state.messages.length === 0) {
    return (
      <div className="flex flex-1 items-center justify-center">
        <p className="text-sm text-text-muted">No messages yet. Start a conversation!</p>
      </div>
    )
  }

  return (
    <div className="flex-1 overflow-y-auto px-6 py-4">
      <div className="mx-auto max-w-3xl space-y-4">
        {state.messagesTotal > state.messages.length && (
          <div className="flex justify-center">
            <button
              onClick={loadMoreMessages}
              className="rounded-lg px-4 py-2 text-xs font-medium text-accent transition-colors hover:bg-dark-600"
            >
              Load older messages ({state.messages.length} of {state.messagesTotal})
            </button>
          </div>
        )}
        {state.messages.map((msg) => (
          <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div
              className={`max-w-[75%] rounded-2xl px-4 py-2.5 text-sm leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-user-bubble text-white'
                  : 'bg-assistant-bubble text-text-primary'
              }`}
            >
              <p className="whitespace-pre-wrap break-words">{msg.content}</p>
              <div className="mt-1 flex items-center gap-2">
                {msg.audio_file && (
                  <button
                    onClick={() => togglePlay(msg.id, msg.audio_file!.file_path)}
                    className="flex h-6 w-6 items-center justify-center rounded-full bg-dark-600 text-text-secondary transition-colors hover:bg-dark-500 hover:text-text-primary"
                    title={playingId === msg.id ? 'Pause' : 'Play audio'}
                  >
                    {playingId === msg.id ? (
                      <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
                        <rect x="6" y="4" width="4" height="16" rx="1" />
                        <rect x="14" y="4" width="4" height="16" rx="1" />
                      </svg>
                    ) : (
                      <svg className="h-3 w-3" fill="currentColor" viewBox="0 0 24 24">
                        <path d="M8 5v14l11-7z" />
                      </svg>
                    )}
                  </button>
                )}
                <p
                  className={`text-[10px] ${msg.role === 'user' ? 'text-white/60' : 'text-text-muted'}`}
                >
                  {new Date(msg.created_at + 'Z').toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                </p>
              </div>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
