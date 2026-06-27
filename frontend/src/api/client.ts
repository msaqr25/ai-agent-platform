import type { AgentCreate, AgentResponse, AgentUpdate } from '../types'
import type { ChatSessionCreate, ChatSessionResponse } from '../types'
import type { MessageCreate, MessageResponse, SendMessageResponse } from '../types'
import type { VoiceResponse, ErrorResponse } from '../types'

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
  const headers: Record<string, string> = {}
  // Don't set Content-Type for FormData (browser sets it with boundary),
  // but do set it for JSON bodies.
  if (!(options.body instanceof FormData)) {
    headers['Content-Type'] = 'application/json'
  }
  const res = await fetch(url, {
    headers: { ...headers, ...(options.headers as Record<string, string> | undefined) },
    ...options,
  })

  if (!res.ok) {
    const body = (await res.json().catch(() => ({ detail: res.statusText }))) as ErrorResponse
    throw new ApiError(res.status, body)
  }

  // 204 No Content has no body — return undefined cast to T.
  if (res.status === 204) return undefined as T

  return res.json() as Promise<T>
}

export const api = {
  agents: {
    list: () => request<AgentResponse[]>('/api/v1/agents/'),
    get: (id: number) => request<AgentResponse>(`/api/v1/agents/${id}`),
    create: (data: AgentCreate) =>
      request<AgentResponse>('/api/v1/agents/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    update: (id: number, data: AgentUpdate) =>
      request<AgentResponse>(`/api/v1/agents/${id}`, {
        method: 'PUT',
        body: JSON.stringify(data),
      }),
    delete: (id: number) =>
      request<void>(`/api/v1/agents/${id}`, { method: 'DELETE' }),
  },

  sessions: {
    listForAgent: (agentId: number) =>
      request<ChatSessionResponse[]>(`/api/v1/sessions/agent/${agentId}`),
    get: (id: number) => request<ChatSessionResponse>(`/api/v1/sessions/${id}`),
    create: (data: ChatSessionCreate) =>
      request<ChatSessionResponse>('/api/v1/sessions/', {
        method: 'POST',
        body: JSON.stringify(data),
      }),
    delete: (id: number) =>
      request<void>(`/api/v1/sessions/${id}`, { method: 'DELETE' }),
  },

  messages: {
    list: (sessionId: number) =>
      request<MessageResponse[]>(`/api/v1/sessions/${sessionId}/messages/`),
    send: (sessionId: number, data: MessageCreate) =>
      request<SendMessageResponse>(`/api/v1/sessions/${sessionId}/messages/`, {
        method: 'POST',
        body: JSON.stringify(data),
      }),
  },

  voice: {
    send: (sessionId: number, audioBlob: Blob) => {
      const form = new FormData()
      form.append('audio', audioBlob, `recording.${audioBlob.type === 'audio/webm' ? 'webm' : 'webm'}`)
      return request<VoiceResponse>(`/api/v1/sessions/${sessionId}/voice/`, {
        method: 'POST',
        body: form,
      })
    },
  },
}
