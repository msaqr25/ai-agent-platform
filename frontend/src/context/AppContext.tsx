import { createContext, useContext, useReducer, useCallback, useRef, type ReactNode } from 'react'
import { api } from '../api/client'
import type { AgentResponse, ChatSessionResponse, MessageResponse } from '../types'

const AGENTS_PAGE_SIZE = 50
const MESSAGES_PAGE_SIZE = 50

interface AppState {
  agents: AgentResponse[]
  agentsTotal: number
  selectedAgent: AgentResponse | null
  sessions: ChatSessionResponse[]
  sessionsTotal: number
  selectedSession: ChatSessionResponse | null
  messages: MessageResponse[]
  messagesTotal: number
  sidebarOpen: boolean
  isLoading: boolean
  error: string | null
}

type Action =
  | { type: 'SET_AGENTS'; payload: AgentResponse[]; total?: number }
  | { type: 'APPEND_AGENTS'; payload: AgentResponse[] }
  | { type: 'SET_AGENTS_TOTAL'; payload: number }
  | { type: 'UPDATE_AGENT'; payload: AgentResponse }
  | { type: 'REMOVE_AGENT'; payload: number }
  | { type: 'SET_SELECTED_AGENT'; payload: AgentResponse | null }
  | { type: 'SET_SESSIONS'; payload: ChatSessionResponse[]; total?: number }
  | { type: 'SET_SESSIONS_TOTAL'; payload: number }
  | { type: 'SET_SELECTED_SESSION'; payload: ChatSessionResponse | null }
  | { type: 'REMOVE_SESSION'; payload: number }
  | { type: 'SET_MESSAGES'; payload: MessageResponse[]; total?: number }
  | { type: 'PREPEND_MESSAGES'; payload: MessageResponse[] }
  | { type: 'APPEND_MESSAGES'; payload: [MessageResponse, MessageResponse] }
  | { type: 'APPEND_VOICE_MESSAGES'; payload: { user_message: MessageResponse; assistant_message: MessageResponse } }
  | { type: 'TOGGLE_SIDEBAR' }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }

const initialState: AppState = {
  agents: [],
  agentsTotal: 0,
  selectedAgent: null,
  sessions: [],
  sessionsTotal: 0,
  selectedSession: null,
  messages: [],
  messagesTotal: 0,
  sidebarOpen: true,
  isLoading: false,
  error: null,
}

