import { useApp } from '../context/AppContext'

function toLocalTime(iso: string) {
  return new Date(iso + 'Z').toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
}

export function SessionBar() {
  const { state, selectSession, createSession } = useApp()

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
    </div>
  )
}
