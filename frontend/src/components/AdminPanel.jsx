import { useEffect, useState } from 'react'
import { api, ROLE_OPTIONS } from '../api'

export default function AdminPanel({ user, onError }) {
  const [pending, setPending] = useState([])
  const [selectedId, setSelectedId] = useState('')
  const [role, setRole] = useState('researcher')

  const loadPending = async () => {
    if (!user?.token) return
    try {
      const data = await api.pending(user.token)
      setPending(data)
    } catch (err) {
      onError(err.message)
    }
  }

  useEffect(() => {
    loadPending()
  }, [user?.token])

  const approve = async () => {
    try {
      await api.approve({ user_id: Number(selectedId), role }, user.token)
      setSelectedId('')
      await loadPending()
    } catch (err) {
      onError(err.message)
    }
  }

  return (
    <div className="admin-card">
      <div className="card-title">Admin</div>
      <div className="muted">Approve users</div>
      <div className="pending-list">
        {pending.map((p) => (
          <button key={p.id} className={selectedId == p.id ? 'pending active' : 'pending'} onClick={() => setSelectedId(p.id)}>
            {p.email} · requested {p.requested_role}
          </button>
        ))}
        {!pending.length && <div className="muted">No pending users.</div>}
      </div>
      <div className="stack">
        <label className="label">Role</label>
        <select value={role} onChange={(e) => setRole(e.target.value)}>
          {ROLE_OPTIONS.map((r) => (
            <option key={r} value={r}>{r}</option>
          ))}
        </select>
        <button className="primary" disabled={!selectedId} onClick={approve}>Approve</button>
      </div>
    </div>
  )
}
