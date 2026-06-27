import { useState } from 'react'
import { useApp } from '../context/AppContext'
import { Modal } from './Modal'

export function Sidebar() {
  const { state, selectAgent, createAgent, toggleSidebar } = useApp()
  const [showNewAgent, setShowNewAgent] = useState(false)
  const [newName, setNewName] = useState('')
  const [newPrompt, setNewPrompt] = useState('')
  const [creating, setCreating] = useState(false)

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!newName.trim()) return
    setCreating(true)
    try {
      await createAgent(newName.trim(), newPrompt.trim())
      setNewName('')
      setNewPrompt('')
      setShowNewAgent(false)
    } catch {
      // error is shown via context
    } finally {
      setCreating(false)
    }
  }

  return (
    <>
      <aside
        className={`flex h-full flex-col border-r border-border bg-dark-800 transition-all duration-200 ${
          state.sidebarOpen ? 'w-72' : 'w-0 overflow-hidden'
        }`}
      >
        <div className="flex items-center justify-between border-b border-border px-4 py-3">
          {state.sidebarOpen && <h1 className="text-sm font-semibold uppercase tracking-wider text-text-muted">Agents</h1>}
          <button
            onClick={toggleSidebar}
            className="rounded p-1.5 text-text-muted hover:bg-dark-600 hover:text-text-primary"
            title="Toggle sidebar"
          >
            <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 19l-7-7 7-7m8 14l-7-7 7-7" />
            </svg>
          </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 py-2">
          {state.agents.length === 0 && !state.isLoading && (
            <p className="px-2 text-sm text-text-muted">No agents yet</p>
          )}
          {state.agents.map((agent) => (
            <button
              key={agent.id}
              onClick={() => selectAgent(agent)}
              className={`w-full rounded-lg px-3 py-2.5 text-left text-sm transition-colors ${
                state.selectedAgent?.id === agent.id
                  ? 'bg-accent/20 text-accent-light'
                  : 'text-text-secondary hover:bg-dark-600 hover:text-text-primary'
              }`}
            >
              <div className="truncate font-medium">{agent.name}</div>
              <div className="mt-0.5 truncate text-xs text-text-muted">
                {agent.prompt.slice(0, 60)}{agent.prompt.length > 60 ? '...' : ''}
              </div>
            </button>
          ))}
        </div>

        <div className="border-t border-border p-3">
          <button
            onClick={() => setShowNewAgent(true)}
            className="flex w-full items-center justify-center gap-2 rounded-lg bg-accent px-3 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover"
          >
            <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
            </svg>
            New Agent
          </button>
        </div>
      </aside>

      <Modal open={showNewAgent} onClose={() => setShowNewAgent(false)} title="Create Agent">
        <form onSubmit={handleCreate} className="space-y-4">
          <div>
            <label className="mb-1 block text-sm text-text-secondary">Name</label>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              className="w-full rounded-lg border border-border bg-dark-700 px-3 py-2 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent focus:ring-1 focus:ring-accent"
              placeholder="Agent name"
              autoFocus
              required
            />
          </div>
          <div>
            <label className="mb-1 block text-sm text-text-secondary">Prompt</label>
            <textarea
              value={newPrompt}
              onChange={(e) => setNewPrompt(e.target.value)}
              rows={4}
              className="w-full resize-none rounded-lg border border-border bg-dark-700 px-3 py-2 text-sm text-text-primary placeholder-text-muted outline-none focus:border-accent focus:ring-1 focus:ring-accent"
              placeholder="You are a helpful AI assistant..."
            />
          </div>
          <div className="flex justify-end gap-2">
            <button
              type="button"
              onClick={() => setShowNewAgent(false)}
              className="rounded-lg px-4 py-2 text-sm text-text-secondary transition-colors hover:bg-dark-600 hover:text-text-primary"
            >
              Cancel
            </button>
            <button
              type="submit"
              disabled={creating || !newName.trim()}
              className="rounded-lg bg-accent px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
            >
              {creating ? 'Creating...' : 'Create'}
            </button>
          </div>
        </form>
      </Modal>
    </>
  )
}
