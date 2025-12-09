const API_BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
export const ROLE_OPTIONS = ['student', 'researcher', 'pi', 'admin']

async function request(path, { method = 'GET', body, token } = {}) {
  const res = await fetch(`${API_BASE}${path}`, {
    method,
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: body ? JSON.stringify(body) : undefined,
  })
  const data = await res.json().catch(() => ({}))
  if (!res.ok) {
    const msg = data.detail || res.statusText
    throw new Error(msg)
  }
  return data
}

export const api = {
  signup: (payload) => request('/auth/signup', { method: 'POST', body: payload }),
  login: (payload) => request('/auth/login', { method: 'POST', body: payload }),
  pending: (token) => request('/admin/pending', { token }),
  approve: (payload, token) => request('/admin/approve', { method: 'POST', body: payload, token }),
  removePending: (userId, token) => request(`/admin/pending/${userId}`, { method: 'DELETE', token }),
  me: (token) => request('/auth/me', { token }),
  deleteAccount: (token) => request('/auth/me', { method: 'DELETE', token }),
  requestRole: (role, reason, token) => request('/auth/request-role', { method: 'POST', body: { role, reason }, token }),
  logout: (token) => request('/auth/logout', { method: 'POST', token }),
  
  admin: {
      pending: (token) => request('/admin/pending', { token }),
      approve: (payload, token) => request('/admin/approve', { method: 'POST', body: payload, token }),
      removePending: (userId, token) => request(`/admin/pending/${userId}`, { method: 'DELETE', token }),
      users: (token) => request('/admin/users', { token }),
      logs: (token) => request('/admin/logs', { token }),
      updateRole: (userId, role, durationMinutes, token) => request(`/admin/users/${userId}/role`, { method: 'PUT', body: { role, duration_minutes: durationMinutes }, token }),
      deleteUser: (userId, token) => request(`/admin/users/${userId}`, { method: 'DELETE', token }),
  },

  chat: (payload, token) => request('/chat/query', { method: 'POST', body: payload, token }),
  threads: (token) => request('/chat/threads', { token }),
  updateThread: (threadId, title, token) => request(`/chat/threads/${threadId}`, { method: 'PATCH', body: { title }, token }),
  deleteThread: (threadId, token) => request(`/chat/threads/${threadId}`, { method: 'DELETE', token }),
  messages: (threadId, token) => request(`/chat/threads/${threadId}/messages`, { token }),
}

export { API_BASE }
