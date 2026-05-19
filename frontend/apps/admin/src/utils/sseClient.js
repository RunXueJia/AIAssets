import { getToken } from './apiClient.js'

export async function streamOpenAiSse(path, payload, handlers = {}, options = {}) {
  const baseURL = options.baseURL || import.meta.env.VITE_API_BASE_URL || '/api/v1'
  const controller = options.controller || new AbortController()
  const startedAt = performance.now()
  let firstTokenAt = 0
  let completed = false
  let rawBuffer = ''
  let text = ''
  let chunkCount = 0

  const response = await fetch(`${baseURL}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(getToken() ? { Authorization: `Bearer ${getToken()}` } : {})
    },
    body: JSON.stringify(payload || {}),
    signal: controller.signal
  })

  if (!response.ok || !response.body) {
    throw new Error(`SSE request failed: ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let pending = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) {
      break
    }

    pending += decoder.decode(value, { stream: true })
    const events = pending.split(/\r?\n\r?\n/)
    pending = events.pop() || ''

    for (const event of events) {
      const dataLines = event
        .split(/\r?\n/)
        .filter((line) => line.startsWith('data:'))
        .map((line) => line.slice(5).trim())

      for (const data of dataLines) {
        rawBuffer += `${data}\n`

        if (data === '[DONE]') {
          completed = true
          handlers.onDone?.({ text, raw: rawBuffer, chunkCount, durationMs: performance.now() - startedAt })
          continue
        }

        const chunk = JSON.parse(data)
        chunkCount += 1
        handlers.onChunk?.(chunk)

        const delta = chunk.choices?.[0]?.delta?.content || ''
        if (delta) {
          if (!firstTokenAt) {
            firstTokenAt = performance.now()
            handlers.onFirstToken?.({ firstTokenMs: firstTokenAt - startedAt })
          }
          text += delta
          handlers.onDelta?.(delta, { text, chunk, chunkCount })
        }
      }
    }
  }

  if (!completed) {
    handlers.onInterrupted?.({ text, raw: rawBuffer, chunkCount })
  }

  return { text, raw: rawBuffer, chunkCount, completed }
}
