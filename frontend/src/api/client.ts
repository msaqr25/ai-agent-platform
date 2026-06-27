import type { AgentCreate, AgentResponse, AgentUpdate } from '../types'
import type { ChatSessionCreate, ChatSessionResponse } from '../types'
import type { MessageCreate, MessageResponse, SendMessageResponse } from '../types'
import type { ErrorResponse } from '../types'

class ApiError extends Error {
  status: number
  code?: string
  errors?: Record<string, string[]>

  constructor(status: number, body: ErrorResponse) {
    super(body.detail)
    this.name = 'ApiError'
    this.status = status
    this.code = body.code
    this.errors = body.errors
  }
}

async function request<T>(path: string, options: RequestInit = {}): Promise<T> {
  const url = path
  const res = await fetch(url, {
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  })

  if (!res.ok) {
    const body = (await res.json().catch(() => ({ detail: res.statusText }))) as ErrorResponse
    throw new ApiError(res.status, body)
  }

  return res.json() as Promise<T>
}

export const api = {
  agents: {
    list: () => request<AgentResponse[]>('/agents/'),
    get: (id: number) => request<AgentResponse>(`/agents/${id}`),
    create: (data: AgentCreate) =>
      request<AgentResponse>('/agents/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: number, data: AgentUpdate) =>
      request<AgentResponse>(`/agents/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
  },

  sessions: {
    listForAgent: (agentId: number) =>
      request<ChatSessionResponse[]>(`/sessions/agent/${agentId}`),
    get: (id: number) => request<ChatSessionResponse>(`/sessions/${id}`),
    create: (data: ChatSessionCreate) =>
      request<ChatSessionResponse>('/sessions/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },

  messages: {
    list: (sessionId: number) =>
      request<MessageResponse[]>(`/sessions/${sessionId}/messages/`),
    send: (sessionId: number, data: MessageCreate) =>
      request<SendMessageResponse>(`/sessions/${sessionId}/messages/`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },
}
