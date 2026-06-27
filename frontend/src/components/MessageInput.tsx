import { useState, useRef } from 'react'
import { useApp } from '../context/AppContext'

export function MessageInput() {
  const { state, sendMessage } = useApp()
  const [text, setText] = useState('')
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const [sending, setSending] = useState(false)

  const canSend = state.selectedSession && text.trim() && !sending

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
          disabled={!state.selectedSession}
          className="max-h-32 min-h-[44px] flex-1 resize-none rounded-xl border border-border bg-dark-700 px-4 py-3 text-sm text-text-primary placeholder-text-muted outline-none transition-colors focus:border-accent focus:ring-1 focus:ring-accent disabled:cursor-not-allowed disabled:opacity-50"
        />
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
