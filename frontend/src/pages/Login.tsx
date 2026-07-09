import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, setToken } from '../api'

export default function Login() {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [phone, setPhone] = useState('')
  const [password, setPassword] = useState('')
  const [err, setErr] = useState('')
  const nav = useNavigate()

  async function submit() {
    setErr('')
    try {
      const res =
        mode === 'login'
          ? await api.login(phone, password)
          : await api.register(phone, password)
      setToken(res.access_token)
      localStorage.setItem('bc_role', res.role)
      nav('/')
    } catch (e: any) {
      setErr(e.message)
    }
  }

  return (
    <div className="auth-wrap">
      <div className="auth-card">
        <h1>茉莉派 · AI品牌咨询</h1>
        <p className="subtitle">专业可信，温暖引导 —— 让中小企业用得起品牌咨询</p>
        <input placeholder="手机号" value={phone} onChange={(e) => setPhone(e.target.value)} />
        <input
          type="password"
          placeholder="密码（≥6位）"
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          onKeyDown={(e) => e.key === 'Enter' && submit()}
        />
        {err && <div className="error">{err}</div>}
        <button className="btn-primary" onClick={submit}>
          {mode === 'login' ? '登录' : '注册并体验'}
        </button>
        <div className="switch">
          {mode === 'login' ? '还没有账号？' : '已有账号？'}
          <a onClick={() => setMode(mode === 'login' ? 'register' : 'login')}>
            {mode === 'login' ? '免费注册' : '去登录'}
          </a>
        </div>
      </div>
    </div>
  )
}
