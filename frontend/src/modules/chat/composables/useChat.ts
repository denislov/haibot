import { ref } from 'vue'
import { streamQuery } from '@/api/chats'
import type { DisplayMessage, DisplayBlock, ContentItem } from '@/types'

function uuidv4(): string {
  if (typeof crypto !== 'undefined' && crypto.randomUUID) return crypto.randomUUID()
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16)
  })
}

export function useChat() {
  const displayMessages = ref<DisplayMessage[]>([])
  const streaming = ref(false)
  const inputText = ref('')

  let abortController: AbortController | null = null

  // ── Convert history messages → display blocks ──────────────────────────
  function convertHistoryToDisplay(messages: Record<string, unknown>[]): DisplayMessage[] {
    const result: DisplayMessage[] = []
    const callBlockMap = new Map<string, DisplayBlock>()
    let currentAssistantMsg: DisplayMessage | null = null

    function flushAssistant() {
      if (currentAssistantMsg && currentAssistantMsg.blocks.length > 0) {
        result.push(currentAssistantMsg)
      }
      currentAssistantMsg = null
    }

    function ensureAssistantMsg(): DisplayMessage {
      if (!currentAssistantMsg) {
        currentAssistantMsg = { id: uuidv4(), role: 'assistant', blocks: [] }
      }
      return currentAssistantMsg
    }

    for (const m of messages) {
      const role = m.role as string
      const type = m.type as string
      const content = (m.content as ContentItem[]) || []

      if (role === 'user') {
        flushAssistant()
        const text = content
          .filter((c) => c.type === 'text')
          .map((c) => c.text || '')
          .join('')
        result.push({
          id: (m.id as string) || uuidv4(),
          role: 'user',
          blocks: [{ id: uuidv4(), kind: 'text', text }],
        })
      } else if (role === 'assistant') {
        const msg = ensureAssistantMsg()

        if (type === 'reasoning') {
          const text = content.filter((c) => c.type === 'text').map((c) => c.text || '').join('')
          msg.blocks.push({ id: uuidv4(), kind: 'reasoning', text, expanded: false })
        } else if (type === 'message') {
          const text = content.filter((c) => c.type === 'text').map((c) => c.text || '').join('')
          if (text) msg.blocks.push({ id: uuidv4(), kind: 'text', text })
        } else if (
          type === 'plugin_call' || type === 'function_call' ||
          type === 'mcp_call' || type === 'component_call'
        ) {
          const dataItem = content.find((c) => c.type === 'data')
          const data = (dataItem?.data as Record<string, unknown>) || {}
          const callId = data.call_id as string | undefined
          const block: DisplayBlock = {
            id: uuidv4(),
            kind: 'tool_call',
            toolType: type,
            toolName: (data.name as string) || type,
            toolArgs: data.arguments as string | undefined,
            expanded: false,
            loading: false,
          }
          msg.blocks.push(block)
          if (callId) callBlockMap.set(callId, block)
        }
      } else if (type === 'plugin_call_output') {
        ensureAssistantMsg()
        const dataItem = content.find((c) => c.type === 'data')
        const data = (dataItem?.data as Record<string, unknown>) || {}
        const callId = data.call_id as string | undefined
        if (callId) {
          const toolBlock = callBlockMap.get(callId)
          if (toolBlock) {
            toolBlock.toolOutput = (data.output as string) || ''
          }
        }
      }
    }

    flushAssistant()
    return result
  }

  // ── Load history ───────────────────────────────────────────────────────
  function setMessages(messages: DisplayMessage[]) {
    displayMessages.value = messages
  }

  function clearMessages() {
    displayMessages.value = []
  }

  // ── Stop streaming ─────────────────────────────────────────────────────
  function stopStreaming() {
    abortController?.abort()
  }

  // ── Send message ───────────────────────────────────────────────────────
  async function sendMessage(
    text: string,
    sessionId: string,
    userId: string,
    scrollToBottom: () => void,
    onDone?: () => void,
    onError?: (e: Error) => void,
  ) {
    if (!text.trim() || streaming.value) return

    // Add user message
    displayMessages.value.push({
      id: uuidv4(),
      role: 'user',
      blocks: [{ id: uuidv4(), kind: 'text', text }],
    })

    // Add assistant shell
    displayMessages.value.push({ id: uuidv4(), role: 'assistant', blocks: [], streaming: true })
    const assistantMsg = displayMessages.value[displayMessages.value.length - 1]

    streaming.value = true
    scrollToBottom()

    // Event routing maps
    const msgBlockMap = new Map<string, DisplayBlock>()
    const callBlockMap = new Map<string, DisplayBlock>()
    const outputMsgIds = new Set<string>()

    function pushBlock(block: DisplayBlock): DisplayBlock {
      assistantMsg.blocks.push(block)
      return assistantMsg.blocks[assistantMsg.blocks.length - 1]
    }

    function onEvent(event: Record<string, unknown>) {
      const obj = event.object as string
      const evStatus = event.status as string | undefined

      if (obj === 'message') {
        const type = event.type as string
        const msgId = event.id as string

        if (evStatus === 'in_progress') {
          if (type === 'message') {
            const block = pushBlock({ id: uuidv4(), kind: 'text', text: '' })
            msgBlockMap.set(msgId, block)
          } else if (type === 'reasoning') {
            const block = pushBlock({ id: uuidv4(), kind: 'reasoning', text: '', expanded: false })
            msgBlockMap.set(msgId, block)
          } else if (
            type === 'plugin_call' || type === 'function_call' ||
            type === 'mcp_call' || type === 'component_call'
          ) {
            const block = pushBlock({
              id: uuidv4(), kind: 'tool_call', toolType: type,
              toolName: '', toolArgs: undefined, expanded: false, loading: true,
            })
            msgBlockMap.set(msgId, block)
          } else if (
            type === 'plugin_call_output' || type === 'function_call_output' ||
            type === 'mcp_call_output' || type === 'component_call_output'
          ) {
            outputMsgIds.add(msgId)
          }
        }
      } else if (obj === 'content') {
        const type = event.type as string
        const msgId = event.msg_id as string
        const evContentStatus = event.status as string | undefined

        if (type === 'text' && event.delta === true) {
          const block = msgBlockMap.get(msgId)
          if (block && (block.kind === 'text' || block.kind === 'reasoning')) {
            block.text = (block.text || '') + (event.text as string || '')
            scrollToBottom()
          }
        } else if (type === 'data') {
          const data = event.data as Record<string, unknown>
          const callId = data.call_id as string | undefined

          if (outputMsgIds.has(msgId)) {
            if (callId) {
              const toolBlock = callBlockMap.get(callId)
              if (toolBlock) {
                const rawOutput = data.output as string | undefined
                if (rawOutput !== undefined) toolBlock.toolOutput = rawOutput
                if (evContentStatus === 'completed') toolBlock.loading = false
              }
            }
          } else {
            const block = msgBlockMap.get(msgId)
            if (block && block.kind === 'tool_call') {
              if (data.name) block.toolName = data.name as string
              if (data.arguments !== undefined) block.toolArgs = data.arguments as string
              if (callId) callBlockMap.set(callId, block)
            }
          }
        }
      }
    }

    abortController = new AbortController()

    await streamQuery(
      text, sessionId, userId,
      onEvent,
      async () => {
        for (const block of msgBlockMap.values()) {
          if (block.kind === 'tool_call' && block.loading) block.loading = false
        }
        streaming.value = false
        assistantMsg.streaming = false
        abortController = null
        onDone?.()
      },
      (e) => {
        streaming.value = false
        assistantMsg.streaming = false
        abortController = null
        if (e.name !== 'AbortError') {
          let textBlock = [...assistantMsg.blocks].reverse().find((b) => b.kind === 'text')
          if (!textBlock) {
            assistantMsg.blocks.push({ id: uuidv4(), kind: 'text', text: '' })
            textBlock = assistantMsg.blocks[assistantMsg.blocks.length - 1]
          }
          textBlock.text = (textBlock.text || '') + `\n\n**错误**: ${e.message}`
          onError?.(e)
        }
      },
      abortController.signal,
    )
  }

  return {
    displayMessages,
    streaming,
    inputText,
    convertHistoryToDisplay,
    setMessages,
    clearMessages,
    stopStreaming,
    sendMessage,
  }
}
