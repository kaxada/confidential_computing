import { useState } from 'react'

function MessageBubble({ role, content }) {
  const isUser = role === 'user'
  return (
    <div className={`bubble ${isUser ? 'user' : 'assistant'}`}>
      <div className="bubble-role">{isUser ? 'You' : 'Assistant'}</div>
      <div className="bubble-content">{content}</div>
    </div>
  )
}

export default function ChatView({ messages, loading, onSend, disabled }) {
  const [text, setText] = useState('')

  const handleSend = (e) => {
    e.preventDefault()
    if (!text.trim()) return
    onSend(text.trim())
    setText('')
  }

  return (
    <div className="chat-card">
      <div className="chat-log">
        {messages.map((m) => (
          <MessageBubble key={m.id} role={m.role} content={m.content} />
        ))}
        {loading && <div className="muted">Loading messages…</div>}
        {!messages.length && <div className="muted">Start a new conversation.</div>}
      </div>
      <form className="chat-input" onSubmit={handleSend}>
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          placeholder={disabled ? 'Log in to chat' : 'Send a message'}
          disabled={disabled}
        />
        <button type="submit" className="primary" disabled={disabled || !text.trim()}>Send</button>
      </form>
    </div>
  )
}
