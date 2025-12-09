import { useEffect, useState } from 'react'
import { api, ROLE_OPTIONS } from './api'
import AuthView from './components/AuthView'
import ChatView from './components/ChatView'
import Sidebar from './components/Sidebar'
import AdminPanel from './components/AdminPanel'
import Profile from './components/Profile'

export default function App() {
  const [user, setUser] = useState(null) // { email, role, token }
  const [threads, setThreads] = useState([])
  const [activeThreadId, setActiveThreadId] = useState(null)
  const [messages, setMessages] = useState([])
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [latestResponseId, setLatestResponseId] = useState(null)
  const [error, setError] = useState(null)
  const [profile, setProfile] = useState(null)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  
  const [showRoleModal, setShowRoleModal] = useState(false)
  const [requestRole, setRequestRole] = useState('student')
  const [requestReason, setRequestReason] = useState('')

  const PRIVACY_OPTIONS = [
    { label: 'Student (High Privacy)', value: 'student' },
    { label: 'Intern (High Privacy)', value: 'intern' },
    { label: 'Auditor (Moderate Privacy)', value: 'auditor' },
    { label: 'Analyst (Moderate Privacy)', value: 'analyst' },
    { label: 'Researcher (Low Privacy)', value: 'researcher' },
    { label: 'Clinician (Low Privacy)', value: 'clinician' },
    { label: 'PI (No Privacy)', value: 'pi' },
  ]

  const SESSION_DURATION = 60 * 1000 // 1 minute

  const isAdmin = user?.role === 'admin'

  useEffect(() => {
    const stored = localStorage.getItem('cc_session')
    if (stored) {
      try {
        const { user: savedUser, timestamp } = JSON.parse(stored)
        if (Date.now() - timestamp < SESSION_DURATION) {
          setUser(savedUser)
        } else {
          localStorage.removeItem('cc_session')
        }
      } catch (e) {
        localStorage.removeItem('cc_session')
      }
    }
  }, [])

  const loadThreads = async (token) => {
    if (!token || isAdmin) return
    try {
      const data = await api.threads(token)
      setThreads(data)
      if (data.length && !activeThreadId) {
        setActiveThreadId(data[0].id)
      }
    } catch (err) {
      setError(err.message)
    }
  }

  const loadMessages = async (threadId, token) => {
    if (!threadId || !token) return
    setLoadingMessages(true)
    try {
      const data = await api.messages(threadId, token)
      setMessages(data)
    } catch (err) {
      setError(err.message)
    } finally {
      setLoadingMessages(false)
    }
  }

  useEffect(() => {
    if (user?.token && !isAdmin) {
      loadThreads(user.token)
    }
  }, [user?.token, isAdmin])

  useEffect(() => {
    if (activeThreadId && user?.token && !isAdmin) {
      setLatestResponseId(null)
      loadMessages(activeThreadId, user.token)
    }
  }, [activeThreadId, user?.token, isAdmin])

  const fetchProfile = async () => {
    if (!user?.token) {
      setProfile(null)
      return
    }
    try {
      const data = await api.me(user.token)
      setProfile(data)
      const newUserName = (data.first_name && data.last_name) ? `${data.first_name} ${data.last_name}` : data.email
      setUser(prevUser => ({
          ...prevUser,
          first_name: data.first_name,
          last_name: data.last_name,
          name: newUserName,
          role: data.role,
          base_role: data.base_role,
          role_expires_at: data.role_expires_at,
      }))
    } catch (err) {
      handleLogout()
    }
  }

  useEffect(() => {
    fetchProfile()
  }, [user?.token])

  const handleSend = async (text) => {
    if (!user?.token) return
    
    // show user message immediately
    const tempId = Date.now()
    setMessages(prev => [...prev, { id: tempId, role: 'user', content: text }])
    setIsThinking(true)

    try {
      const payload = { question: text, thread_id: activeThreadId }
      const res = await api.chat(payload, user.token)
      const threadId = res.thread_id || activeThreadId
      if (!activeThreadId) {
        setActiveThreadId(threadId)
        await loadThreads(user.token)
      }
      
      const data = await api.messages(threadId, user.token)
      setMessages(data)
      if (data.length > 0) {
        setLatestResponseId(data[data.length - 1].id)
      }
    } catch (err) {
      setError(err.message)
    } finally {
      setIsThinking(false)
    }
  }

  const handleNewChat = () => {
    setActiveThreadId(null)
    setMessages([])
    setLatestResponseId(null)
  }

  const handleLogin = (creds, token, role) => {
    const userData = { 
      email: creds.email, 
      first_name: creds.first_name,
      last_name: creds.last_name,
      name: (creds.first_name && creds.last_name) ? `${creds.first_name} ${creds.last_name}` : creds.email, 
      role, 
      token 
    }
    setUser(userData)
    localStorage.setItem('cc_session', JSON.stringify({ user: userData, timestamp: Date.now() }))
    setThreads([])
    setMessages([])
    setActiveThreadId(null)
    setError(null)
  }

  const handleLogout = async () => {
    try { await api.logout(user?.token) } catch(e) {}
    localStorage.removeItem('cc_session')
    setUser(null)
    setThreads([])
    setMessages([])
    setActiveThreadId(null)
    setProfile(null)
  }

  const handleDeleteAccount = async () => {
    try {
      await api.deleteAccount(user.token)
      handleLogout()
    } catch (err) {
      setError(err.message)
    }
  }

  const handleRenameThread = async (threadId, newTitle) => {
    try {
      await api.updateThread(threadId, newTitle, user.token)
      setThreads(threads.map(t => t.id === threadId ? { ...t, title: newTitle } : t))
    } catch (err) {
      setError(err.message)
    }
  }

  const handleDeleteThread = async (threadId) => {
    try {
      await api.deleteThread(threadId, user.token)
      setThreads(threads.filter(t => t.id !== threadId))
      if (activeThreadId === threadId) {
        handleNewChat()
      }
    } catch (err) {
      setError(err.message)
    }
  }

  const handleRequestRoleChange = async () => {
      if (!user?.token) return
      try {
          await api.requestRole(requestRole, requestReason, user.token)
          setShowRoleModal(false)
          setRequestReason('')
          alert("Role request submitted.")
      } catch (e) {
          setError(e.message)
      }
  }

  return (
    <div className={`app ${isSidebarCollapsed ? 'collapsed' : ''}`}>
      <Sidebar
        collapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        user={user}
        profile={profile}
        showThreads={!isAdmin && !!user}
        threads={threads}
        activeThreadId={activeThreadId}
        onSelectThread={setActiveThreadId}
        onNewChat={handleNewChat}
        onLogout={handleLogout}
        onDelete={handleDeleteAccount}
        onRenameThread={handleRenameThread}
        onDeleteThread={handleDeleteThread}
        onRequestRole={() => setShowRoleModal(true)}
        onRefreshProfile={fetchProfile}
      />
      <main className="main">
        {!user && (
          <AuthView onLogin={handleLogin} onError={setError} />
        )}

        {user && isAdmin && <AdminPanel user={user} onError={setError} />}

        {user && !isAdmin && (
          <div className="content-grid single">
            <ChatView
              messages={messages}
              loading={loadingMessages}
              thinking={isThinking}
              latestResponseId={latestResponseId}
              onSend={handleSend}
              disabled={!user}
              user={user}
              threadId={activeThreadId}
            />
          </div>
        )}

        {showRoleModal && (
            <div className="auth-container" style={{zIndex: 200, background: 'rgba(0,0,0,0.5)'}}>
                <div className="auth-card-modern" style={{maxWidth: 400}}>
                    <h3 className="auth-title" style={{fontSize: 20}}>Request Privacy Level Change</h3>
                    <div className="input-group">
                        <label style={{fontSize: 14, fontWeight: 500, marginBottom: 4, display: 'block', textAlign: 'left'}}>Desired Privacy Level</label>
                        <select value={requestRole} onChange={e => setRequestRole(e.target.value)} className="auth-input">
                            {PRIVACY_OPTIONS.map(opt => <option key={opt.value} value={opt.value}>{opt.label}</option>)}
                        </select>
                    </div>
                    <div className="input-group" style={{marginTop: 10}}>
                        <textarea 
                            value={requestReason} 
                            onChange={e => setRequestReason(e.target.value)} 
                            placeholder="Reason for request..."
                            className="auth-input"
                            rows={3}
                        />
                    </div>
                    <div className="auth-actions" style={{marginTop: 20, gap: 10, justifyContent: 'flex-end'}}>
                        <button className="btn-reject" onClick={() => setShowRoleModal(false)}>Cancel</button>
                        <button className="btn-approve" onClick={handleRequestRoleChange}>Submit</button>
                    </div>
                </div>
            </div>
        )}

        {error && <div className="error">{error}</div>}
      </main>
    </div>
  )
}
