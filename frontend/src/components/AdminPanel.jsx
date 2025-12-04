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
    <div className="admin-card">
      <div className="card-title">Admin</div>
      <div className="muted">Manage pending users</div>
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
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px' }}>
          <button type="button" className="primary" disabled={!selectedId || busy} onClick={approve}>Approve</button>
          <button type="button" className="ghost" disabled={!selectedId || busy} onClick={remove}>Delete</button>
        </div>
        {status && <div className="muted">{status}</div>}
      </div>
    </div>
  )
}
