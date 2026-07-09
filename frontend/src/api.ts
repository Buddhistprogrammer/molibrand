// 后端 API 客户端。token 存 localStorage。
const TOKEN_KEY = 'bc_token'

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}
export function setToken(t: string) {
  localStorage.setItem(TOKEN_KEY, t)
}
export function clearToken() {
  localStorage.removeItem(TOKEN_KEY)
}

function authHeaders(): Record<string, string> {
  const t = getToken()
  return t ? { Authorization: `Bearer ${t}` } : {}
}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(path, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      ...authHeaders(),
      ...(opts.headers || {}),
    },
  })
  if (!res.ok) {
    const msg = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(msg.detail || '请求失败')
  }
  return res.json()
}

export interface TokenOut {
  access_token: string
  role: string
  nickname?: string
}

export const api = {
  register: (phone: string, password: string, nickname?: string) =>
    req<TokenOut>('/api/auth/register', {
      method: 'POST',
      body: JSON.stringify({ phone, password, nickname }),
    }),
  login: (phone: string, password: string) =>
    req<TokenOut>('/api/auth/login', {
      method: 'POST',
      body: JSON.stringify({ phone, password }),
    }),
  listConsultations: () => req<any[]>('/api/consultations'),
  listMessages: (cid: number) => req<any[]>(`/api/consultations/${cid}/messages`),
  postMessage: (consultation_id: number | null, message: string, attachments: any[] = []) =>
    req<{ consultation_id: number }>('/api/chat', {
      method: 'POST',
      body: JSON.stringify({ consultation_id, message, attachments }),
    }),
  generateReport: (cid: number) =>
    req<any>(`/api/reports/generate/${cid}`, { method: 'POST' }),
  myReports: () => req<any[]>('/api/reports/mine'),
  pendingReports: () => req<any[]>('/api/reports/pending'),
  reviewReport: (id: number, action: string, comment?: string, content?: any) =>
    req<any>(`/api/reports/${id}/review`, {
      method: 'POST',
      body: JSON.stringify({ action, comment, content }),
    }),
  listDocs: () => req<any[]>('/api/knowledge/documents'),
  createDoc: (doc: any) =>
    req<any>('/api/knowledge/documents', { method: 'POST', body: JSON.stringify(doc) }),
}

/**
 * SSE 流式对话。用 fetch + ReadableStream 以便携带 Authorization 头
 * （原生 EventSource 无法自定义 header）。
 */
export async function streamChat(
  consultationId: number,
  onDelta: (text: string) => void,
  onDone: () => void,
) {
  const res = await fetch(`/api/chat/stream?consultation_id=${consultationId}`, {
    headers: { ...authHeaders() },
  })
  if (!res.body) return onDone()
  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { done, value } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''
    for (const part of parts) {
      const line = part.trim()
      if (!line.startsWith('data:')) continue
      try {
        const data = JSON.parse(line.slice(5).trim())
        if (data.delta) onDelta(data.delta)
        if (data.done) onDone()
      } catch {
        /* 忽略解析失败 */
      }
    }
  }
  onDone()
}
