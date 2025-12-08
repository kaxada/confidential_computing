import { useState, useEffect, useRef, memo } from 'react'

function Icon({ path }) {
  return (
    <svg width="24" height="24" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d={path} stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  )
}

const MessageRow = memo(({ role, content, animate }) => {
  const isUser = role === 'user'
  const [displayContent, setDisplayContent] = useState(animate && !isUser ? '' : content)

  useEffect(() => {
    if (!animate || isUser) {
      setDisplayContent(content)
      return
    }

    let i = 0
    setDisplayContent('')
    const interval = setInterval(() => {
      i++
      setDisplayContent(content.substring(0, i))
      if (i >= content.length) {
        clearInterval(interval)
      }
    }, 15) // Typing speed

    return () => clearInterval(interval)
  }, [content, animate, isUser])

  return (
    <div className={`message-row ${isUser ? 'user' : 'assistant'}`}>
      {!isUser && (
        <div className="message-avatar">
           {/* SVG logo for assistant */}
           <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{width: '100%', height: '100%', padding: 4, color: 'white'}}>
             <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
           </svg>
        </div>
      )}
      <div className={isUser ? 'message-bubble' : 'assistant-text'}>
        <div className="message-content">{displayContent}</div>
      </div>
    </div>
  )
})

export default function ChatView({ messages, loading, thinking, latestResponseId, onSend, disabled, user }) {
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
  }, [messages, thinking])

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
            <div className="empty-text">Hello, {user?.name || user?.email || 'User'}</div>
          </div>
        ) : (
          <div className="messages-list">
             {messages.map((m, index) => (
              <MessageRow 
                key={m.id || index} 
                role={m.role} 
                content={m.content} 
                animate={m.id === latestResponseId}
              />
            ))}
            {thinking && (
               <div className="message-row assistant">
                 <div className="message-avatar">
                   <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" style={{width: '100%', height: '100%', padding: 4, color: 'white'}}>
                     <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 13.5l10.5-11.25L12 10.5h8.25L9.75 21.75 12 13.5H3.75z" />
                   </svg>
                 </div>
                 <div className="assistant-text">
                   <div className="message-bubble" style={{background: 'transparent', padding: '10px 0'}}>
                     <div className="typing-indicator">
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                        <div className="typing-dot"></div>
                     </div>
                   </div>
                 </div>
               </div>
            )}
          </div>
        )}
      </div>

      <div className="input-area-wrapper" style={isEmpty ? { position: 'absolute', top: '50%', transform: 'translateY(-50%)', background: 'transparent', bottom: 'auto' } : {}}>
        <form className="input-container" onSubmit={handleSend}>
          <textarea
            ref={textareaRef}
            className="chat-input-field"
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Type your query here"
            disabled={disabled}
            rows={1}
            autoFocus
          />
          {text.trim() && (
             <button type="submit" className="input-btn send-btn" disabled={disabled || !text.trim()}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M5 12h14M12 5l7 7-7 7" strokeLinecap="round" strokeLinejoin="round"/>
                </svg>
             </button>
          )}
        </form>
      </div>
    </div>
  )
}
