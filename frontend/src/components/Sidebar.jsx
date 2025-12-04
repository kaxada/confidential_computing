import { useState, useEffect, useRef } from 'react'

function Icon({ children }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className="icon">
      {children}
    </svg>
  )
}

export default function Sidebar({ collapsed, onToggleCollapse, user, profile, showThreads = true, threads, activeThreadId, onSelectThread, onNewChat, onLogout, onDelete }) {
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false)
      }
    }
    document.addEventListener("mousedown", handleClickOutside)
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [menuRef])

  const handleProfileClick = () => {
    if (collapsed) {
        onToggleCollapse()
    } else {
        setMenuOpen(!menuOpen)
    }
  }

  return (
    <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
      <div className="sidebar-header">
        {!collapsed && <div className="logo-text">Confidential Computing</div>}
        <button className="icon-btn" onClick={onToggleCollapse} aria-label="Toggle sidebar">
          <Icon>
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="1.5" d="M9 4.5v15m6-15v15m-10.5-15h15a2.25 2.25 0 012.25 2.25v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25v-10.5a2.25 2.25 0 012.25-2.25z" stroke="currentColor" />
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
          
          {!collapsed && <div className="section-label">Your chats</div>}
          {!collapsed && (
            <div className="thread-list">
                {threads.map((t) => (
                <button
                    key={t.id}
                    className={`thread-link ${activeThreadId === t.id ? 'active' : ''}`}
                    onClick={() => onSelectThread(t.id)}
                    title={t.title || `Conversation ${t.id}`}
                >
                    <span className="thread-title">{t.title || `Conversation ${t.id}`}</span>
                </button>
                ))}
                {!threads.length && <div className="muted small" style={{paddingLeft: 10}}>No conversations.</div>}
            </div>
          )}
        </>
      ) : (
        <div className="muted">{!collapsed && 'Admin panel'}</div>
      )}
      {user && (
        <div className="sidebar-footer" ref={menuRef}>
          {menuOpen && !collapsed && (
            <div className="user-menu">
               <div className="menu-item info">
                  <div className="menu-email">{user.email}</div>
                  {profile?.role && <div className="menu-role">{profile.role}</div>}
               </div>
               <div className="menu-divider"></div>
               <button className="menu-item" onClick={onLogout}>Log out</button>
               <button className="menu-item danger" onClick={onDelete}>Delete account</button>
            </div>
          )}
          <button className={`profile-btn ${menuOpen ? 'active' : ''}`} onClick={handleProfileClick} title="User menu">
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