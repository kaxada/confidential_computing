export default function Sidebar({ user, threads, activeThreadId, onSelectThread, onNewChat, onLogout }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo">CC</div>
        <button className="ghost" onClick={onNewChat}>+ New chat</button>
      </div>
      <div className="thread-list">
        {threads.map((t) => (
          <button
            key={t.id}
            className={`thread ${activeThreadId === t.id ? 'active' : ''}`}
            onClick={() => onSelectThread(t.id)}
          >
            {t.title || `Conversation ${t.id}`}
          </button>
        ))}
        {!threads.length && <div className="muted">No conversations yet.</div>}
      </div>
      {user && (
        <div className="sidebar-footer">
          <div className="muted">{user.email}</div>
          <button className="ghost" onClick={onLogout}>Log out</button>
        </div>
      )}
    </aside>
  )
}
