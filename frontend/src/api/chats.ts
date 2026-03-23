import api from './index'
import type { ChatSpec, AgentMessage, ChatHistory } from '@/types'

declare const BASE_URL: string

const getChatsEndpoint = (agentId?: string) =>
  agentId ? `/agents/${agentId}/chats` : '/chats'

/**
 * List all chats, optionally filtered by user or channel
 */
export const listChats = (
  params?: { user_id?: string; channel?: string },
  agentId?: string,
) => api.get<ChatSpec[]>(getChatsEndpoint(agentId), { params }).then((r) => r.data)

/**
 * Create a new chat session
 */
export const createChat = (data: Partial<ChatSpec>, agentId?: string) =>
  api.post<ChatSpec>(getChatsEndpoint(agentId), data).then((r) => r.data)

/**
 * Get full chat history and status
 */
export const getChat = (id: string, agentId?: string) =>
  api.get<ChatHistory>(`${getChatsEndpoint(agentId)}/${id}`).then((r) => r.data)

/**
 * Update chat metadata
 */
export const updateChat = (id: string, data: ChatSpec, agentId?: string) =>
  api.put<ChatSpec>(`${getChatsEndpoint(agentId)}/${id}`, data).then((r) => r.data)

/**
 * Delete a single chat
 */
export const deleteChat = (id: string, agentId?: string) =>
  api.delete<{ deleted: boolean }>(`${getChatsEndpoint(agentId)}/${id}`).then((r) => r.data)

/**
 * Delete multiple chats at once
 */
export const batchDeleteChats = (ids: string[], agentId?: string) =>
  api.post<{ deleted: boolean }>(`${getChatsEndpoint(agentId)}/batch-delete`, ids).then((r) => r.data)

/** Stop a running chat on the server side. */
export const stopChat = (chatId: string, agentId?: string) => {
  const url = agentId ? `agents/${agentId}/console/chat/stop` : 'console/chat/stop'
  return api.post(url, null, { params: { chat_id: chatId } })
}

/** Stream a query to the agent via /api/console/chat. */
export async function streamQuery(
  input: string,
  sessionId: string,
  userId: string,
  onEvent: (msg: Record<string, unknown>) => void,
  onDone: () => void,
  onError: (e: Error) => void,
  signal?: AbortSignal,
  agentId?: string,
  groupId?: string,
  reconnect?: boolean,
  attachments?: { url: string; name: string; type: string }[],
  regenerate?: boolean,
) {
  const contentParts: Record<string, unknown>[] = [{ type: 'text', text: input }]
  for (const att of attachments ?? []) {
    if (att.type.startsWith('image/')) {
      contentParts.push({ type: 'image', image_url: { url: att.url } })
    } else {
      contentParts.push({ type: 'file', file_url: att.url, filename: att.name })
    }
  }

  const body: Record<string, unknown> = {
    input: [
      {
        role: 'user',
        type: 'message',
        content: contentParts,
      },
    ],
    session_id: sessionId,
    user_id: userId,
    stream: true,
  }
  
  if (reconnect) {
    body.reconnect = true
  }

  if (regenerate) {
    body.regenerate = true
  }

  if (groupId) {
    body.metadata = { group_id: groupId }
  }

  const base = (typeof BASE_URL !== 'undefined' && BASE_URL) || ''
  const apiPrefix = "/api"

  let endpoint: string
  if (groupId) {
    // Group chat → use the multi-agent stream coordinator
    endpoint = '/console/group-chat/stream'
    // Merge group-specific fields into the body
    body.group_chat_id = groupId
    body.text = input
  } else {
    endpoint = agentId ? `/agents/${agentId}/console/chat` : '/console/chat'
  }
  const url = `${base}${apiPrefix}${endpoint}`

  const headers: Record<string, string> = { 'Content-Type': 'application/json' }
  if (typeof TOKEN !== 'undefined' && TOKEN) {
    headers['Authorization'] = `Bearer ${TOKEN}`
  }

  try {
    const response = await fetch(url, {
      method: 'POST',
      headers,
      body: JSON.stringify(body),
      signal,
    })

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}))
      throw new Error(errorData.detail || `HTTP ${response.status}`)
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    const pump = async () => {
      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          if (buffer.trim()) {
            processLines(buffer)
          }
          onDone()
          return
        }
        buffer += decoder.decode(value, { stream: true })
        buffer = processLines(buffer)
      }
    }

    const processLines = (data: string) => {
      const lines = data.split('\n')
      const remaining = lines.pop() ?? ''
      for (const line of lines) {
        if (line.startsWith('data: ')) {
          const raw = line.slice(6).trim()
          if (!raw || raw === '[DONE]') continue
          try {
            const event = JSON.parse(raw) as Record<string, unknown>
            onEvent(event)
          } catch {
            // ignore malformed
          }
        }
      }
      return remaining
    }

    await pump()
  } catch (e: unknown) {
    if (e instanceof Error) {
      if (e.name === 'AbortError') return
      onError(e)
    } else {
      onError(new Error(String(e)))
    }
  }
}
