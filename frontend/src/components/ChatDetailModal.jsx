function ChatDetailModal({ chat, onClose }) {
  if (!chat) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Детали чата</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ marginBottom: '1.5rem' }}>
            <strong>Дата:</strong>
            <p>{new Date(chat.created_at).toLocaleString('ru-RU')}</p>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <strong>Резюме:</strong>
            <div className="summary-box">
              {chat.summary}
            </div>
          </div>

          <div>
            <h3 style={{ marginBottom: '1rem' }}>Сообщения</h3>
            {chat.messages.map((message, index) => (
              <div key={index} className="chat-message">
                <div className="message-meta">
                  <strong>{message.from === 'assistant' ? 'HALO Ассистент' : 'Клиент'}</strong>
                  {' • '}
                  {new Date(message.timestamp).toLocaleTimeString('ru-RU')}
                </div>
                <div className="message-text">{message.text}</div>
              </div>
            ))}
          </div>

          <div className="info-box" style={{ textAlign: 'center' }}>
            <p style={{ fontSize: '0.875rem', margin: 0 }}>
              Демо-чат • Визуализация Telegram переписки
            </p>
          </div>
        </div>
      </div>
    </div>
  )
}

export default ChatDetailModal
