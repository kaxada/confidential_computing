import { useEffect, useState, useRef } from 'react'
import { api, ROLE_OPTIONS } from '../api'

const PRIVACY_OPTIONS = [
  { label: 'High Privacy', value: 'high' },
  { label: 'Moderate Privacy', value: 'moderate' },
  { label: 'Low Privacy', value: 'low' },
  { label: 'No Privacy', value: 'none' },
]

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
  const [tab, setTab] = useState('pending') // Default to pending as requested
  const [users, setUsers] = useState([])
  const [pendingRequests, setPendingRequests] = useState([])
  const [logs, setLogs] = useState([])
  
  // For User Edit Modal
  const [selectedUser, setSelectedUser] = useState(null)
  const [role, setRole] = useState('researcher')
  const [privacyLevel, setPrivacyLevel] = useState('moderate')
  const [isPrivacyMode, setIsPrivacyMode] = useState(false)
  const [duration, setDuration] = useState('')
  
  // For Pending Requests
  const [pendingDurations, setPendingDurations] = useState({}) // map userId -> duration string
  
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)

  const loadData = async () => {
    if (!user?.token) return
    try {
      setStatus('')
      if (tab === 'users') {
        const data = await api.admin.users(user.token)
        setUsers(data)
      } else if (tab === 'pending') {
        const data = await api.admin.pending(user.token)
        setPendingRequests(data)
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

  // Reset modal state when selected user changes
  useEffect(() => {
      if (selectedUser) {
          setIsPrivacyMode(false)
          setRole(selectedUser.role || 'researcher')
          setPrivacyLevel('moderate')
          setDuration('')
      }
  }, [selectedUser])

  // --- Handlers for User Management ---

  const handleUpdateAccess = async () => {
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
      
      const payloadRole = isPrivacyMode ? null : role
      const payloadPrivacy = isPrivacyMode ? privacyLevel : null

      await api.admin.updateAccess(selectedUser.id, payloadRole, payloadPrivacy, durationMinutes, user.token)
      setStatus('User updated.')
      setSelectedUser(null)
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

  // --- Handlers for Pending Requests ---

  const handlePendingDurationChange = (userId, value) => {
      setPendingDurations(prev => ({ ...prev, [userId]: value }))
  }

  const handleApproveRequest = async (request) => {
      try {
          setBusy(true)
          
          let durationMinutes = null
          const userDuration = pendingDurations[request.id]
          if (userDuration) {
               const minutes = parseFloat(userDuration)
               if (isNaN(minutes) || minutes < 0.25 || minutes > 60) {
                   alert("Duration must be between 0.25 and 60 minutes")
                   setBusy(false)
                   return
               }
               durationMinutes = minutes
          }

          // Determine what we are approving
          let payloadRole = null
          let payloadPrivacy = null
          
          if (!request.approved) {
              // New user signup - usually approve requested role
              payloadRole = request.requested_role
          } else if (request.requested_privacy_level) {
              // Privacy change
              payloadPrivacy = request.requested_privacy_level
          } else if (request.requested_role) {
              // Role change
              payloadRole = request.requested_role
          }

          await api.admin.updateAccess(request.id, payloadRole, payloadPrivacy, durationMinutes, user.token)
          setStatus('Request approved.')
          setPendingDurations(prev => {
              const next = {...prev}
              delete next[request.id]
              return next
          })
          await loadData()
      } catch (err) {
          onError(err.message)
      } finally {
          setBusy(false)
      }
  }

  const handleRejectRequest = async (request) => {
      if (!confirm("Reject this request?")) return
      try {
          setBusy(true)
          if (!request.approved) {
              // Rejecting signup -> Delete user
              await api.admin.removePending(request.id, user.token)
          } else {
              // Rejecting change request -> Reset requested fields
              await api.admin.rejectRequest(request.id, user.token)
          }
          setStatus('Request rejected.')
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
                className={`tab-btn ${tab === 'pending' ? 'active' : ''}`}
                onClick={() => setTab('pending')}
                style={{
                    background: 'transparent', border: 'none', padding: '10px 0', 
                    borderBottom: tab === 'pending' ? '2px solid var(--text)' : '2px solid transparent',
                    fontWeight: tab === 'pending' ? 600 : 400, cursor: 'pointer', color: 'var(--text)'
                }}
            >
                Pending Approvals
            </button>
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

      {tab === 'pending' && (
          <div className="users-view" style={{overflowY: 'auto', marginTop: 20}}>
              {pendingRequests.length === 0 ? (
                  <div style={{padding: 20, color: 'var(--text-secondary)'}}>No pending approvals.</div>
              ) : (
                  <table style={{width: '100%', borderCollapse: 'collapse', fontSize: 14}}>
                      <thead>
                          <tr style={{borderBottom: '1px solid var(--border)', textAlign: 'left'}}>
                              <th style={{padding: 10}}>User</th>
                              <th style={{padding: 10}}>Request Type</th>
                              <th style={{padding: 10}}>Details</th>
                              <th style={{padding: 10}}>Duration (Min)</th>
                              <th style={{padding: 10}}>Actions</th>
                          </tr>
                      </thead>
                      <tbody>
                          {pendingRequests.map(req => {
                              const isSignup = !req.approved
                              const isPrivacy = !!req.requested_privacy_level
                              const isRole = !isSignup && !isPrivacy && (req.requested_role !== req.role)
                              
                              let typeLabel = 'Unknown'
                              if (isSignup) typeLabel = 'New Signup'
                              else if (isPrivacy) typeLabel = 'Privacy Change'
                              else if (isRole) typeLabel = 'Role Change'

                              return (
                                  <tr key={req.id} style={{borderBottom: '1px solid var(--border)'}}>
                                      <td style={{padding: 10}}>
                                          <div style={{fontWeight: 500}}>{req.email}</div>
                                      </td>
                                      <td style={{padding: 10}}>
                                          <span className={`badge ${isSignup ? 'badge-blue' : 'badge-purple'}`} style={{
                                              background: isSignup ? 'rgba(59, 130, 246, 0.1)' : 'rgba(139, 92, 246, 0.1)',
                                              color: isSignup ? '#60a5fa' : '#a78bfa',
                                              padding: '2px 8px', borderRadius: 4, fontSize: 12
                                          }}>
                                              {typeLabel}
                                          </span>
                                      </td>
                                      <td style={{padding: 10}}>
                                          {isSignup && <div>Role: <b>{req.requested_role}</b></div>}
                                          {isRole && <div>{req.role} ➝ <b>{req.requested_role}</b></div>}
                                          {isPrivacy && <div>Level: <b>{req.requested_privacy_level}</b></div>}
                                          {req.request_reason && (
                                              <div style={{fontSize: 12, color: 'var(--text-secondary)', fontStyle: 'italic', marginTop: 4}}>
                                                  "{req.request_reason}"
                                              </div>
                                          )}
                                      </td>
                                      <td style={{padding: 10}}>
                                          {isPrivacy ? (
                                              <input 
                                                  type="number" 
                                                  placeholder="60"
                                                  min="0.25" max="60" step="0.25"
                                                  value={pendingDurations[req.id] || ''}
                                                  onChange={(e) => handlePendingDurationChange(req.id, e.target.value)}
                                                  className="auth-input"
                                                  style={{width: 80, padding: 4, fontSize: 13}}
                                              />
                                          ) : (
                                              <span style={{color: 'var(--text-secondary)'}}>-</span>
                                          )}
                                      </td>
                                      <td style={{padding: 10}}>
                                          <button 
                                            onClick={() => handleApproveRequest(req)} 
                                            disabled={busy}
                                            style={{marginRight: 8, cursor: 'pointer', background: 'var(--success-btn, #059669)', border: 'none', color: 'white', padding: '4px 12px', borderRadius: 4}}
                                          >
                                              Approve
                                          </button>
                                          <button 
                                            onClick={() => handleRejectRequest(req)}
                                            disabled={busy}
                                            style={{cursor: 'pointer', background: 'transparent', border: '1px solid var(--error-text)', color: 'var(--error-text)', padding: '4px 12px', borderRadius: 4}}
                                          >
                                              Reject
                                          </button>
                                      </td>
                                  </tr>
                              )
                          })}
                      </tbody>
                  </table>
              )}
          </div>
      )}

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
                      Manage User Access
                  </h3>
                  <p className="auth-subtitle" style={{marginBottom: 20}}>
                    {selectedUser.email}<br/>
                    <span style={{fontSize: 12, color: 'var(--text-secondary)'}}>
                        Base Role: {selectedUser.role || 'None'}
                    </span>
                  </p>
                  
                  <div style={{display: 'flex', gap: 10, marginBottom: 15}}>
                      <button 
                        className={`btn-small ${!isPrivacyMode ? 'active' : ''}`} 
                        onClick={() => setIsPrivacyMode(false)}
                        style={{flex: 1, padding: 8, background: !isPrivacyMode ? 'var(--primary)' : 'var(--bg-secondary)', border: '1px solid var(--border)'}}
                      >
                          Role Change
                      </button>
                      <button 
                        className={`btn-small ${isPrivacyMode ? 'active' : ''}`} 
                        onClick={() => setIsPrivacyMode(true)}
                        style={{flex: 1, padding: 8, background: isPrivacyMode ? 'var(--primary)' : 'var(--bg-secondary)', border: '1px solid var(--border)'}}
                      >
                          Privacy Level Change
                      </button>
                  </div>

                  <div className="input-group">
                      <label style={{fontSize: 14, fontWeight: 500, marginBottom: 4, display: 'block', textAlign: 'left'}}>
                          {isPrivacyMode ? 'Temporary Privacy Level' : 'New Role'}
                      </label>
                      
                      {isPrivacyMode ? (
                          <select value={privacyLevel} onChange={e => setPrivacyLevel(e.target.value)} className="auth-input">
                              {PRIVACY_OPTIONS.map(p => <option key={p.value} value={p.value}>{p.label}</option>)}
                          </select>
                      ) : (
                          <select value={role} onChange={e => setRole(e.target.value)} className="auth-input">
                              {ROLE_OPTIONS.map(r => <option key={r} value={r}>{r}</option>)}
                          </select>
                      )}
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
                        placeholder={isPrivacyMode ? "Required for privacy change" : "Leave blank for permanent"}
                      />
                      <div style={{fontSize: 12, color: 'var(--text-secondary)', marginTop: 4}}>
                        {isPrivacyMode 
                            ? "Privacy changes MUST be temporary (0.25-60 min)." 
                            : "Set time for temporary role, or leave blank for permanent change."}
                        {selectedUser.role_expires_at && (
                             <span style={{display: 'block', marginTop: 2, color: 'var(--warning-text, orange)'}}>
                               Current Access Expires in: <ExpiryTimer expiresAt={selectedUser.role_expires_at} />
                             </span>
                        )}
                      </div>
                  </div>

                  <div className="auth-actions" style={{marginTop: 20, gap: 10, justifyContent: 'flex-end'}}>
                      <button className="btn-reject" onClick={() => setSelectedUser(null)}>Cancel</button>
                      <button className="btn-approve" disabled={busy} onClick={handleUpdateAccess}>
                          Save Changes
                      </button>
                  </div>
              </div>
          </div>
      )}
    </div>
  )
}