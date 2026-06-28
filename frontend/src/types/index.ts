export interface AgentResponse {
  id: number
  name: string
  prompt: string
  created_at: string
  updated_at: string
}

export interface AgentCreate {
  name: string
  prompt?: string
}

export interface AgentUpdate {
  name?: string
  prompt?: string
}

export interface ChatSessionResponse {
  id: number
  agent_id: number
  title: string
  created_at: string
  updated_at: string
}

export interface ChatSessionCreate {
  agent_id: number
}

export interface MessageResponse {
  id: number
  session_id: number
  role: 'user' | 'assistant'
  content: string
  created_at: string
  audio_file?: AudioFileResponse | null
}

export interface MessageCreate {
  content: string
}

export interface SendMessageResponse {
  user_message: MessageResponse
  assistant_message: MessageResponse
}

export interface AudioFileResponse {
  id: number
  message_id: number
  filename: string
  file_path: string
  mime_type: string
  file_size: number
  created_at: string
}

export interface VoiceResponse {
  user_message: MessageResponse
  assistant_message: MessageResponse
  audio_file: AudioFileResponse
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
}

export interface PaginationParams {
  skip?: number
  limit?: number
}

export interface MessagePaginationParams extends PaginationParams {
  order?: 'asc' | 'desc'
}

export interface ErrorResponse {
  detail: string
  code?: string
  errors?: Record<string, string[]>
}
