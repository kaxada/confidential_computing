import { useEffect, useState } from 'react'
import { api, ROLE_OPTIONS } from '../api'

export default function AdminPanel({ user, onError }) {
  const [tab, setTab] = useState('users')
  const [users, setUsers] = useState([])
  const [logs, setLogs] = useState([])
  const [selectedUser, setSelectedUser] = useState(null)
  const [role, setRole] = useState('researcher')
  const [expiresAt, setExpiresAt] = useState('')
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
          setRole(selectedUser.role || selectedUser.requested_role || 'researcher')
          setExpiresAt(selectedUser.role_expires_at ? selectedUser.role_expires_at.split('T')[0] : '')
      }
  }, [selectedUser])

  const handleUpdateRole = async () => {
    if (!selectedUser) return
    try {
      setBusy(true)
      const isoDate = expiresAt ? new Date(expiresAt).toISOString() : null
      await api.admin.updateRole(selectedUser.id, role, isoDate, user.token)
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
                                  {u.role_expires_at ? new Date(u.role_expires_at).toLocaleDateString() : 'Permanent'}
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
                  <h3 className="auth-title" style={{fontSize: 20}}>Edit User Role</h3>
                  <p className="auth-subtitle" style={{marginBottom: 20}}>{selectedUser.email}</p>
                  
                  <div className="input-group">
                      <label style={{fontSize: 14, fontWeight: 500, marginBottom: 4, display: 'block', textAlign: 'left'}}>Role</label>
                      <select value={role} onChange={e => setRole(e.target.value)} className="auth-input">
                          {ROLE_OPTIONS.map(r => <option key={r} value={r}>{r}</option>)}
                      </select>
                  </div>

                  <div className="input-group" style={{marginTop: 15}}>
                      <label style={{fontSize: 14, fontWeight: 500, marginBottom: 4, display: 'block', textAlign: 'left'}}>Expiration (Optional)</label>
                      <input 
                        type="date" 
                        className="auth-input" 
                        value={expiresAt} 
                        onChange={e => setExpiresAt(e.target.value)}
                      />
                      <div style={{fontSize: 12, color: 'var(--text-secondary)', marginTop: 4}}>Leave blank for permanent access</div>
                  </div>

                  <div className="auth-actions" style={{marginTop: 20, gap: 10, justifyContent: 'flex-end'}}>
                      <button className="btn-reject" onClick={() => setSelectedUser(null)}>Cancel</button>
                      <button className="btn-approve" disabled={busy} onClick={handleUpdateRole}>Save Changes</button>
                  </div>
              </div>
          </div>
      )}
    </div>
  )
}