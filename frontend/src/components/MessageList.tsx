import { useEffect, useRef } from 'react'
import { useApp } from '../context/AppContext'

export function MessageList() {
  const { state } = useApp()
  const bottomRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [state.messages])

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
              <p
                className={`mt-1 text-[10px] ${
                  msg.role === 'user' ? 'text-white/60' : 'text-text-muted'
                }`}
              >
                {new Date(msg.created_at + 'Z').toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </p>
            </div>
          </div>
        ))}
        <div ref={bottomRef} />
      </div>
    </div>
  )
}
