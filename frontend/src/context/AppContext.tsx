import { createContext, useContext, useReducer, useCallback, useRef, type ReactNode } from 'react'
import { api } from '../api/client'
import type { AgentResponse, ChatSessionResponse, MessageResponse } from '../types'

interface AppState {
  agents: AgentResponse[]
  selectedAgent: AgentResponse | null
  sessions: ChatSessionResponse[]
  selectedSession: ChatSessionResponse | null
  messages: MessageResponse[]
  sidebarOpen: boolean
  isLoading: boolean
  error: string | null
}

type Action =
  | { type: 'SET_AGENTS'; payload: AgentResponse[] }
  | { type: 'UPDATE_AGENT'; payload: AgentResponse }
  | { type: 'REMOVE_AGENT'; payload: number }
  | { type: 'SET_SELECTED_AGENT'; payload: AgentResponse | null }
  | { type: 'SET_SESSIONS'; payload: ChatSessionResponse[] }
  | { type: 'SET_SELECTED_SESSION'; payload: ChatSessionResponse | null }
  | { type: 'REMOVE_SESSION'; payload: number }
  | { type: 'SET_MESSAGES'; payload: MessageResponse[] }
  | { type: 'APPEND_MESSAGES'; payload: [MessageResponse, MessageResponse] }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'APPEND_VOICE_MESSAGES'; payload: { user_message: MessageResponse; assistant_message: MessageResponse } }

const initialState: AppState = {
  agents: [],
  selectedAgent: null,
  sessions: [],
  selectedSession: null,
  messages: [],
  sidebarOpen: true,
  isLoading: false,
  error: null,
}

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_AGENTS':
      return { ...state, agents: action.payload }
    case 'UPDATE_AGENT':
      return {
        ...state,
        agents: state.agents.map((a) => (a.id === action.payload.id ? action.payload : a)),
        selectedAgent: state.selectedAgent?.id === action.payload.id ? action.payload : state.selectedAgent,
      }
    case 'REMOVE_AGENT':
      return {
        ...state,
        agents: state.agents.filter((a) => a.id !== action.payload),
        selectedAgent: state.selectedAgent?.id === action.payload ? null : state.selectedAgent,
        sessions: state.selectedAgent?.id === action.payload ? [] : state.sessions,
        selectedSession: state.selectedAgent?.id === action.payload ? null : state.selectedSession,
        messages: state.selectedAgent?.id === action.payload ? [] : state.messages,
      }
    case 'SET_SELECTED_AGENT':
      return { ...state, selectedAgent: action.payload }
    case 'SET_SESSIONS':
      return { ...state, sessions: action.payload }
    case 'SET_SELECTED_SESSION':
      return { ...state, selectedSession: action.payload }
    case 'REMOVE_SESSION':
      return {
        ...state,
        sessions: state.sessions.filter((s) => s.id !== action.payload),
        selectedSession: state.selectedSession?.id === action.payload ? null : state.selectedSession,
        messages: state.selectedSession?.id === action.payload ? [] : state.messages,
      }
    case 'SET_MESSAGES':
      return { ...state, messages: action.payload }
    case 'APPEND_MESSAGES':
      return { ...state, messages: [...state.messages, action.payload[0], action.payload[1]] }
    case 'APPEND_VOICE_MESSAGES':
      return {
        ...state,
        messages: [...state.messages, action.payload.user_message, action.payload.assistant_message],
      }
    case 'TOGGLE_SIDEBAR':
      return { ...state, sidebarOpen: !state.sidebarOpen }
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload }
    case 'SET_ERROR':
      return { ...state, error: action.payload }
    default:
      return state
  }
}

interface AppContextValue {
  state: AppState
  loadAgents: () => Promise<void>
  selectAgent: (agent: AgentResponse) => Promise<void>
  createAgent: (name: string, prompt: string) => Promise<void>
  updateAgent: (id: number, name: string, prompt: string) => Promise<void>
  deleteAgent: (id: number) => Promise<void>
  selectSession: (session: ChatSessionResponse) => Promise<void>
  createSession: () => Promise<void>
  deleteSession: (id: number) => Promise<void>
  sendMessage: (content: string) => Promise<void>
  sendVoiceMessage: (audioBlob: Blob) => Promise<void>
  toggleSidebar: () => void
  clearError: () => void
  consumePendingPlayback: () => number | null
}

