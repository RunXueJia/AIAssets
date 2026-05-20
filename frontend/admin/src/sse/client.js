const BASE = import.meta.env.VITE_API_BASE || '/api/v1'

export function createStreamUrl(taskId) {
  return `${BASE}/generation/stream/${taskId}`
}

export class SSEClient {
  constructor(url, handlers) {
    this.url = url
    this.handlers = handlers
    this.eventSource = null
    this.retryCount = 0
    this.maxRetries = 5
    this.retryDelay = 1000
    this.closed = false
  }

  connect() {
    if (this.closed) return
    const token = localStorage.getItem('token')
    // Use fetch + ReadableStream for better control and auth header support
    this._connectViaFetch(token)
  }

  async _connectViaFetch(token) {
    try {
      const response = await fetch(this.url, {
        headers: {
          Accept: 'text/event-stream',
          Authorization: `Bearer ${token}`,
        },
      })

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}`)
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

      this.retryCount = 0

      while (!this.closed) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop() || ''

        let eventType = ''
        let eventData = ''

        for (const line of lines) {
          if (line.startsWith('event: ')) {
            eventType = line.slice(7).trim()
          } else if (line.startsWith('data: ')) {
            eventData = line.slice(6).trim()
          } else if (line === '' && eventData) {
            this._dispatch(eventType, eventData)
            eventType = ''
            eventData = ''
          }
        }
      }
    } catch (err) {
      if (!this.closed) {
        this._handleError(err)
      }
    }
  }

  _dispatch(eventType, dataStr) {
    try {
      const data = JSON.parse(dataStr)
      if (this.handlers.onEvent) {
        this.handlers.onEvent(eventType, data)
      }
      if (this.handlers[eventType]) {
        this.handlers[eventType](data)
      }
    } catch {
      // ignore parse errors
    }
  }

  _handleError(err) {
    if (this.handlers.onError) {
      this.handlers.onError(err)
    }
    if (this.retryCount < this.maxRetries) {
      this.retryCount++
      const delay = this.retryDelay * Math.pow(2, this.retryCount - 1)
      setTimeout(() => this.connect(), delay)
    }
  }

  close() {
    this.closed = true
    if (this.eventSource) {
      this.eventSource.close()
      this.eventSource = null
    }
  }
}
