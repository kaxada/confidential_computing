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
  const [form, setForm] = useState({ first_name: '', last_name: '', email: '', password: '', requested_role: 'researcher' })
  const [status, setStatus] = useState('')
  const [localError, setLocalError] = useState(null)
  const [showPassword, setShowPassword] = useState(false)
  
  const roleOptions = useMemo(() => ROLE_OPTIONS.filter(r => r !== 'admin'), [])

  const handleChange = (e) => {
    setForm({ ...form, [e.target.name]: e.target.value })
    if (localError) setLocalError(null)
  }

  const submit = async (e) => {
    e.preventDefault()
    setStatus('')
    setLocalError(null)
    onError(null)
    try {
      if (mode === 'signup') {
        const res = await api.signup({
            email: form.email,
            password: form.password,
            first_name: form.first_name,
            last_name: form.last_name,
            requested_role: form.requested_role
        })
        setStatus('Account created. Pending admin approval.')
        // Do NOT switch to login automatically, let user see the message.
      } else {
        const res = await api.login({ email: form.email, password: form.password })
        onLogin({ 
            email: form.email, 
            first_name: form.first_name, 
            last_name: form.last_name,
        }, res.token, res.role)
      }
    } catch (err) {
      setLocalError(err.message)
    }
  }

  const isLogin = mode === 'login'
  const isSignupSuccess = !isLogin && status === 'Account created. Pending admin approval.'

  return (
    <div className="auth-container">
        <div className="auth-card-modern">
            <div className="auth-header">
                <h2 className="auth-title">{isLogin ? 'Sign In' : 'Create Account'}</h2>
                <p className="auth-subtitle">
                    {isSignupSuccess 
                        ? 'Your request has been submitted.' 
                        : (isLogin ? 'Enter your credentials to continue' : 'Fill in the details to get started')
                    }
                </p>
            </div>

            {!isSignupSuccess ? (
                <form onSubmit={submit} className="auth-form">
                    {localError && (
                        <div className="auth-error-banner">
                            <Icon path="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" />
                            <span>{localError}</span>
                        </div>
                    )}
                    {!isLogin && (
                        <>
                            <div className="input-group">
                                <input 
                                    name="first_name" 
                                    value={form.first_name} 
                                    onChange={handleChange} 
                                    placeholder="First Name" 
                                    className="auth-input" 
                                    required 
                                />
                            </div>
                            <div className="input-group">
                                <input 
                                    name="last_name" 
                                    value={form.last_name} 
                                    onChange={handleChange} 
                                    placeholder="Last Name" 
                                    className="auth-input" 
                                    required 
                                />
                            </div>
                        </>
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
                    
                    {/* Removed Remember Me & Forgot Password */}
                    {isLogin && <div style={{ marginBottom: 12 }}></div>}

                    <button type="submit" className="auth-submit-btn">
                        {isLogin ? 'Sign In' : 'Create Account'}
                    </button>
                </form>
            ) : (
                 <div className="auth-status success-block">
                    <div className="success-icon">
                        <Icon path="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </div>
                    <p>{status}</p>
                 </div>
            )}

            <div className="auth-footer">
                <span>{isLogin ? "Don't have an account?" : (isSignupSuccess ? "Return to" : "Already have an account?")}</span>
                <button className="auth-link-btn" onClick={() => { setMode(isLogin ? 'signup' : 'login'); setStatus(''); setLocalError(null); onError(null); }}>
                    {isLogin ? 'Create one' : 'Sign in'}
                </button>
            </div>
        </div>
    </div>
  )
}
