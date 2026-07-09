import { useEffect, useState } from 'react'
import Nav from '../components/Nav'
import { api } from '../api'

const STATUS_LABEL: Record<string, string> = {
  draft: '草稿',
  pending_review: '审核中',
  approved: '已通过',
  rejected: '已驳回',
  delivered: '已下发',
}

export default function Reports() {
  const [reports, setReports] = useState<any[]>([])

  useEffect(() => {
    api.myReports().then(setReports).catch(() => {})
  }, [])

  return (
    <div className="app">
      <Nav />
      <main className="page">
        <h1>我的诊断报告</h1>
        {reports.length === 0 && <p className="muted">还没有报告，去「品牌诊断」开始对话并生成报告吧。</p>}
        {reports.map((r) => (
          <div key={r.id} className="report-card">
            <div className="report-head">
              <span className={`tag tag-${r.status}`}>{STATUS_LABEL[r.status] || r.status}</span>
              <span className="muted">#{r.id}</span>
            </div>
            {r.status === 'delivered' ? (
              <ReportBody content={r.content} />
            ) : (
              <p className="muted">
                {r.status === 'pending_review'
                  ? '茉莉总正在人工审核，通过后即可查看完整方案。'
                  : r.review_comment || '报告处理中。'}
              </p>
            )}
          </div>
        ))}
      </main>
    </div>
  )
}

function ReportBody({ content }: { content: any }) {
  return (
    <div className="report-body">
      <h3>{content.brand_summary}</h3>
      <Section title="品牌现状评估" text={content.current_assessment} />
      <Section title="品牌定位建议" text={content.positioning_advice} />
      <Section title="差异化建议" text={content.differentiation} />
      {Array.isArray(content.core_problems) && (
        <div><h4>核心问题</h4><ul>{content.core_problems.map((p: string, i: number) => <li key={i}>{p}</li>)}</ul></div>
      )}
      {Array.isArray(content.action_plan) && (
        <div><h4>可落地行动</h4><ol>{content.action_plan.map((p: string, i: number) => <li key={i}>{p}</li>)}</ol></div>
      )}
      {content.health_score && (
        <div className="scores">
          {Object.entries(content.health_score).map(([k, v]) => (
            <div key={k} className="score"><span>{k}</span><b>{v as number}</b></div>
          ))}
        </div>
      )}
    </div>
  )
}

function Section({ title, text }: { title: string; text?: string }) {
  if (!text) return null
  return <div><h4>{title}</h4><p>{text}</p></div>
}
