import { useEffect, useState } from 'react'
import { api } from './api'
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
  const [error, setError] = useState(null)
  const [profile, setProfile] = useState(null)
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false)

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
      loadMessages(activeThreadId, user.token)
    }
  }, [activeThreadId, user?.token, isAdmin])

  useEffect(() => {
    const fetchProfile = async () => {
      if (!user?.token) {
        setProfile(null)
        return
      }
      try {
        const data = await api.me(user.token)
        setProfile(data)
      } catch (err) {
        handleLogout()
      }
    }
    fetchProfile()
  }, [user?.token])

  const handleSend = async (text) => {
    if (!user?.token) return
    try {
      const payload = { question: text, thread_id: activeThreadId }
      const res = await api.chat(payload, user.token)
      const threadId = res.thread_id || activeThreadId
      if (!activeThreadId) {
        setActiveThreadId(threadId)
        await loadThreads(user.token)
      }
      await loadMessages(threadId, user.token)
    } catch (err) {
      setError(err.message)
    }
  }

  const handleNewChat = () => {
    setActiveThreadId(null)
    setMessages([])
  }

  const handleLogin = (creds, token, role) => {
    const userData = { email: creds.email, name: creds.name || creds.email, role, token }
    setUser(userData)
    localStorage.setItem('cc_session', JSON.stringify({ user: userData, timestamp: Date.now() }))
    setThreads([])
    setMessages([])
    setActiveThreadId(null)
    setError(null)
  }

  const handleLogout = () => {
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
              onSend={handleSend}
              disabled={!user}
              user={user}
            />
          </div>
        )}

        {error && <div className="error">{error}</div>}
      </main>
    </div>
  )
}
