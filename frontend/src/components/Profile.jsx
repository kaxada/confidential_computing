import { useState } from 'react'

export default function Profile({ user, profile, onLogout, onDelete }) {
  const [open, setOpen] = useState(false)

  const initials = (user.name || user.email || '?')
    .split(' ')
    .map((p) => p[0])
    .join('')
    .slice(0, 2)
    .toUpperCase()

  return (
    <div className="profile">
      <button className="profile-trigger" onClick={() => setOpen(!open)}>
        <div className="avatar">{initials}</div>
        <div className="profile-meta">
          <div className="profile-name">{user.name || user.email}</div>
          <div className="profile-role">{user.role || 'member'}</div>
        </div>
      </button>
      {open && (
        <div className="profile-card">
          <div className="profile-row">
            <span className="muted">Email</span>
            <span>{user.email}</span>
          </div>
          {profile?.role && (
            <div className="profile-row">
              <span className="muted">Role</span>
              <span>{profile.role}</span>
            </div>
          )}
          {profile?.created_at && (
            <div className="profile-row">
              <span className="muted">Joined</span>
              <span>{new Date(profile.created_at).toLocaleDateString()}</span>
            </div>
          )}
          <div className="profile-actions">
            <button className="ghost" onClick={onLogout}>Log out</button>
            <button className="ghost danger" onClick={onDelete}>Delete account</button>
          </div>
        </div>
      )}
    </div>
  )
}
