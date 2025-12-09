import { useState, useEffect } from 'react'

export default function Profile({ user, profile, onLogout, onDelete }) {
  const [open, setOpen] = useState(false)
  const [timeLeft, setTimeLeft] = useState('')

  // base_role is the permanent identity. role is the effective capabilities.
  const displayRole = user.base_role || user.role || 'member'
  const privacyLabel = profile?.privacy_label || profile?.privacy_level
  
  // In the decoupled model, role doesn't change. We detect temporary status by the presence of an expiry date.
  const expiresAt = user.role_expires_at ? new Date(user.role_expires_at) : null
  const isExpired = expiresAt && expiresAt < new Date()
  const isTemporary = !!user.role_expires_at && !isExpired

  useEffect(() => {
    if (!expiresAt || isExpired) {
        setTimeLeft(isExpired ? 'Expired' : '')
        return
    }

    const updateTimer = () => {
        const now = new Date()
        const diff = expiresAt - now
        if (diff <= 0) {
            setTimeLeft('Expired')
        } else {
            const minutes = Math.floor(diff / 60000)
            const seconds = Math.floor((diff % 60000) / 1000)
            if (minutes > 0) {
                setTimeLeft(`${minutes}m ${seconds}s`)
            } else {
                setTimeLeft(`${seconds}s`)
            }
        }
    }

    updateTimer()
    const interval = setInterval(updateTimer, 1000)
    return () => clearInterval(interval)
  }, [user.role_expires_at])

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
            <span className="role-label">{displayRole}</span>
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
          
          <div className="profile-row">
              <span className="muted">Role</span>
              <span style={{textTransform: 'capitalize'}}>{displayRole}</span>
          </div>

          {isTemporary && (
             <div className="profile-row" style={{color: 'var(--success-text, green)'}}>
                 <span className="muted">Temp Access</span>
                 <span>
                    Privacy Boost
                    <div style={{fontSize: 11, opacity: 0.8, textAlign: 'right'}}>Ends in: {timeLeft}</div>
                 </span>
             </div>
          )}

          <div className="profile-row">
            <span className="muted">Privacy</span>
            <div className="role-privacy-row compact">
               <span className="privacy-label">{privacyLabel}</span>
            </div>
          </div>

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
