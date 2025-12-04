import { useState, useEffect, useRef } from 'react'

function Icon({ path }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d={path} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}

function MessageRow({ role, content }) {
  const isUser = role === 'user'
  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && (
        <div className="message-avatar">
           {/* Simple SVG logo or similar for assistant */}
           <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{width: '100%', height: '100%', padding: 4, color: 'white'}}>
             <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
           </svg>
        </div>
      )}
      <div className={isUser ? 'message-bubble' : 'assistant-text'}>
        <div className="message-content">{content}</div>
      </div>
    </div>
  )
}

export default function ChatView({ messages, loading, onSend, disabled }) {
  const [text, setText] = useState('')
  const textareaRef = useRef(null)
  const scrollRef = useRef(null)

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [text])

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight
    }
  }, [messages, loading])

  const handleSend = (e) => {
    e && e.preventDefault()
    if (!text.trim()) return
    onSend(text.trim())
    setText('')
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const isEmpty = messages.length === 0

  return (
    <div className="chat-container">
      <div className="chat-scroll-area" ref={scrollRef}>
        {isEmpty ? (
          <div className="empty-state">
            <div className="empty-text">Ready when you are.</div>
          </div>
        ) : (
          <div className="messages-list">
             {messages.map((m) => (
              <MessageRow key={m.id} role={m.role} content={m.content} />
            ))}
            {loading && (
               <div className="message-row assistant">
                 <div className="message-avatar">
                   <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{width: '100%', height: '100%', padding: 4, color: 'white'}}>
                     <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                   </svg>
                 </div>
                 <div className="assistant-text">
                   <div className="message-content">Thinking...</div>
                 </div>
               </div>
            )}
          </div>
        )}
      </div>

      {/* Input Area - centered if empty, bottom if not. 
          Actually, in the CSS I made .empty-state take height. 
          To achieve the visual of input in middle for empty state, 
          we can move this block inside empty-state conditionally, 
          OR use CSS to position it. 
          For now, I'll keep it fixed at bottom to ensure consistent UX 
          as user starts typing, matching typical behavior. 
          The user's screenshot shows it in the middle, so let's try to support that visually.
      */}
      <div className="input-area-wrapper" style={isEmpty ? { position: 'absolute', top: '50%', transform: 'translateY(-50%)', background: 'transparent', bottom: 'auto' } : {}}>
        <form className="input-container" onSubmit={handleSend}>
          <button type="button" className="input-btn" title="Attachments">
             <Icon path="M12 4.5v15m7.5-7.5h-15" />
          </button>
          <textarea
            ref={textareaRef}
            className="chat-input-field"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything"
            disabled={disabled}
            rows={1}
          />
          {text.trim() ? (
             <button type="submit" className="input-btn send-btn" disabled={disabled || !text.trim()}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
             </button>
          ) : (
             <button type="button" className="input-btn" title="Voice Mode">
                <Icon path="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m6 7.5v3.75m-3.75 0h7.5M12 15.75a3 3 0 01-3-3V4.5a3 3 0 116 0v8.25a3 3 0 01-3 3z" />
             </button>
          )}
        </form>
      </div>
    </div>
  )
}