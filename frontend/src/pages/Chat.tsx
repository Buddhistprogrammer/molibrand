import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import Nav from '../components/Nav'
import { api, streamChat } from '../api'

interface Msg {
  role: string
  content: string
}

export default function Chat() {
  const [cid, setCid] = useState<number | null>(null)
  const [messages, setMessages] = useState<Msg[]>([])
  const [input, setInput] = useState('')
  const [streaming, setStreaming] = useState(false)
  const bottomRef = useRef<HTMLDivElement>(null)
  const nav = useNavigate()

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  async function send() {
    if (!input.trim() || streaming) return
    const text = input.trim()
    setInput('')
    setMessages((m) => [...m, { role: 'user', content: text }])

    const { consultation_id } = await api.postMessage(cid, text)
    setCid(consultation_id)

    setStreaming(true)
    setMessages((m) => [...m, { role: 'assistant', content: '' }])
    await streamChat(
      consultation_id,
      (delta) =>
        setMessages((m) => {
          const copy = [...m]
          copy[copy.length - 1] = {
            role: 'assistant',
            content: copy[copy.length - 1].content + delta,
          }
          return copy
        }),
      () => setStreaming(false),
    )
  }

  async function makeReport() {
    if (!cid) return
    await api.generateReport(cid)
    nav('/reports')
  }

  return (
    <div className="app">
      <Nav />
      <main className="chat">
        <div className="messages">
          {messages.length === 0 && (
            <div className="empty">
              <h2>你好，我是茉莉总的 AI 分身 👋</h2>
              <p>请描述你的品牌现状，我会像品牌军师一样为你做诊断。</p>
              <p className="hint">例：我做健康零食，年营收2000万，但品牌定位模糊，不知怎么和竞品差异化。</p>
            </div>
          )}
          {messages.map((m, i) => (
            <div key={i} className={`msg ${m.role}`}>
              <div className="bubble">{m.content || (streaming && i === messages.length - 1 ? '思考中…' : '')}</div>
            </div>
          ))}
          <div ref={bottomRef} />
        </div>
        <div className="composer">
          <textarea
            value={input}
            placeholder="描述你的品牌，或回答 AI 的追问…"
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault()
                send()
              }
            }}
          />
          <div className="composer-actions">
            {cid && messages.length >= 2 && (
              <button className="btn-ghost" onClick={makeReport} disabled={streaming}>
                生成诊断报告
              </button>
            )}
            <button className="btn-primary" onClick={send} disabled={streaming}>
              发送
            </button>
          </div>
        </div>
      </main>
    </div>
  )
}