const AppContext = createContext<AppContextValue | null>(null)

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(reducer, initialState)
  const abortRef = useRef<AbortController | null>(null)
  const pendingPlaybackRef = useRef<number | null>(null)

  const loadAgents = useCallback(async () => {
    dispatch({ type: 'SET_LOADING', payload: true })
    dispatch({ type: 'SET_ERROR', payload: null })
    try {
      const agents = await api.agents.list()
      dispatch({ type: 'SET_AGENTS', payload: agents })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to load agents' })
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }, [])

  const selectAgent = useCallback(async (agent: AgentResponse) => {
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = new AbortController()

    dispatch({ type: 'SET_SELECTED_AGENT', payload: agent })
    dispatch({ type: 'SET_SELECTED_SESSION', payload: null })
    dispatch({ type: 'SET_MESSAGES', payload: [] })
    dispatch({ type: 'SET_LOADING', payload: true })
    dispatch({ type: 'SET_ERROR', payload: null })

    try {
      const sessions = await api.sessions.listForAgent(agent.id)
      dispatch({ type: 'SET_SESSIONS', payload: sessions })
      if (sessions.length > 0) {
        const firstSession = sessions[0]
        dispatch({ type: 'SET_SELECTED_SESSION', payload: firstSession })
        const messages = await api.messages.list(firstSession.id)
        dispatch({ type: 'SET_MESSAGES', payload: messages })
      }
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to load sessions' })
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }, [])

  const createAgent = useCallback(async (name: string, prompt: string) => {
    dispatch({ type: 'SET_ERROR', payload: null })
    try {
      await api.agents.create({ name, prompt: prompt || undefined })
      const agents = await api.agents.list()
      dispatch({ type: 'SET_AGENTS', payload: agents })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to create agent' })
      throw e
    }
  }, [])

  const updateAgent = useCallback(async (id: number, name: string, prompt: string) => {
    dispatch({ type: 'SET_ERROR', payload: null })
    try {
      const updated = await api.agents.update(id, { name, prompt })
      dispatch({ type: 'UPDATE_AGENT', payload: updated })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to update agent' })
      throw e
    }
  }, [])

  const deleteAgent = useCallback(async (id: number) => {
    dispatch({ type: 'SET_ERROR', payload: null })
    try {
      await api.agents.delete(id)
      dispatch({ type: 'REMOVE_AGENT', payload: id })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to delete agent' })
    }
  }, [])

  const selectSession = useCallback(async (session: ChatSessionResponse) => {
    dispatch({ type: 'SET_SELECTED_SESSION', payload: session })
    dispatch({ type: 'SET_LOADING', payload: true })
    dispatch({ type: 'SET_ERROR', payload: null })
    try {
      const messages = await api.messages.list(session.id)
      dispatch({ type: 'SET_MESSAGES', payload: messages })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to load messages' })
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }, [])

  const createSession = useCallback(async () => {
    if (!state.selectedAgent) return
    dispatch({ type: 'SET_ERROR', payload: null })
    try {
      const session = await api.sessions.create({ agent_id: state.selectedAgent.id })
      const sessions = await api.sessions.listForAgent(state.selectedAgent.id)
      dispatch({ type: 'SET_SESSIONS', payload: sessions })
      dispatch({ type: 'SET_SELECTED_SESSION', payload: session })
      dispatch({ type: 'SET_MESSAGES', payload: [] })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to create session' })
    }
  }, [state.selectedAgent])

  const deleteSession = useCallback(async (id: number) => {
    dispatch({ type: 'SET_ERROR', payload: null })
    try {
      await api.sessions.delete(id)
      dispatch({ type: 'REMOVE_SESSION', payload: id })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to delete session' })
    }
  }, [])

  const sendMessage = useCallback(async (content: string) => {
    if (!state.selectedSession) return
    dispatch({ type: 'SET_ERROR', payload: null })
    const currentSession = state.selectedSession
    try {
      const response = await api.messages.send(currentSession.id, { content })
      dispatch({ type: 'APPEND_MESSAGES', payload: [response.user_message, response.assistant_message] })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to send message' })
    }
  }, [state.selectedSession])

  const sendVoiceMessage = useCallback(async (audioBlob: Blob) => {
    if (!state.selectedSession) return
    dispatch({ type: 'SET_ERROR', payload: null })
    const currentSession = state.selectedSession
    try {
      const response = await api.voice.send(currentSession.id, audioBlob)
      if (response.assistant_message.audio_file) {
        pendingPlaybackRef.current = response.assistant_message.id
      }
      dispatch({ type: 'APPEND_VOICE_MESSAGES', payload: response })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to send voice message' })
    }
  }, [state.selectedSession])

  const consumePendingPlayback = useCallback(() => {
    const id = pendingPlaybackRef.current
    pendingPlaybackRef.current = null
    return id
  }, [])

  const toggleSidebar = useCallback(() => {
    dispatch({ type: 'TOGGLE_SIDEBAR' })
  }, [])

  const clearError = useCallback(() => {
    dispatch({ type: 'SET_ERROR', payload: null })
  }, [])

  return (
    <AppContext.Provider value={{
      state,
      loadAgents,
      selectAgent,
      createAgent,
      updateAgent,
      deleteAgent,
      selectSession,
      createSession,
      deleteSession,
      sendMessage,
      sendVoiceMessage,
      toggleSidebar,
      clearError,
      consumePendingPlayback,
    }}>
      {children}
    </AppContext.Provider>
  )
}

export function useApp() {
  const ctx = useContext(AppContext)
  if (!ctx) throw new Error('useApp must be used within AppProvider')
  return ctx
}
