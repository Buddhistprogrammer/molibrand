import { useEffect, useState } from 'react'
import Nav from '../components/Nav'
import { api } from '../api'

const DOC_TYPES = [
  { v: 'methodology', label: '方法论' },
  { v: 'case', label: '案例复盘' },
  { v: 'template', label: '诊断模板' },
  { v: 'faq', label: 'FAQ' },
]

export default function Knowledge() {
  const [docs, setDocs] = useState<any[]>([])
  const [title, setTitle] = useState('')
  const [docType, setDocType] = useState('methodology')
  const [content, setContent] = useState('')
  const [busy, setBusy] = useState(false)

  const load = () => api.listDocs().then(setDocs).catch(() => {})
  useEffect(() => {
    load()
  }, [])

  async function submit() {
    if (!title.trim() || !content.trim()) return
    setBusy(true)
    try {
      await api.createDoc({ title, doc_type: docType, content })
      setTitle('')
      setContent('')
      load()
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="app">
      <Nav />
      <main className="page">
        <h1>知识库管理</h1>
        <p className="muted">录入茉莉总的品牌经验文档，系统自动分块 + 向量化入库（RAG）。</p>

        <div className="kb-form">
          <input placeholder="文档标题" value={title} onChange={(e) => setTitle(e.target.value)} />
          <select value={docType} onChange={(e) => setDocType(e.target.value)}>
            {DOC_TYPES.map((t) => (
              <option key={t.v} value={t.v}>{t.label}</option>
            ))}
          </select>
          <textarea
            placeholder="文档正文…"
            rows={6}
            value={content}
            onChange={(e) => setContent(e.target.value)}
          />
          <button className="btn-primary" onClick={submit} disabled={busy}>
            {busy ? '向量化中…' : '录入并向量化'}
          </button>
        </div>

        <table className="kb-table">
          <thead>
            <tr><th>ID</th><th>标题</th><th>类型</th><th>状态</th><th>分块数</th></tr>
          </thead>
          <tbody>
            {docs.map((d) => (
              <tr key={d.id}>
                <td>{d.id}</td>
                <td>{d.title}</td>
                <td>{d.doc_type}</td>
                <td>{d.status}</td>
                <td>{d.chunk_count}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </main>
    </div>
  )
}
