import { Link, useLocation, useNavigate } from 'react-router-dom'
import { clearToken } from '../api'

export default function Nav() {
  const loc = useLocation()
  const nav = useNavigate()
  const role = localStorage.getItem('bc_role') || 'user'

  const item = (to: string, label: string) => (
    <Link to={to} className={loc.pathname === to ? 'nav-link active' : 'nav-link'}>
      {label}
    </Link>
  )

  return (
    <header className="nav">
      <div className="brand">茉莉派 · AI品牌咨询</div>
      <nav className="nav-links">
        {item('/', '品牌诊断')}
        {item('/reports', '我的报告')}
        {(role === 'reviewer' || role === 'admin') && item('/review', '审核工作台')}
        {(role === 'reviewer' || role === 'admin') && item('/knowledge', '知识库')}
      </nav>
      <button
        className="btn-ghost"
        onClick={() => {
          clearToken()
          nav('/login')
        }}
      >
        退出
      </button>
    </header>
  )
}
