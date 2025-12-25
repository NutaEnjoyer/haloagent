import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { demoAPI } from '../api/client'
import CallDetailModal from './CallDetailModal'
import ChatDetailModal from './ChatDetailModal'

function Analytics() {
  const { sessionId } = useParams()
  const navigate = useNavigate()

  const [analytics, setAnalytics] = useState(null)
  const [interactions, setInteractions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  // Modal states
  const [selectedCall, setSelectedCall] = useState(null)
  const [selectedChat, setSelectedChat] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analyticsData, interactionsData] = await Promise.all([
          demoAPI.getAnalytics(),
          demoAPI.getInteractions()
        ])

        setAnalytics(analyticsData)
        setInteractions(interactionsData.items)
      } catch (err) {
        setError(err.response?.data?.detail || 'Ошибка при загрузке данных')
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const handleShowDetails = async (interactionId, type) => {
    try {
      const detail = await demoAPI.getInteractionDetail(interactionId)

      if (type === 'call') {
        setSelectedCall(detail)
      } else {
        setSelectedChat(detail)
      }
    } catch (err) {
      alert('Ошибка при загрузке деталей')
    }
  }

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <span className="spinner" style={{ width: '40px', height: '40px', borderWidth: '4px' }}></span>
        <p style={{ marginTop: '1rem', color: '#666' }}>Загрузка аналитики...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="card">
        <div style={{
          padding: '2rem',
          background: '#ffebee',
          color: '#c62828',
          borderRadius: '8px',
          textAlign: 'center'
        }}>
          <h3>Ошибка</h3>
          <p>{error}</p>
        </div>
      </div>
    )
  }

  return (
    <>
      <div className="card">
        <h2 className="card-title">Аналитика HALO</h2>

        {/* Metrics Grid */}
        <div className="analytics-grid">
          <div className="metric-card">
            <div className="metric-value">{analytics.totals.calls}</div>
            <div className="metric-label">Всего звонков</div>
          </div>

          <div className="metric-card">
            <div className="metric-value">{analytics.totals.chats}</div>
            <div className="metric-label">Всего чатов</div>
          </div>

          <div className="metric-card">
            <div className="metric-value">{(analytics.totals.lead_rate * 100).toFixed(0)}%</div>
            <div className="metric-label">Конверсия в лиды</div>
          </div>

          <div className="metric-card">
            <div className="metric-value">{analytics.totals.avg_call_duration_sec}с</div>
            <div className="metric-label">Средняя длительность</div>
          </div>
        </div>

        {/* Funnel */}
        <div style={{ marginTop: '2rem' }}>
          <h3 style={{
            marginBottom: '1.5rem',
            fontSize: '1.8rem',
            fontWeight: 700,
            background: 'var(--primary-gradient)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            Воронка обращений
          </h3>
          <div className="funnel-container">
            <div className="funnel-grid">
              <div className="funnel-item">
                <div className="funnel-value">{analytics.funnel.called}</div>
                <div className="funnel-label">Позвонили</div>
              </div>

              <div className="funnel-item">
                <div className="funnel-value">{analytics.funnel.talked}</div>
                <div className="funnel-label">Разговаривали</div>
              </div>

              <div className="funnel-item">
                <div className="funnel-value">{analytics.funnel.interested}</div>
                <div className="funnel-label">Заинтересованы</div>
              </div>

              <div className="funnel-item">
                <div className="funnel-value">{analytics.funnel.lead}</div>
                <div className="funnel-label">Лиды</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Interactions Table */}
      <div className="card">
        <h2 className="card-title">Все обращения</h2>

        <div className="table-container">
          <table>
            <thead>
              <tr>
                <th>Тип</th>
                <th>Канал</th>
                <th>Дата/Время</th>
                <th>Статус</th>
                <th>Источник</th>
                <th>Действия</th>
              </tr>
            </thead>
            <tbody>
              {interactions.map((interaction) => (
                <tr key={interaction.id}>
                  <td>
                    {interaction.type === 'call' ? '📞 Звонок' : '💬 Чат'}
                  </td>
                  <td>
                    {interaction.channel === 'voice' ? 'Голос' : 'Telegram'}
                  </td>
                  <td>
                    {new Date(interaction.created_at).toLocaleString('ru-RU')}
                  </td>
                  <td>
                    {interaction.disposition ? (
                      <span className={`badge badge-${interaction.disposition}`}>
                        {interaction.disposition}
                      </span>
                    ) : (
                      '-'
                    )}
                  </td>
                  <td>
                    <span className={`badge ${interaction.is_demo ? 'badge-demo' : 'badge-real'}`}>
                      {interaction.is_demo ? 'Demo' : 'Вы'}
                    </span>
                  </td>
                  <td>
                    <button
                      onClick={() => handleShowDetails(interaction.id, interaction.type)}
                      className="btn btn-secondary"
                      style={{ padding: '0.5rem 1rem', fontSize: '0.875rem' }}
                    >
                      Детали
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        <div style={{
          marginTop: '2rem',
          textAlign: 'center'
        }}>
          <button
            onClick={() => navigate('/')}
            className="btn btn-primary"
          >
            Запустить новое демо
          </button>
        </div>
      </div>

      {/* Modals */}
      {selectedCall && (
        <CallDetailModal
          call={selectedCall}
          onClose={() => setSelectedCall(null)}
        />
      )}

      {selectedChat && (
        <ChatDetailModal
          chat={selectedChat}
          onClose={() => setSelectedChat(null)}
        />
      )}
    </>
  )
}

export default Analytics
