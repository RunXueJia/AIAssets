/**
 * SSE client for streaming generation.
 * Parses Server-Sent Events and calls handlers for each event type.
 */

export function createStreamClient(urlOrConfig, options = {}) {
  const config = typeof urlOrConfig === 'string'
    ? { ...options, url: urlOrConfig }
    : { ...urlOrConfig }

  const {
    url,
    method = 'POST',
    body,
    headers = {},
    onStart,
    onRecordCreated,
    onStage,
    onToken,
    onSnapshot,
    onDone,
    onError,
    onClose,
    onEvent,
    onSequence,
  } = config

  let reader = null
  let aborted = false
  let controller = null
  let localSequence = Number(config.afterSequence || 0)

  function abort() {
    aborted = true
    if (controller) {
      controller.abort()
    }
    if (reader) {
      reader.cancel()
    }
  }

  async function connect(connectBody) {
    aborted = false
    controller = new AbortController()
    const requestBody = connectBody !== undefined ? connectBody : body
    const normalizedMethod = method.toUpperCase()
    try {
      const requestHeaders = { ...headers }
      const requestInit = {
        method: normalizedMethod,
        headers: requestHeaders,
        signal: controller.signal,
      }

      if (normalizedMethod !== 'GET' && requestBody !== undefined) {
        requestHeaders['Content-Type'] = requestHeaders['Content-Type'] || 'application/json'
        requestInit.body = typeof requestBody === 'string' ? requestBody : JSON.stringify(requestBody)
      }

      await readResponse(await fetch(url, requestInit))
    } catch (err) {
      if (!aborted) {
        onError?.({ message: err.message || '流式连接中断' })
      }
      onClose?.()
    }
  }

  async function connectResponse(response) {
    aborted = false
    try {
      await readResponse(response)
    } catch (err) {
      if (!aborted) {
        onError?.({ message: err.message || '流式连接中断' })
      }
      onClose?.()
    }
  }

  async function readResponse(response) {
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

    // Flush remaining buffer
    if (eventType && eventDataLines.length) {
      dispatchEvent(eventType, eventDataLines.join('\n'))
    }

    onClose?.()
  }

  function dispatchEvent(type, data) {
    try {
      const parsed = JSON.parse(data)
      const serverSequence = Number(parsed.sequence_no)
      if (Number.isFinite(serverSequence) && serverSequence > 0) {
        localSequence = serverSequence
      } else {
        localSequence += 1
      }
      onSequence?.(localSequence, parsed, type)
      onEvent?.({ type, data: parsed, sequence: localSequence })
      switch (type) {
        case 'start':
          onStart?.(parsed)
          break
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

  return {
    connect,
    connectResponse,
    abort,
    getSequence() {
      return localSequence
    },
  }
}

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
