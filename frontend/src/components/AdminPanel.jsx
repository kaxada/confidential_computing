import { useEffect, useState, useRef } from 'react'
import { api, ROLE_OPTIONS } from '../api'

export function ExpiryTimer({ expiresAt, label, onExpire }) {
    const [timeLeft, setTimeLeft] = useState('')
    const expiredRef = useRef(false)

    useEffect(() => {
        if (!expiresAt) {
            expiredRef.current = false
            return
        }

        // Reset expired state if expiresAt changes to a future date
        if (new Date(expiresAt) > new Date()) {
             expiredRef.current = false
        }

        const update = () => {
            const now = new Date()
            const expiry = new Date(expiresAt)
            const diff = expiry - now

            if (diff <= 0) {
                setTimeLeft('Expired')
                if (!expiredRef.current) {
                    expiredRef.current = true
                    if (onExpire) onExpire()
                }
                return
            }

            const minutes = Math.floor(diff / 60000)
            const seconds = Math.floor((diff % 60000) / 1000)
            
            if (minutes > 0) {
                setTimeLeft(`${minutes}m ${seconds}s`)
            } else {
                setTimeLeft(`${seconds}s`)
            }
        }

        update()
        const interval = setInterval(update, 1000)
        return () => clearInterval(interval)
    }, [expiresAt, onExpire])

    if (!expiresAt) return 'Permanent'
    if (timeLeft === 'Expired') return null
    return (
        <span className="expiry-timer-wrapper">
            {label && <span className="expiry-label" style={{marginRight: '4px'}}>{label}</span>}
            <span style={{color: 'var(--warning-text, orange)', fontWeight: 500}}>{timeLeft}</span>
        </span>
    )
}

