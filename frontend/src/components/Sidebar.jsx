import { useState, useEffect, useRef } from 'react'

function Icon({ children, size = 24, className = "" }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg" className={`icon ${className}`}>
      {children}
    </svg>
  )
}

function ThreadItem({ thread, active, onSelect, onRename, onDelete }) {
  const [isEditing, setIsEditing] = useState(false)
  const [editTitle, setEditTitle] = useState(thread.title || `Conversation ${thread.id}`)
  const [menuOpen, setMenuOpen] = useState(false)
  const menuRef = useRef(null)
  const inputRef = useRef(null)

  useEffect(() => {
    setEditTitle(thread.title || `Conversation ${thread.id}`)
  }, [thread.title, thread.id])

  useEffect(() => {
    function handleClickOutside(event) {
      if (menuRef.current && !menuRef.current.contains(event.target)) {
        setMenuOpen(false)
      }
    }
    if (menuOpen) {
      document.addEventListener("mousedown", handleClickOutside)
    }
    return () => {
      document.removeEventListener("mousedown", handleClickOutside)
    }
  }, [menuOpen])

  useEffect(() => {
    if (isEditing && inputRef.current) {
        inputRef.current.focus()
    }
  }, [isEditing])

  const handleSave = (e) => {
    e.stopPropagation() // Prevent thread selection
    if (editTitle.trim() && editTitle !== thread.title) {
      onRename(thread.id, editTitle.trim())
    }
    setIsEditing(false)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter') {
        handleSave(e)
    } else if (e.key === 'Escape') {
        setIsEditing(false)
        setEditTitle(thread.title || `Conversation ${thread.id}`)
    }
  }

  const toggleMenu = (e) => {
      e.stopPropagation()
      setMenuOpen(!menuOpen)
  }

  return (
    <div className={`thread-item-wrapper ${active ? 'active' : ''}`} style={{position: 'relative'}}>
        {isEditing ? (
            <input
                ref={inputRef}
                className="thread-edit-input"
                value={editTitle}
                onChange={(e) => setEditTitle(e.target.value)}
                onBlur={handleSave}
                onKeyDown={handleKeyDown}
                onClick={(e) => e.stopPropagation()}
            />
        ) : (
            <button
                className={`thread-link ${active ? 'active' : ''}`}
                onClick={() => onSelect(thread.id)}
                title={thread.title || `Conversation ${thread.id}`}
            >
                <span className="thread-title">{thread.title || `Conversation ${thread.id}`}</span>
                <div className="thread-actions">
                     <div className="icon-btn-small" onClick={toggleMenu}>
                        <Icon size={16}>
                            <path d="M6.75 12a.75.75 0 11-1.5 0 .75.75 0 011.5 0zM12.75 12a.75.75 0 11-1.5 0 .75.75 0 011.5 0zM18.75 12a.75.75 0 11-1.5 0 .75.75 0 011.5 0z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                        </Icon>
                     </div>
                </div>
            </button>
        )}
        
        {menuOpen && (
            <div className="thread-menu" ref={menuRef} style={{
                position: 'absolute',
                right: 0,
                top: '100%',
                zIndex: 10,
                background: 'var(--bg)',
                border: '1px solid var(--border)',
                borderRadius: '6px',
                boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
                minWidth: '120px',
                overflow: 'hidden'
            }}>
                <button className="menu-item small" onClick={(e) => { e.stopPropagation(); setIsEditing(true); setMenuOpen(false); }}>
                    <Icon size={14} className="mr-2"><path d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L11.553 15.06a.9.9 0 01-.283.19l-4.903 1.634a.26.26 0 01-.326-.326l1.634-4.903a.9.9 0 01.19-.283L16.863 4.487z" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></Icon>
                    Rename
                </button>
                <button className="menu-item small danger" onClick={(e) => { e.stopPropagation(); onDelete(thread.id); setMenuOpen(false); }}>
                     <Icon size={14} className="mr-2"><path d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/></Icon>
                    Delete
                </button>
            </div>
        )}
    </div>
  )
}

export default function Sidebar({ collapsed, onToggleCollapse, user, profile, showThreads = true, threads, activeThreadId, onSelectThread, onNewChat, onLogout, onDelete, onRenameThread, onDeleteThread }) {
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
                    <ThreadItem 
                        key={t.id}
                        thread={t}
                        active={activeThreadId === t.id}
                        onSelect={onSelectThread}
                        onRename={onRenameThread}
                        onDelete={onDeleteThread}
                    />
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
                  <div className="menu-email">
                    {(user.first_name && user.last_name) ? `${user.first_name} ${user.last_name}` : user.email}
                  </div>
                  {profile?.role && <div className="menu-role">{profile.role}</div>}
               </div>
               <div className="menu-divider"></div>
               <button className="menu-item" onClick={onLogout}>Log out</button>
               <button className="menu-item danger" onClick={onDelete}>Delete account</button>
            </div>
          )}
          <button className={`profile-btn ${menuOpen ? 'active' : ''}`} onClick={handleProfileClick} title="User menu">
            <div className="avatar small">{user.first_name?.[0]?.toUpperCase() || user.email?.[0]?.toUpperCase() || 'U'}</div>
            {!collapsed && <div className="user-info">
                <div className="user-name">
                    {(user.first_name && user.last_name) ? `${user.first_name} ${user.last_name}` : user.email}
                </div>
            </div>}
          </button>
        </div>
      )}
    </aside>
  )
}