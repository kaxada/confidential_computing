function NavLink({ label, active, onClick }) {
  return (
    <button className={`nav-link ${active ? 'active' : ''}`} onClick={onClick} type="button">
      {label}
    </button>
  )
}

export default function Sidebar({
  user,
  profile,
  showThreads = true,
  threads,
  activeThreadId,
  onSelectThread,
  onNewChat,
  onLogout,
}) {
  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="logo">CC</div>
      </div>

      {showThreads ? (
        <>
          <div className="nav-links">
            <NavLink label="New chat" active onClick={onNewChat} />
            <NavLink label="Search chats" onClick={() => {}} />
            <NavLink label="Library" onClick={() => {}} />
          </div>

          <div className="section-label">Your chats</div>
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
            {!threads.length && <div className="muted small">No conversations yet.</div>}
          </div>
        </>
      ) : (
        <div className="muted">Admin panel</div>
      )}

      {user && (
        <div className="sidebar-footer">
          <div>
            <div className="muted">{user.name || user.email}</div>
            {profile?.role && <div className="muted small">{profile.role}</div>}
          </div>
          <button className="ghost" type="button" onClick={onLogout}>Log out</button>
        </div>
      )}
    </aside>
  )
}
