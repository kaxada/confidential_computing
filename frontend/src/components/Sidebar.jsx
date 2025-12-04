function Icon({ children }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="icon">
      {children}
    </svg>
  )
}

export default function Sidebar({ collapsed, onToggleCollapse, user, profile, showThreads = true, threads, activeThreadId, onSelectThread, onNewChat, onLogout }) {
  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        {!collapsed && <div className="logo-text">Confidential Computing</div>}
        <button className="icon-btn" onClick={onToggleCollapse} aria-label="Toggle sidebar">
          <Icon>
            <rect x="3" y="3" width="18" height="18" rx="2" stroke="currentColor" strokeWidth="1.5" />
            <path d="M9 3V21" stroke="currentColor" strokeWidth="1.5" />
          </Icon>
        </button>
      </div>
      {showThreads ? (
        <>
          <div className="nav-links">
            <button
              className="nav-link"
              onClick={onNewChat}
              title="New chat"
            >
              <Icon>
                 <path d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
              </Icon>
              {!collapsed && <span>New chat</span>}
            </button>
          </div>
          
          {!collapsed && <div className="section-label">Your Queries</div>}
          <div className="thread-list">
            {threads.map((t) => (
              <button
                key={t.id}
                className={`thread-link ${activeThreadId === t.id ? 'active' : ''}`}
                onClick={() => onSelectThread(t.id)}
                title={t.title || `Conversation ${t.id}`}
              >
                {!collapsed ? (
                    <span className="thread-title">{t.title || `Conversation ${t.id}`}</span>
                ) : (
                    <span className="thread-dot"></span>
                )}
              </button>
            ))}
            {!threads.length && !collapsed && <div className="muted small" style={{paddingLeft: 10}}>No conversations.</div>}
          </div>
        </>
      ) : (
        <div className="muted">{!collapsed && 'Admin panel'}</div>
      )}
      {user && (
        <div className="sidebar-footer">
          <button className="profile-btn" onClick={onLogout} title="Log out">
            <div className="avatar small">{user.name?.[0]?.toUpperCase() || 'U'}</div>
            {!collapsed && <div className="user-info">
                <div className="user-name">{user.name || user.email}</div>
            </div>}
          </button>
        </div>
      )}
    </aside>
  )
}