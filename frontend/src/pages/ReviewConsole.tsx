import { useEffect, useState } from 'react'
import Nav from '../components/Nav'
import { api } from '../api'

export default function ReviewConsole() {
  const [pending, setPending] = useState<any[]>([])
  const [comment, setComment] = useState('')

  const load = () => api.pendingReports().then(setPending).catch(() => {})
  useEffect(() => {
    load()
  }, [])

  async function act(id: number, action: string) {
    await api.reviewReport(id, action, comment)
    setComment('')
    load()
  }

  return (
    <div className="app">
      <Nav />
      <main className="page">
        <h1>人工审核工作台</h1>
        <p className="muted">审核 AI 生成的诊断报告，通过 / 修改后下发给用户。</p>
        {pending.length === 0 && <p className="muted">暂无待审核报告 🎉</p>}
        {pending.map((r) => (
          <div key={r.id} className="report-card">
            <div className="report-head">
              <span className="tag tag-pending_review">待审核 #{r.id}</span>
              <span className="muted">会话 {r.consultation_id}</span>
            </div>
            <pre className="report-json">{JSON.stringify(r.content, null, 2)}</pre>
            <textarea
              placeholder="审核意见（可选）"
              value={comment}
              onChange={(e) => setComment(e.target.value)}
            />
            <div className="composer-actions">
              <button className="btn-ghost" onClick={() => act(r.id, 'reject')}>驳回</button>
              <button className="btn-primary" onClick={() => act(r.id, 'approve')}>通过并下发</button>
            </div>
          </div>
        ))}
      </main>
    </div>
  )
}
