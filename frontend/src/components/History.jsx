import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { demoAPI } from '../api/client'
import CallDetailModal from './CallDetailModal'
import ChatDetailModal from './ChatDetailModal'

function History() {
  const navigate = useNavigate()
  const [interactions, setInteractions] = useState([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState('all') // all, call, chat
  const [sortBy, setSortBy] = useState('date') // date, disposition

  const [selectedCall, setSelectedCall] = useState(null)
  const [selectedChat, setSelectedChat] = useState(null)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await demoAPI.getInteractions()
        setInteractions(data.items)
      } catch (err) {
        console.error('Error loading history:', err)
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

  const filteredInteractions = interactions.filter(item => {
    if (filter === 'all') return true
    return item.type === filter
  })

  const sortedInteractions = [...filteredInteractions].sort((a, b) => {
    if (sortBy === 'date') {
      return new Date(b.created_at) - new Date(a.created_at)
    }
    return 0
  })

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <span className="spinner" style={{ width: '50px', height: '50px', borderWidth: '4px' }}></span>
        <p style={{ marginTop: '1.5rem', color: 'var(--text-secondary)' }}>Загрузка истории...</p>
      </div>
    )
  }

  return (
    <>
      <div className="card">
        <h2 className="card-title">История сессий</h2>

        {/* Filters */}
        <div style={{
          display: 'flex',
          gap: '1rem',
          marginBottom: '2rem',
          flexWrap: 'wrap',
          alignItems: 'center'
        }}>
          <div>
            <label style={{
              display: 'block',
              color: 'var(--text-secondary)',
              fontSize: '0.85rem',
              marginBottom: '0.5rem',
              textTransform: 'uppercase',
              letterSpacing: '1px'
            }}>
              Фильтр
            </label>
            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={() => setFilter('all')}
                className="btn btn-secondary"
                style={{
                  padding: '0.75rem 1.5rem',
                  fontSize: '0.9rem',
                  ...(filter === 'all' && {
                    background: 'var(--premium-gradient)',
                    color: 'white',
                    boxShadow: 'var(--shadow-glow)'
                  })
                }}
              >
                Все
              </button>
              <button
                onClick={() => setFilter('call')}
                className="btn btn-secondary"
                style={{
                  padding: '0.75rem 1.5rem',
                  fontSize: '0.9rem',
                  ...(filter === 'call' && {
                    background: 'var(--premium-gradient)',
                    color: 'white',
                    boxShadow: 'var(--shadow-glow)'
                  })
                }}
              >
                📞 Звонки
              </button>
              <button
                onClick={() => setFilter('chat')}
                className="btn btn-secondary"
                style={{
                  padding: '0.75rem 1.5rem',
                  fontSize: '0.9rem',
                  ...(filter === 'chat' && {
                    background: 'var(--premium-gradient)',
                    color: 'white',
                    boxShadow: 'var(--shadow-glow)'
                  })
                }}
              >
                💬 Чаты
              </button>
            </div>
          </div>

          <div style={{ marginLeft: 'auto' }}>
            <label style={{
              display: 'block',
              color: 'var(--text-secondary)',
              fontSize: '0.85rem',
              marginBottom: '0.5rem',
              textTransform: 'uppercase',
              letterSpacing: '1px'
            }}>
              Всего: {sortedInteractions.length}
            </label>
          </div>
        </div>

        {/* Table */}
        {sortedInteractions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>
              Нет сессий по выбранному фильтру
            </p>
            <button
              onClick={() => navigate('/launch')}
              className="btn btn-primary"
              style={{ marginTop: '1.5rem' }}
            >
              Запустить первое демо
            </button>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>Тип</th>
                  <th>Канал</th>
                  <th>Дата / Время</th>
                  <th>Длительность</th>
                  <th>Статус</th>
                  <th>Источник</th>
                  <th>Действия</th>
                </tr>
              </thead>
              <tbody>
                {sortedInteractions.map((interaction) => (
                  <tr key={interaction.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: '0.85rem' }}>
                      {interaction.id.substring(0, 8)}...
                    </td>
                    <td>
                      {interaction.type === 'call' ? '📞 Звонок' : '💬 Чат'}
                    </td>
                    <td>
                      {interaction.channel === 'voice' ? 'Голос' : 'Telegram'}
                    </td>
                    <td>
                      {new Date(interaction.created_at).toLocaleString('ru-RU', {
                        day: '2-digit',
                        month: '2-digit',
                        year: 'numeric',
                        hour: '2-digit',
                        minute: '2-digit'
                      })}
                    </td>
                    <td>
                      {interaction.duration_sec ? `${interaction.duration_sec}s` : '-'}
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
                        {interaction.is_demo ? 'Demo' : 'Real'}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => handleShowDetails(interaction.id, interaction.type)}
                        className="btn btn-secondary"
                        style={{ padding: '0.5rem 1rem', fontSize: '0.85rem' }}
                      >
                        Детали
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div style={{
          marginTop: '2rem',
          display: 'flex',
          gap: '1rem',
          justifyContent: 'center'
        }}>
          <button
            onClick={() => navigate('/')}
            className="btn btn-secondary"
          >
            На главную
          </button>
          <button
            onClick={() => navigate('/launch')}
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

export default History
