import api from './index'
import type { ChatSpec, AgentMessage } from '@/types'

export const listChats = (params?: { user_id?: string; channel?: string }) =>
  api.get<ChatSpec[]>('/chats', { params }).then((r) => r.data)

export const createChat = (data: Partial<ChatSpec>) =>
  api.post<ChatSpec>('/chats', data).then((r) => r.data)

export const getChat = (id: string) =>
  api.get<{ messages: AgentMessage[] }>(`/chats/${id}`).then((r) => r.data)

export const updateChat = (id: string, data: ChatSpec) =>
  api.put<ChatSpec>(`/chats/${id}`, data).then((r) => r.data)

export const deleteChat = (id: string) =>
  api.delete<{ deleted: boolean }>(`/chats/${id}`).then((r) => r.data)

export const batchDeleteChats = (ids: string[]) =>
  api.post<{ deleted: boolean }>('/chats/batch-delete', ids).then((r) => r.data)

/** Stream a query to the agent. */
export async function streamQuery(
  input: string,
  sessionId: string,
  userId: string,
  onEvent: (msg: Record<string, unknown>) => void,
  onDone: () => void,
  onError: (e: Error) => void,
  signal?: AbortSignal,
) {
  const body = {
    input: [
      {
        role: 'user',
        type: 'message',
        content: [{ type: 'text', text: input }],
      },
    ],
    session_id: sessionId,
    user_id: userId,
    stream: true,
  }

  try {
    const response = await fetch('/agent/process', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal,
    })

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`)
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()
    let buffer = ''

    const pump = async () => {
      while (true) {
        const { done, value } = await reader.read()
        if (done) {
          onDone()
          return
        }
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() ?? ''
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
      }
    }

    await pump()
  } catch (e: unknown) {
    if (e instanceof Error) {
      onError(e)
    } else {
      onError(new Error(String(e)))
    }
  }
}
