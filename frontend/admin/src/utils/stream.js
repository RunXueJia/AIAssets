export async function parseSseResponse(response, handlers = {}) {
  if (!response.ok) {
    const errData = await response.json().catch(() => ({}))
    handlers.onError?.({ message: errData.message || `HTTP ${response.status}` })
    return
  }

  if (!response.body) {
    handlers.onError?.({ message: '流式响应为空' })
    return
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  let eventType = ''
  let eventDataLines = []

  function dispatchEvent(type, data) {
    try {
      handlers.onEvent?.(type, JSON.parse(data))
    } catch {
      handlers.onError?.({ message: '流式响应解析失败' })
    }
  }

  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const rawLine of lines) {
      const line = rawLine.replace(/\r$/, '')
      if (line.startsWith('event: ')) {
        eventType = line.slice(7).trim()
      } else if (line.startsWith('data: ')) {
        eventDataLines.push(line.slice(6))
      } else if (line === '' && eventType && eventDataLines.length) {
        dispatchEvent(eventType, eventDataLines.join('\n'))
        eventType = ''
        eventDataLines = []
      }
    }
  }

  if (eventType && eventDataLines.length) {
    dispatchEvent(eventType, eventDataLines.join('\n'))
  }
}
