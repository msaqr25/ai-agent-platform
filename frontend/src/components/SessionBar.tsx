import { useState } from 'react'
import { useApp } from '../context/AppContext'
import { ConfirmDialog } from './ConfirmDialog'

function toLocalTime(iso: string) {
  return new Date(iso + 'Z').toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function SessionBar() {
  const { state, selectSession, createSession, deleteSession } = useApp()
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false)
  const [deleting, setDeleting] = useState(false)

  const sortedSessions = [...state.sessions].sort(
    (a, b) => new Date(b.updated_at + 'Z').getTime() - new Date(a.updated_at + 'Z').getTime()
  )

  if (!state.selectedAgent) {
    return (
      <div className="flex items-center border-b border-border bg-dark-800 px-6 py-3">
        <p className="text-sm text-text-muted">Select an agent to start chatting</p>
      </div>
    )
  }

  return (
    <div className="flex items-center gap-3 border-b border-border bg-dark-800 px-6 py-3">
      <div className="flex items-center gap-2">
        <span className="text-sm font-medium text-text-primary">{state.selectedAgent.name}</span>
        <span className="text-text-muted">/</span>
      </div>
      <select
        value={state.selectedSession?.id ?? ''}
        onChange={(e) => {
          const session = state.sessions.find((s) => s.id === Number(e.target.value))
          if (session) selectSession(session)
        }}
        className="flex-1 rounded-lg border border-border bg-dark-700 px-3 py-1.5 text-sm text-text-primary outline-none focus:border-accent focus:ring-1 focus:ring-accent"
      >
        {state.sessions.length === 0 && <option value="">No sessions</option>}
        {sortedSessions.map((session) => (
          <option key={session.id} value={session.id}>
            {session.title} — {toLocalTime(session.updated_at)}
          </option>
        ))}
      </select>
      <button
        onClick={createSession}
        disabled={!state.selectedAgent}
        className="flex items-center gap-1.5 rounded-lg bg-accent px-3 py-1.5 text-sm font-medium text-white transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
        title="New session"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
        </svg>
        New
      </button>
      <button
        onClick={() => setShowDeleteConfirm(true)}
        disabled={!state.selectedSession}
        className="flex items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm font-medium text-text-muted transition-colors hover:bg-dark-600 hover:text-danger disabled:cursor-not-allowed disabled:opacity-50"
        title="Delete session"
      >
        <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
        </svg>
      </button>

      <ConfirmDialog
        open={showDeleteConfirm}
        title="Delete Session"
        message={`Are you sure you want to delete "${state.selectedSession?.title}"? All messages in this session will be lost.`}
        onConfirm={async () => {
          if (!state.selectedSession) return
          setDeleting(true)
          try {
            await deleteSession(state.selectedSession.id)
          } finally {
            setDeleting(false)
            setShowDeleteConfirm(false)
          }
        }}
        onCancel={() => setShowDeleteConfirm(false)}
        loading={deleting}
      />
    </div>
  )
}
