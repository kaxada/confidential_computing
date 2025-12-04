const quickLinks = [
  { label: 'New chat', action: 'new', icon: <path d="M12 4.5H6C5.17157 4.5 4.5 5.17157 4.5 6V18C4.5 18.8284 5.17157 19.5 6 19.5H18C18.8284 19.5 19.5 18.8284 19.5 18V12" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /><path d="M13.5 4.5L19.5 10.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /><path d="M20.25 3.75L14.25 9.75" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /> },
  { label: 'Search chats', action: 'search', icon: <path d="M21 21L16.65 16.65M19 11C19 15.4183 15.4183 19 11 19C6.58172 19 3 15.4183 3 11C3 6.58172 6.58172 3 11 3C15.4183 3 19 6.58172 19 11Z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /> },
  { label: 'Library', action: 'library', icon: <path d="M4 19.5V4.5H20V19.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /><path d="M8 4.5V1.5H16V4.5" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" /> },
]

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
            {/* Other links can be added similarly if functionality existed, currently mainly New Chat is active */}
             <button className="nav-link" title="Search chats">
                <Icon>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" stroke="currentColor" strokeWidth="1.5" />
                </Icon>
                {!collapsed && <span>Search chats</span>}
             </button>
             <button className="nav-link" title="Library">
                <Icon>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M2.25 12.75V12A2.25 2.25 0 014.5 9.75h15A2.25 2.25 0 0121.75 12v.75m-8.69-6.44l-2.12-2.12a1.5 1.5 0 00-1.061-.44H4.5A2.25 2.25 0 002.25 6v12a2.25 2.25 0 002.25 2.25h15A2.25 2.25 0 0021.75 18V9a2.25 2.25 0 00-2.25-2.25h-5.379a1.5 1.5 0 01-1.06-.44z" stroke="currentColor" strokeWidth="1.5" />
                </Icon>
                {!collapsed && <span>Library</span>}
             </button>
          </div>
          
          {!collapsed && <div className="section-label">Your chats</div>}
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