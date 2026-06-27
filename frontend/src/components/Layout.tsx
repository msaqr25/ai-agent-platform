import { useApp } from '../context/AppContext'
import { Sidebar } from './Sidebar'
import { SessionBar } from './SessionBar'
import { MessageList } from './MessageList'
import { MessageInput } from './MessageInput'

export function Layout() {
  const { state, toggleSidebar, clearError } = useApp()

  return (
    <div className="flex h-screen">
      <Sidebar />

      <div className="flex flex-1 flex-col">
        {state.error && (
          <div className="flex items-center gap-2 bg-danger/10 px-6 py-2 text-sm text-danger">
            <span className="flex-1">{state.error}</span>
            <button onClick={clearError} className="text-danger/70 hover:text-danger">
              <svg className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        )}

        {!state.sidebarOpen && (
          <div className="border-b border-border bg-dark-800 px-4 py-2">
            <button
              onClick={toggleSidebar}
              className="rounded p-1.5 text-text-muted hover:bg-dark-600 hover:text-text-primary"
              title="Open sidebar"
            >
              <svg className="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 5l7 7-7 7M5 5l7 7-7 7" />
              </svg>
            </button>
          </div>
        )}

        <SessionBar />
        <MessageList />
        <MessageInput />
      </div>
    </div>
  )
}
