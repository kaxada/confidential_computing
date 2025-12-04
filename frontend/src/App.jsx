import { useEffect, useMemo, useState } from 'react'
import { api, API_BASE } from './api'
import AuthView from './components/AuthView'
import ChatView from './components/ChatView'
import Sidebar from './components/Sidebar'
import AdminPanel from './components/AdminPanel'

export default function App() {
  const [user, setUser] = useState(null) // { email, role, token }
  const [threads, setThreads] = useState([])
  const [activeThreadId, setActiveThreadId] = useState(null)
  const [messages, setMessages] = useState([])
  const [loadingMessages, setLoadingMessages] = useState(false)
  const [error, setError] = useState(null)

  const isAdmin = user?.role === 'admin'

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
    setUser({ email: creds.email, name: creds.name || creds.email, role, token })
    setThreads([])
    setMessages([])
    setActiveThreadId(null)
    setError(null)
  }

  const handleLogout = () => {
    setUser(null)
    setThreads([])
    setMessages([])
    setActiveThreadId(null)
  }

  return (
    <div className="app">
      <Sidebar
        user={user}
        showThreads={!isAdmin && !!user}
        threads={threads}
        activeThreadId={activeThreadId}
        onSelectThread={setActiveThreadId}
        onNewChat={handleNewChat}
        onLogout={handleLogout}
      />
      <main className="main">
        <header className="topbar">
          <div>
            <div className="eyebrow">Connected to {API_BASE}</div>
            <div className="title">Confidential Computing</div>
            <div className="subtitle">Hub + Enclave backed (stubbed site)</div>
          </div>
          {user && <div className="pill">{user.email} · {user.role}</div>}
        </header>

        {!user && (
          <AuthView onLogin={handleLogin} onError={setError} />
        )}

        {user && isAdmin && <AdminPanel user={user} onError={setError} />}

        {user && !isAdmin && (
          <div className="content-grid">
            <ChatView
              messages={messages}
              loading={loadingMessages}
              onSend={handleSend}
              disabled={!user}
            />
          </div>
        )}

        {error && <div className="error">{error}</div>}
      </main>
    </div>
  )
}
