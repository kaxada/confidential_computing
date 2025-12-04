import { useMemo, useState } from 'react'
import { api, ROLE_OPTIONS } from '../api'

export default function AuthView({ onLogin, onError }) {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ name: '', email: '', password: '', requested_role: 'researcher' })
  const [status, setStatus] = useState('')
  const roleOptions = useMemo(() => ROLE_OPTIONS, [])

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
  }

  const submit = async (e) => {
    e.preventDefault()
    setStatus('')
    onError(null)
    try {
      if (mode === 'signup') {
        const res = await api.signup(form)
        setStatus('Account created. Pending admin approval.')
      } else {
        const res = await api.login({ email: form.email, password: form.password })
        onLogin({ email: form.email, name: form.name || form.email }, res.token, res.role)
      }
    } catch (err) {
      onError(err.message)
    }
  }

  return (
    <div className="auth-card">
      <div className="auth-tabs">
        <button className={mode === 'login' ? 'active' : ''} onClick={() => setMode('login')}>Log in</button>
        <button className={mode === 'signup' ? 'active' : ''} onClick={() => setMode('signup')}>Sign up</button>
      </div>
      <form onSubmit={submit} className="stack">
        <label className="label">Name</label>
        <input name="name" value={form.name} onChange={handleChange} placeholder="Your name" required />
        <label className="label">Email</label>
        <input name="email" type="email" value={form.email} onChange={handleChange} required />
        <label className="label">Password</label>
        <input name="password" type="password" value={form.password} onChange={handleChange} required />
        {mode === 'signup' && (
          <>
            <label className="label">Requested Role</label>
            <select name="requested_role" value={form.requested_role} onChange={handleChange}>
              {roleOptions.map((r) => (
                <option key={r} value={r}>{r}</option>
              ))}
            </select>
            <div className="muted">Admin is reserved; others require approval.</div>
          </>
        )}
        <button type="submit" className="primary">{mode === 'signup' ? 'Create account' : 'Log in'}</button>
        {status && <div className="muted">{status}</div>}
      </form>
    </div>
  )
}