export default function AdminPanel({ user, onError }) {
  const [tab, setTab] = useState('users')
  const [users, setUsers] = useState([])
  const [logs, setLogs] = useState([])
  const [selectedUser, setSelectedUser] = useState(null)
  const [role, setRole] = useState('researcher')
  const [duration, setDuration] = useState('')
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)

  const loadData = async () => {
    if (!user?.token) return
    try {
      setStatus('')
      if (tab === 'users') {
        const data = await api.admin.users(user.token)
        setUsers(data)
      } else {
        const data = await api.admin.logs(user.token)
        setLogs(data)
      }
    } catch (err) {
      onError(err.message)
    }
  }

  useEffect(() => {
    loadData()
  }, [user?.token, tab])

  useEffect(() => {
      if (selectedUser) {
          // Prefer requested_role so the admin sees what the user wants
          const targetRole = selectedUser.requested_role || selectedUser.role || 'researcher'
          setRole(targetRole)
          
          // If approved user has a different requested role, assume temporary request -> default to 60m
          const isPrivacyRequest = selectedUser.approved && selectedUser.requested_role && selectedUser.requested_role !== selectedUser.role
          setDuration(isPrivacyRequest ? '60' : '')
      }
  }, [selectedUser])

  const handleUpdateRole = async () => {
    if (!selectedUser) return
    try {
      setBusy(true)
      let durationMinutes = null
      if (duration) {
          const minutes = parseFloat(duration)
          if (isNaN(minutes) || minutes < 0.25 || minutes > 60) {
              alert("Duration must be between 0.25 and 60 minutes")
              setBusy(false)
              return
          }
          durationMinutes = minutes
      }
      
      await api.admin.updateRole(selectedUser.id, role, durationMinutes, user.token)
      setStatus('User updated.')
      setSelectedUser(null)
      await loadData()
    } catch (err) {
      onError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const handleApproveUser = async (userToApprove) => {
    try {
      setBusy(true)
      await api.admin.approve({ 
        user_id: userToApprove.id, 
        role: userToApprove.requested_role 
      }, user.token)
      setStatus('User approved.')
      await loadData()
    } catch (err) {
      onError(err.message)
    } finally {
      setBusy(false)
    }
  }

  const handleDeleteUser = async (userId) => {
    if (!confirm("Are you sure you want to delete this user and all their data?")) return
    try {
      setBusy(true)
      await api.admin.deleteUser(userId, user.token)
      await loadData()
    } catch (err) {
        onError(err.message)
    } finally {
        setBusy(false)
    }
  }

  return (
    <div className="admin-container">
      <div className="admin-header">
        <h2 className="admin-title">Admin Dashboard</h2>
        <div className="admin-tabs" style={{display: 'flex', gap: 20, borderBottom: '1px solid var(--border)', paddingBottom: 0}}>
            <button 
                className={`tab-btn ${tab === 'users' ? 'active' : ''}`}
                onClick={() => setTab('users')}
                style={{
                    background: 'transparent', border: 'none', padding: '10px 0', 
                    borderBottom: tab === 'users' ? '2px solid var(--text)' : '2px solid transparent',
                    fontWeight: tab === 'users' ? 600 : 400, cursor: 'pointer', color: 'var(--text)'
                }}
            >
                Users
            </button>
            <button 
                className={`tab-btn ${tab === 'logs' ? 'active' : ''}`}
                onClick={() => setTab('logs')}
                style={{
                    background: 'transparent', border: 'none', padding: '10px 0', 
                    borderBottom: tab === 'logs' ? '2px solid var(--text)' : '2px solid transparent',
                    fontWeight: tab === 'logs' ? 600 : 400, cursor: 'pointer', color: 'var(--text)'
                }}
            >
                Audit Logs
            </button>
        </div>
      </div>

      {tab === 'users' && (
          <div className="users-view" style={{overflowY: 'auto', marginTop: 20}}>
              <table style={{width: '100%', borderCollapse: 'collapse', fontSize: 14}}>
                  <thead>
                      <tr style={{borderBottom: '1px solid var(--border)', textAlign: 'left'}}>
                          <th style={{padding: 10}}>User</th>
                          <th style={{padding: 10}}>Role</th>
                          <th style={{padding: 10}}>Status</th>
                          <th style={{padding: 10}}>Expiry</th>
                          <th style={{padding: 10}}>Actions</th>
                      </tr>
                  </thead>
                  <tbody>
                      {users.map(u => (
                          <tr key={u.id} style={{borderBottom: '1px solid var(--border)'}}>
                              <td style={{padding: 10}}>
                                  <div style={{fontWeight: 500}}>{u.email}</div>
                                  {u.request_reason && <div style={{fontSize: 12, color: 'var(--text-secondary)'}}>Reason: {u.request_reason}</div>}
                              </td>
                              <td style={{padding: 10}}>{u.role || '-'}</td>
                              <td style={{padding: 10}}>
                                  {u.approved ? 
                                    <span style={{color: 'green'}}>Active</span> : 
                                    <span style={{color: 'orange'}}>Pending ({u.requested_role})</span>
                                  }
                              </td>
                              <td style={{padding: 10}}>
                                  <ExpiryTimer expiresAt={u.role_expires_at} />
                              </td>
                              <td style={{padding: 10}}>
                                  {!u.approved && (
                                      <button onClick={() => handleApproveUser(u)} style={{marginRight: 8, cursor: 'pointer', background: 'none', border: 'none', color: 'var(--success-text, green)', fontWeight: 600}}>Approve</button>
                                  )}
                                  <button onClick={() => setSelectedUser(u)} style={{marginRight: 8, cursor: 'pointer', background: 'none', border: 'none', color: 'var(--primary-btn)'}}>Edit</button>
                                  <button onClick={() => handleDeleteUser(u.id)} style={{cursor: 'pointer', background: 'none', border: 'none', color: 'var(--error-text)'}}>Delete</button>
                              </td>
                          </tr>
                      ))}
                  </tbody>
              </table>
          </div>
      )}

      {tab === 'logs' && (
          <div className="logs-view" style={{overflowY: 'auto', marginTop: 20}}>
              <table style={{width: '100%', borderCollapse: 'collapse', fontSize: 14}}>
                  <thead>
                      <tr style={{borderBottom: '1px solid var(--border)', textAlign: 'left'}}>
                          <th style={{padding: 10}}>Time</th>
                          <th style={{padding: 10}}>User ID</th>
                          <th style={{padding: 10}}>Event</th>
                          <th style={{padding: 10}}>Details</th>
                      </tr>
                  </thead>
                  <tbody>
                      {logs.map(l => (
                          <tr key={l.id} style={{borderBottom: '1px solid var(--border)'}}>
                              <td style={{padding: 10}}>{new Date(l.created_at).toLocaleString()}</td>
                              <td style={{padding: 10}}>{l.user_id}</td>
                              <td style={{padding: 10}}>{l.event}</td>
                              <td style={{padding: 10, maxWidth: 300, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap'}} title={l.details}>
                                  {l.details}
                              </td>
                          </tr>
                      ))}
                  </tbody>
              </table>
          </div>
      )}

      {selectedUser && (
          <div className="auth-container" style={{zIndex: 200, background: 'rgba(0,0,0,0.5)'}}>
              <div className="auth-card-modern" style={{maxWidth: 500}}>
                  <h3 className="auth-title" style={{fontSize: 20}}>
                      {selectedUser.approved && selectedUser.requested_role !== selectedUser.role 
                        ? 'Review Privacy Request' 
                        : 'Edit User Role'}
                  </h3>
                  <p className="auth-subtitle" style={{marginBottom: 20}}>
                    {selectedUser.email}<br/>
                    <span style={{fontSize: 12, color: 'var(--text-secondary)'}}>
                        Current Base Role: {selectedUser.role || 'None'}
                        {selectedUser.role !== selectedUser.requested_role && (
                            <><br/>Requested Change: {selectedUser.requested_role}</>
                        )}
                    </span>
                    {selectedUser.request_reason && (
                        <div style={{marginTop: 8, padding: 8, background: 'rgba(255,255,255,0.05)', borderRadius: 4, fontSize: 13, fontStyle: 'italic'}}>
                            "{selectedUser.request_reason}"
                        </div>
                    )}
                  </p>
                  
                  <div className="input-group">
                      <label style={{fontSize: 14, fontWeight: 500, marginBottom: 4, display: 'block', textAlign: 'left'}}>Access Profile</label>
                      <select value={role} onChange={e => setRole(e.target.value)} className="auth-input">
                          {ROLE_OPTIONS.map(r => <option key={r} value={r}>{r}</option>)}
                      </select>
                  </div>

                  <div className="input-group" style={{marginTop: 15}}>
                      <label style={{fontSize: 14, fontWeight: 500, marginBottom: 4, display: 'block', textAlign: 'left'}}>Duration (Minutes)</label>
                      <input 
                        type="number" 
                        min="0.25"
                        max="60"
                        step="0.25"
                        className="auth-input" 
                        value={duration} 
                        onChange={e => setDuration(e.target.value)}
                        placeholder="Leave blank for permanent change"
                      />
                      <div style={{fontSize: 12, color: 'var(--text-secondary)', marginTop: 4}}>
                        Set time (0.25-60 min) to grant temporary privacy access without changing role.
                        <br/>Leave blank to permanently change the user's role.
                        {selectedUser.role_expires_at && (
                             <span style={{display: 'block', marginTop: 2, color: 'var(--warning-text, orange)'}}>
                               Current Access Expires in: <ExpiryTimer expiresAt={selectedUser.role_expires_at} />
                             </span>
                        )}
                      </div>
                  </div>

                  <div className="auth-actions" style={{marginTop: 20, gap: 10, justifyContent: 'flex-end'}}>
                      <button className="btn-reject" onClick={() => setSelectedUser(null)}>Cancel</button>
                      <button className="btn-approve" disabled={busy} onClick={handleUpdateRole}>
                          {duration ? 'Grant Temporary Access' : 'Save Permanent Change'}
                      </button>
                  </div>
              </div>
          </div>
      )}
    </div>
  )
}