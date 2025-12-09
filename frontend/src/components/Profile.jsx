import { useState } from 'react'

export default function Profile({ user, profile, onLogout, onDelete }) {
  const [open, setOpen] = useState(false)

  const roleLabel = profile?.role_label || profile?.role || user.role || 'member'
  const privacyLabel = profile?.privacy_label || profile?.privacy_level

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
          <div className="role-privacy-row">
            <span className="role-label">{roleLabel}</span>
            {privacyLabel && (
              <>
                <span className="dot-separator" aria-hidden="true" />
                <span className="privacy-label">{privacyLabel}</span>
              </>
            )}
          </div>
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
              <span className="muted">Access</span>
              <div className="role-privacy-row compact">
                <span className="role-label">{roleLabel}</span>
                {privacyLabel && (
                  <>
                    <span className="dot-separator" aria-hidden="true" />
                    <span className="privacy-label">{privacyLabel}</span>
                  </>
                )}
              </div>
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
