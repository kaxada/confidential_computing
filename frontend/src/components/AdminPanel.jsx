import { useEffect, useState } from 'react'
import { api, ROLE_OPTIONS } from '../api'

export default function AdminPanel({ user, onError }) {
  const [pending, setPending] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [role, setRole] = useState('researcher')
  const [status, setStatus] = useState('')
  const [busy, setBusy] = useState(false)

  const loadPending = async () => {
    if (!user?.token) return
    try {
      setStatus('')
      onError(null)
      const data = await api.pending(user.token)
      setPending(data)
      if (!data.find((p) => p.id === selectedId)) setSelectedId('')
    } catch (err) {
      onError(err.message)
    }
  }

  useEffect(() => {
    loadPending()
  }, [user?.token])

  const approve = async () => {
    try {
      setBusy(true)
      setStatus('')
      onError(null)
      await api.approve({ user_id: Number(selectedId), role }, user.token)
      setSelectedId('')
      setStatus('User approved.')
      await loadPending()
    } catch (err) {
      onError(err.message)
      setStatus('')
    } finally {
      setBusy(false)
    }
  }

  const remove = async () => {
    try {
      setBusy(true)
      setStatus('')
      onError(null)
      await api.removePending(Number(selectedId), user.token)
      setSelectedId('')
      setStatus('Request deleted.')
      await loadPending()
    } catch (err) {
      onError(err.message)
      setStatus('')
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="admin-container">
      <div className="admin-header">
        <h2 className="admin-title">Admin Dashboard</h2>
        <p className="admin-subtitle">Manage pending user registrations</p>
      </div>

      <div className="admin-grid">
        <div className="pending-section">
            <div className="section-header">
                <h3>Pending Requests</h3>
                <span className="badge">{pending.length}</span>
            </div>
            <div className="pending-list-modern">
                {pending.map((p) => (
                <button 
                    key={p.id} 
                    className={`pending-item ${selectedId === p.id ? 'active' : ''}`} 
                    onClick={() => setSelectedId(p.id)}
                >
                    <div className="pending-info">
                        <div className="pending-email">{p.email}</div>
                        <div className="pending-role">Requested: {p.requested_role}</div>
                    </div>
                    <div className="chevron">›</div>
                </button>
                ))}
                {!pending.length && <div className="empty-pending">No pending requests.</div>}
            </div>
        </div>

        <div className="action-section">
            {selectedId ? (
                <div className="action-card">
                    <h3>Review Request</h3>
                    <div className="selected-user-info">
                        <label>User Email</label>
                        <div className="value">{pending.find(p => p.id === selectedId)?.email}</div>
                    </div>
                    
                    <div className="form-group">
                        <label>Assign Role</label>
                        <select value={role} onChange={(e) => setRole(e.target.value)} className="admin-select">
                            {ROLE_OPTIONS.map((r) => (
                                <option key={r} value={r}>{r.charAt(0).toUpperCase() + r.slice(1)}</option>
                            ))}
                        </select>
                    </div>

                    <div className="action-buttons">
                        <button type="button" className="btn-approve" disabled={busy} onClick={approve}>
                            Approve User
                        </button>
                        <button type="button" className="btn-reject" disabled={busy} onClick={remove}>
                            Reject Request
                        </button>
                    </div>
                    {status && <div className="action-status">{status}</div>}
                </div>
            ) : (
                <div className="placeholder-card">
                    <div className="placeholder-icon">←</div>
                    <p>Select a request to review</p>
                </div>
            )}
        </div>
      </div>
    </div>
  )
}