function reducer(state: AppState, action: Action): AppState {
  switch (action.type) {
    case 'SET_AGENTS':
      return { ...state, agents: action.payload, agentsTotal: action.total ?? state.agentsTotal }
    case 'APPEND_AGENTS':
      return { ...state, agents: [...state.agents, ...action.payload] }
    case 'SET_AGENTS_TOTAL':
      return { ...state, agentsTotal: action.payload }
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
        agentsTotal: Math.max(0, state.agentsTotal - 1),
        selectedAgent: state.selectedAgent?.id === action.payload ? null : state.selectedAgent,
        sessions: state.selectedAgent?.id === action.payload ? [] : state.sessions,
        selectedSession: state.selectedAgent?.id === action.payload ? null : state.selectedSession,
        messages: state.selectedAgent?.id === action.payload ? [] : state.messages,
      }
    case 'SET_SELECTED_AGENT':
      return { ...state, selectedAgent: action.payload }
    case 'SET_SESSIONS':
      return { ...state, sessions: action.payload, sessionsTotal: action.total ?? state.sessionsTotal }
    case 'SET_SESSIONS_TOTAL':
      return { ...state, sessionsTotal: action.payload }
    case 'SET_SELECTED_SESSION':
      return { ...state, selectedSession: action.payload }
    case 'REMOVE_SESSION':
      return {
        ...state,
        sessions: state.sessions.filter((s) => s.id !== action.payload),
        sessionsTotal: Math.max(0, state.sessionsTotal - 1),
        selectedSession: state.selectedSession?.id === action.payload ? null : state.selectedSession,
        messages: state.selectedSession?.id === action.payload ? [] : state.messages,
      }
    case 'SET_MESSAGES':
      return { ...state, messages: action.payload, messagesTotal: action.total ?? state.messagesTotal }
    case 'PREPEND_MESSAGES':
      return { ...state, messages: [...action.payload, ...state.messages] }
    case 'APPEND_MESSAGES':
      return { ...state, messages: [...state.messages, action.payload[0], action.payload[1]], messagesTotal: state.messagesTotal + 2 }
    case 'APPEND_VOICE_MESSAGES':
      return {
        ...state,
        messages: [...state.messages, action.payload.user_message, action.payload.assistant_message],
        messagesTotal: state.messagesTotal + 2,
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
  loadMoreAgents: () => Promise<void>
  selectAgent: (agent: AgentResponse) => Promise<void>
  createAgent: (name: string, prompt: string) => Promise<void>
  updateAgent: (id: number, name: string, prompt: string) => Promise<void>
  deleteAgent: (id: number) => Promise<void>
  selectSession: (session: ChatSessionResponse) => Promise<void>
  loadMoreMessages: () => Promise<void>
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
      const { items, total } = await api.agents.list({ skip: 0, limit: AGENTS_PAGE_SIZE })
      dispatch({ type: 'SET_AGENTS', payload: items, total })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to load agents' })
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }, [])

  const loadMoreAgents = useCallback(async () => {
    dispatch({ type: 'SET_ERROR', payload: null })
    try {
      const { items } = await api.agents.list({ skip: state.agents.length, limit: AGENTS_PAGE_SIZE })
      dispatch({ type: 'APPEND_AGENTS', payload: items })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to load more agents' })
    }
  }, [state.agents.length])

  const selectAgent = useCallback(async (agent: AgentResponse) => {
    if (abortRef.current) abortRef.current.abort()
    abortRef.current = new AbortController()

    dispatch({ type: 'SET_SELECTED_AGENT', payload: agent })
    dispatch({ type: 'SET_SELECTED_SESSION', payload: null })
    dispatch({ type: 'SET_MESSAGES', payload: [] })
    dispatch({ type: 'SET_LOADING', payload: true })
    dispatch({ type: 'SET_ERROR', payload: null })

    try {
      const { items: sessions, total: sessionsTotal } = await api.sessions.listForAgent(agent.id, { limit: 200 })
      dispatch({ type: 'SET_SESSIONS', payload: sessions, total: sessionsTotal })
      if (sessions.length > 0) {
        const firstSession = sessions[0]
        dispatch({ type: 'SET_SELECTED_SESSION', payload: firstSession })
        const { items: messages, total: messagesTotal } = await api.messages.list(firstSession.id, { order: 'desc', limit: MESSAGES_PAGE_SIZE })
        dispatch({ type: 'SET_MESSAGES', payload: messages.slice().reverse(), total: messagesTotal })
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
      const agent = await api.agents.create({ name, prompt: prompt || undefined })
      dispatch({ type: 'SET_AGENTS', payload: [...state.agents, agent], total: state.agentsTotal + 1 })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to create agent' })
      throw e
    }
  }, [state.agents, state.agentsTotal])

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
      const { items: messages, total } = await api.messages.list(session.id, { order: 'desc', limit: MESSAGES_PAGE_SIZE })
      dispatch({ type: 'SET_MESSAGES', payload: messages.slice().reverse(), total })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to load messages' })
    } finally {
      dispatch({ type: 'SET_LOADING', payload: false })
    }
  }, [])

  const loadMoreMessages = useCallback(async () => {
    if (!state.selectedSession) return
    dispatch({ type: 'SET_ERROR', payload: null })
    try {
      const { items: messages } = await api.messages.list(state.selectedSession.id, {
        order: 'desc',
        skip: state.messages.length,
        limit: MESSAGES_PAGE_SIZE,
      })
      dispatch({ type: 'PREPEND_MESSAGES', payload: messages.slice().reverse() })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to load older messages' })
    }
  }, [state.selectedSession, state.messages.length])

  const createSession = useCallback(async () => {
    if (!state.selectedAgent) return
    dispatch({ type: 'SET_ERROR', payload: null })
    try {
      const session = await api.sessions.create({ agent_id: state.selectedAgent.id })
      dispatch({ type: 'SET_SESSIONS', payload: [session, ...state.sessions], total: state.sessionsTotal + 1 })
      dispatch({ type: 'SET_SELECTED_SESSION', payload: session })
      dispatch({ type: 'SET_MESSAGES', payload: [] })
    } catch (e) {
      dispatch({ type: 'SET_ERROR', payload: e instanceof Error ? e.message : 'Failed to create session' })
    }
  }, [state.selectedAgent, state.sessions, state.sessionsTotal])

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
      loadMoreAgents,
      selectAgent,
      createAgent,
      updateAgent,
      deleteAgent,
      selectSession,
      loadMoreMessages,
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
