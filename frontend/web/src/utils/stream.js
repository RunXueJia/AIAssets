/**
 * SSE client for streaming generation.
 * Parses Server-Sent Events and calls handlers for each event type.
 */

export function createStreamClient(url, options = {}) {
  const { onRecordCreated, onStage, onToken, onSnapshot, onDone, onError, onClose } = options

  let reader = null
  let aborted = false

  function abort() {
    aborted = true
    if (reader) {
      reader.cancel()
    }
  }

  async function connect(body) {
    aborted = false
    try {
      const response = await fetch(url, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: options.headers?.Authorization || '',
        },
        body: JSON.stringify(body),
      })

      if (!response.ok) {
        const errData = await response.json().catch(() => ({}))
        onError?.({ message: errData.message || `HTTP ${response.status}` })
        return
      }

      if (!response.body) {
        onError?.({ message: '流式响应为空' })
        return
      }

      reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      let eventType = ''
      let eventDataLines = []

      while (!aborted) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        for (const line of lines) {
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

      // Flush remaining buffer
      if (eventType && eventDataLines.length) {
        dispatchEvent(eventType, eventDataLines.join('\n'))
      }

      onClose?.()
    } catch (err) {
      if (!aborted) {
        onError?.({ message: err.message || '流式连接中断' })
      }
      onClose?.()
    }
  }

  function dispatchEvent(type, data) {
    try {
      const parsed = JSON.parse(data)
      switch (type) {
        case 'record_created':
          onRecordCreated?.(parsed)
          break
        case 'stage':
          onStage?.(parsed)
          break
        case 'token':
          onToken?.(parsed)
          break
        case 'snapshot':
          onSnapshot?.(parsed)
          break
        case 'done':
          onDone?.(parsed)
          break
        case 'error':
          onError?.(parsed)
          break
        default:
          break
      }
    } catch {
      onError?.({ message: '流式响应解析失败' })
    }
  }

  return { connect, abort }
}
