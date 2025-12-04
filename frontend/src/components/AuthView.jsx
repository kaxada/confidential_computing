import { useMemo, useState } from 'react'
import { api, ROLE_OPTIONS } from '../api'

function Icon({ path, onClick }) {
    return (
        <svg 
            width="20" 
            height="20" 
            viewBox="0 0 24 24" 
            fill="none" 
            xmlns="http://www.w3.org/2000/svg" 
            onClick={onClick} 
            style={{ cursor: onClick ? 'pointer' : 'default' }}
        >
            <path d={path} stroke="#666" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
        </svg>
    )
}

export default function AuthView({ onLogin, onError }) {
  const [mode, setMode] = useState('login')
  const [form, setForm] = useState({ name: '', email: '', password: '', requested_role: 'researcher' })
  const [status, setStatus] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [rememberMe, setRememberMe] = useState(false)
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
        // Optional: switch to login mode after success or keep them here to read the message
      } else {
        const res = await api.login({ email: form.email, password: form.password })
        onLogin({ email: form.email, name: form.name || form.email }, res.token, res.role)
      }
    } catch (err) {
      onError(err.message)
    }
  }

  const isLogin = mode === 'login'

  return (
    <div className="auth-container">
        <div className="auth-card-modern">
            <div className="auth-header">
                <h2 className="auth-title">{isLogin ? 'Sign In' : 'Create Account'}</h2>
                <p className="auth-subtitle">
                    {isLogin ? 'Enter your credentials to continue' : 'Fill in the details to get started'}
                </p>
            </div>

            <form onSubmit={submit} className="auth-form">
                {!isLogin && (
                    <div className="input-group">
                         <input 
                            name="name" 
                            value={form.name} 
                            onChange={handleChange} 
                            placeholder="Full Name" 
                            className="auth-input" 
                            required 
                        />
                    </div>
                )}

                <div className="input-group">
                    <input 
                        name="email" 
                        type="email" 
                        value={form.email} 
                        onChange={handleChange} 
                        placeholder="Email" 
                        className="auth-input" 
                        required 
                    />
                </div>

                <div className="input-group">
                    <input 
                        name="password" 
                        type={showPassword ? "text" : "password"} 
                        value={form.password} 
                        onChange={handleChange} 
                        placeholder="Password" 
                        className="auth-input" 
                        required 
                    />
                    <div className="input-icon-right">
                        <Icon 
                            path={showPassword ? "M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z M15 12a3 3 0 11-6 0 3 3 0 016 0z" : "M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"} 
                            onClick={() => setShowPassword(!showPassword)}
                        />
                    </div>
                </div>

                {!isLogin && (
                     <div className="input-group">
                        <select name="requested_role" value={form.requested_role} onChange={handleChange} className="auth-input">
                            {roleOptions.map((r) => (
                                <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                            ))}
                        </select>
                     </div>
                )}

                {isLogin && (
                    <div className="auth-actions">
                        <label className="remember-me">
                            <input 
                                type="checkbox" 
                                checked={rememberMe} 
                                onChange={(e) => setRememberMe(e.target.checked)} 
                            />
                            <span>Remember me</span>
                        </label>
                        <button type="button" className="forgot-password" onClick={() => alert('Reset password flow not implemented yet.')}>
                            Forgot password?
                        </button>
                    </div>
                )}

                <button type="submit" className="auth-submit-btn">
                    {isLogin ? 'Sign In' : 'Create Account'}
                </button>
            </form>

            {status && <div className="auth-status success">{status}</div>}

            <div className="auth-footer">
                <span>{isLogin ? "Don't have an account?" : "Already have an account?"}</span>
                <button className="auth-link-btn" onClick={() => { setMode(isLogin ? 'signup' : 'login'); setStatus(''); onError(null); }}>
                    {isLogin ? 'Create one' : 'Sign in'}
                </button>
            </div>
        </div>
    </div>
  )
}