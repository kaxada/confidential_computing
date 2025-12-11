import { useEffect, useState } from 'react'
import { api, ROLE_OPTIONS } from './api'
import AuthView from './components/AuthView'
import ChatView from './components/ChatView'
import Sidebar from './components/Sidebar'
import AdminPanel from './components/AdminPanel'
import Profile from './components/Profile'
import { useMediaQuery } from './hooks/useMediaQuery'

export default function App() {
  const [user, setUser] = useState(null) // { email, role, token }
  const [threads, setThreads] = useState([])
  const [activeThreadId, setActiveThreadId] = useState(() => {
    const stored = localStorage.getItem('cc_ui_state')
    if (stored) {
      try {
        return JSON.parse(stored).activeThreadId || null
      } catch (e) {}
    }
    return null
  })
  const [messages, setMessages] = useState([])
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [isThinking, setIsThinking] = useState(false)
  const [latestResponseId, setLatestResponseId] = useState(null)
  const [error, setError] = useState(null)
  const [profile, setProfile] = useState(null)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)
  
  const [showAccessModal, setShowAccessModal] = useState(false)
  const [requestPrivacyLevel, setRequestPrivacyLevel] = useState('high')
  const [requestReason, setRequestReason] = useState('')
  const [viewMode, setViewMode] = useState(() => {
    const stored = localStorage.getItem('cc_ui_state')
    if (stored) {
      try {
        return JSON.parse(stored).viewMode || 'admin'
      } catch (e) {}
    }
    return 'admin'
  })
  const [adminTab, setAdminTab] = useState(() => {
    const stored = localStorage.getItem('cc_ui_state')
    if (stored) {
      try {
        return JSON.parse(stored).adminTab || 'pending'
      } catch (e) {}
    }
    return 'pending'
  })
  const isMobile = useMediaQuery('(max-width: 960px)')
  const [showMobileSidebar, setShowMobileSidebar] = useState(false)

  const PRIVACY_OPTIONS = [
    { label: 'High Privacy', value: 'high' },
    { label: 'Moderate Privacy ', value: 'moderate' },
    { label: 'Low Privacy', value: 'low' },
    { label: 'No Privacy', value: 'none' },
  ]

  const SESSION_DURATION = 30 * 60 * 1000 // 30 minutes

  const isAdmin = user?.role === 'admin'
  const showChat = !isAdmin || viewMode === 'chat'

  useEffect(() => {
    const stored = localStorage.getItem('cc_session')
    if (stored) {
      try {
        const { user: savedUser, timestamp } = JSON.parse(stored)
        if (Date.now() - timestamp < SESSION_DURATION) {
          setUser(savedUser)
        } else {
          localStorage.removeItem('cc_session')
          localStorage.removeItem('cc_ui_state')
        }
      } catch (e) {
        localStorage.removeItem('cc_session')
        localStorage.removeItem('cc_ui_state')
      }
    }
  }, [])

  // Persist UI state (viewMode, adminTab, activeThreadId) across reloads
  useEffect(() => {
    const uiState = { viewMode, adminTab, activeThreadId }
    localStorage.setItem('cc_ui_state', JSON.stringify(uiState))
  }, [viewMode, adminTab, activeThreadId])

  const loadThreads = async (token) => {
    if (!token || (isAdmin && viewMode !== 'chat')) return
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
    if (user?.token && showChat) {
      loadThreads(user.token)
    }
  }, [user?.token, isAdmin, viewMode])

  useEffect(() => {
    if (activeThreadId && user?.token && showChat) {
      setLatestResponseId(null)
      loadMessages(activeThreadId, user.token)
    }
  }, [activeThreadId, user?.token, isAdmin, viewMode])

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
      if (data.length > 0) {
        setLatestResponseId(data[data.length - 1].id)
      }
      setMessages(data)
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

  const handleSelectThread = (id) => {
    setActiveThreadId(id)
    if (isMobile) setShowMobileSidebar(false)
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
    // Default admin view to dashboard
    if (role === 'admin') setViewMode('admin')
  }

  const handleLogout = async () => {
    try { await api.logout(user?.token) } catch(e) {}
    localStorage.removeItem('cc_session')
    localStorage.removeItem('cc_ui_state')
    setUser(null)
    setThreads([])
    setMessages([])
    setActiveThreadId(null)
    setProfile(null)
    setViewMode('admin')
    setAdminTab('pending')
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

  const handleRequestAccessChange = async () => {
      if (!user?.token) return
      try {
          // Pass null for role, and the selected privacy level
          await api.requestAccess(null, requestPrivacyLevel, requestReason, user.token)
          setShowAccessModal(false)
      setRequestReason('')
      alert("Privacy access request submitted.")
    } catch (e) {
      setError(e.message)
    }
  }

  return (
    <div className={`app ${isSidebarCollapsed ? 'collapsed' : ''} ${isMobile ? 'mobile' : ''} ${showMobileSidebar ? 'sidebar-open' : ''}`}>
      <Sidebar
        collapsed={isSidebarCollapsed}
        onToggleCollapse={() => setIsSidebarCollapsed(!isSidebarCollapsed)}
        isMobile={isMobile}
        mobileOpen={showMobileSidebar}
        onCloseMobile={() => setShowMobileSidebar(false)}
        user={user}
        profile={profile}
        showThreads={showChat}
        threads={threads}
        activeThreadId={activeThreadId}
        onSelectThread={handleSelectThread}
        onNewChat={handleNewChat}
        onLogout={handleLogout}
        onDelete={handleDeleteAccount}
        onRenameThread={handleRenameThread}
        onDeleteThread={handleDeleteThread}
        onRequestAccess={() => setShowAccessModal(true)}
        onRefreshProfile={fetchProfile}
        viewMode={viewMode}
        onToggleViewMode={() => setViewMode(viewMode === 'admin' ? 'chat' : 'admin')}
        adminTab={adminTab}
        onAdminTabChange={setAdminTab}
      />
      {isMobile && (
        <div className={`sidebar-overlay ${showMobileSidebar ? 'show' : ''}`} onClick={() => setShowMobileSidebar(false)} />
      )}
      <main className="main">
        {isMobile && (
          <div className="mobile-topbar">
            <button className="icon-btn ghost" onClick={() => setShowMobileSidebar(true)} aria-label="Open menu">
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M4 6h16M4 12h16M4 18h16" strokeLinecap="round" />
              </svg>
            </button>
            <div className="mobile-topbar-meta">
              <div className="mobile-brand">Confidential Hub</div>
              {user && <div className="mobile-user">{user.name || user.email}</div>}
            </div>
            {showChat && user && (
              <button className="icon-btn ghost" onClick={handleNewChat} aria-label="New chat">
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5">
                  <path d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" strokeLinecap="round" strokeLinejoin="round" />
                </svg>
              </button>
            )}
          </div>
        )}
        {!user && (
          <AuthView onLogin={handleLogin} onError={setError} />
        )}

        {user && isAdmin && viewMode === 'admin' && <AdminPanel user={user} onError={setError} activeTab={adminTab} />}

        {user && showChat && (
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

        {showAccessModal && (
            <div className="auth-container" style={{zIndex: 200, background: 'rgba(0,0,0,0.5)'}}>
                <div className="auth-card-modern" style={{maxWidth: 400}}>
                    <h3 className="auth-title" style={{fontSize: 20}}>Request Privacy Level Change</h3>
                    <div className="input-group">
                        <label style={{fontSize: 14, fontWeight: 500, marginBottom: 4, display: 'block', textAlign: 'left'}}>Desired Privacy Level</label>
                        <select value={requestPrivacyLevel} onChange={e => setRequestPrivacyLevel(e.target.value)} className="auth-input">
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
                        <button className="btn-reject" onClick={() => setShowAccessModal(false)}>Cancel</button>
                        <button className="btn-approve" onClick={handleRequestAccessChange}>Submit</button>
                    </div>
                </div>
            </div>
        )}

        {error && (
            <div className="error" onClick={() => setError(null)} style={{cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '8px'}}>
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z" strokeLinecap="round" strokeLinejoin="round"/></svg>
                {error}
            </div>
        )}
      </main>
    </div>
  )
}
