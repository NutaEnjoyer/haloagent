function CallDetailModal({ call, onClose }) {
  if (!call) return null

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h2>Детали звонка</h2>
          <button className="modal-close" onClick={onClose}>×</button>
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(2, 1fr)',
            gap: '1rem',
            marginBottom: '1.5rem'
          }}>
            <div>
              <strong>Телефон:</strong>
              <p>{call.phone_masked}</p>
            </div>
            <div>
              <strong>Дата:</strong>
              <p>{new Date(call.created_at).toLocaleString('ru-RU')}</p>
            </div>
            <div>
              <strong>Длительность:</strong>
              <p>{Math.floor(call.duration_sec / 60)}:{String(call.duration_sec % 60).padStart(2, '0')}</p>
            </div>
            <div>
              <strong>Статус:</strong>
              <p>
                <span className={`badge badge-${call.disposition}`}>
                  {call.disposition}
                </span>
              </p>
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <strong>Резюме разговора:</strong>
            <div className="summary-box">
              {call.summary}
            </div>
          </div>

          {call.crm_record && (
            <div className="crm-box">
              <h3>CRM</h3>
              <p><strong>Статус:</strong> {call.crm_record.status}</p>
              {call.crm_record.interest && (
                <p><strong>Интерес:</strong> {call.crm_record.interest}</p>
              )}
              <p>
                <strong>Telegram ссылка:</strong>{' '}
                {call.crm_record.telegram_link_sent ? '✓ Отправлена' : '✗ Не отправлена'}
              </p>
              <p>
                <strong>Telegram подключен:</strong>{' '}
                {call.crm_record.telegram_connected ? '✓ Да' : '✗ Нет'}
              </p>
            </div>
          )}

          <div>
            <h3 style={{ marginBottom: '1rem' }}>Транскрипт разговора</h3>
            <div className="transcript">
              {call.transcript.map((turn, index) => (
                <div
                  key={index}
                  className={`transcript-turn ${turn.speaker}`}
                >
                  <div className="speaker-label">
                    {turn.speaker === 'user' ? 'Клиент' : 'Ассистент'}
                  </div>
                  <div>{turn.text}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default CallDetailModal
