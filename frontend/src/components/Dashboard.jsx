import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { demoAPI } from '../api/client'

function Dashboard() {
  const navigate = useNavigate()
  const [analytics, setAnalytics] = useState(null)
  const [recentSessions, setRecentSessions] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const fetchData = async () => {
      try {
        const [analyticsData, interactionsData] = await Promise.all([
          demoAPI.getAnalytics(),
          demoAPI.getInteractions()
        ])

        setAnalytics(analyticsData)
        setRecentSessions(interactionsData.items.slice(0, 5))
      } catch (err) {
        console.error('Error loading dashboard:', err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <span className="spinner" style={{ width: '50px', height: '50px', borderWidth: '4px' }}></span>
        <p style={{ marginTop: '1.5rem', color: 'var(--text-secondary)' }}>Загрузка дашборда...</p>
      </div>
    )
  }

  return (
    <>
      {/* Welcome Section */}
      <div className="card" style={{
        background: 'var(--premium-gradient)',
        color: 'white',
        textAlign: 'center',
        padding: '3rem'
      }}>
        <h1 style={{ fontSize: '2.5rem', marginBottom: '1rem', fontWeight: '800' }}>
          Добро пожаловать в HALO
        </h1>
        <p style={{ fontSize: '1.2rem', opacity: 0.95, marginBottom: '2rem' }}>
          Премиум платформа для управления AI ассистентом
        </p>
        <button
          onClick={() => navigate('/launch')}
          className="btn btn-secondary"
          style={{
            background: 'white',
            color: '#6366f1',
            fontSize: '1.1rem',
            padding: '1rem 2.5rem'
          }}
        >
          Запустить новое демо
        </button>
      </div>

      {/* Quick Stats */}
      {analytics && (
        <div className="analytics-grid">
          <div className="metric-card" style={{ background: 'var(--premium-gradient)' }}>
            <div className="metric-value">{analytics.totals.calls}</div>
            <div className="metric-label">Всего звонков</div>
          </div>

          <div className="metric-card" style={{ background: 'var(--secondary-gradient)' }}>
            <div className="metric-value">{analytics.totals.chats}</div>
            <div className="metric-label">Всего чатов</div>
          </div>

          <div className="metric-card" style={{ background: 'var(--success-gradient)' }}>
            <div className="metric-value">{(analytics.totals.lead_rate * 100).toFixed(0)}%</div>
            <div className="metric-label">Конверсия</div>
          </div>

          <div className="metric-card" style={{ background: 'var(--gold-gradient)' }}>
            <div className="metric-value">{analytics.funnel.interested}</div>
            <div className="metric-label">Заинтересованы</div>
          </div>
        </div>
      )}

      {/* Recent Sessions */}
      <div className="card">
        <h2 className="card-title">Последние сессии</h2>

        {recentSessions.length === 0 ? (
          <div style={{ textAlign: 'center', padding: '3rem' }}>
            <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem' }}>
              Пока нет сессий. Запустите первое демо!
            </p>
            <button
              onClick={() => navigate('/launch')}
              className="btn btn-primary"
              style={{ marginTop: '1.5rem' }}
            >
              Запустить демо
            </button>
          </div>
        ) : (
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>Тип</th>
                  <th>Канал</th>
                  <th>Дата</th>
                  <th>Статус</th>
                  <th>Источник</th>
                </tr>
              </thead>
              <tbody>
                {recentSessions.map((session) => (
                  <tr
                    key={session.id}
                    onClick={() => navigate(`/analytics/${session.id}`)}
                    style={{ cursor: 'pointer' }}
                  >
                    <td>
                      {session.type === 'call' ? '📞 Звонок' : '💬 Чат'}
                    </td>
                    <td>
                      {session.channel === 'voice' ? 'Голос' : 'Telegram'}
                    </td>
                    <td>
                      {new Date(session.created_at).toLocaleString('ru-RU')}
                    </td>
                    <td>
                      {session.disposition ? (
                        <span className={`badge badge-${session.disposition}`}>
                          {session.disposition}
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td>
                      <span className={`badge ${session.is_demo ? 'badge-demo' : 'badge-real'}`}>
                        {session.is_demo ? 'Demo' : 'Real'}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        <div style={{ marginTop: '2rem', display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <button
            onClick={() => navigate('/history')}
            className="btn btn-secondary"
          >
            Посмотреть всю историю
          </button>
          <button
            onClick={() => navigate('/analytics/' + (recentSessions[0]?.id || ''))}
            className="btn btn-primary"
            disabled={recentSessions.length === 0}
          >
            Аналитика
          </button>
        </div>
      </div>

      {/* Quick Actions */}
      <div className="card">
        <h2 className="card-title">Быстрые действия</h2>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '1.5rem'
        }}>
          <div
            onClick={() => navigate('/launch')}
            style={{
              padding: '2rem',
              background: 'rgba(99, 102, 241, 0.1)',
              borderRadius: '16px',
              border: '1px solid rgba(99, 102, 241, 0.3)',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              textAlign: 'center'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-5px)'
              e.currentTarget.style.boxShadow = 'var(--shadow-lg)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = 'var(--shadow-sm)'
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🚀</div>
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Запустить демо</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Создать новый демо-звонок
            </p>
          </div>

          <div
            onClick={() => navigate('/templates')}
            style={{
              padding: '2rem',
              background: 'rgba(168, 85, 247, 0.1)',
              borderRadius: '16px',
              border: '1px solid rgba(168, 85, 247, 0.3)',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              textAlign: 'center'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-5px)'
              e.currentTarget.style.boxShadow = 'var(--shadow-lg)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = 'var(--shadow-sm)'
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📝</div>
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Шаблоны</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Управление промптами
            </p>
          </div>

          <div
            onClick={() => navigate('/history')}
            style={{
              padding: '2rem',
              background: 'rgba(20, 184, 166, 0.1)',
              borderRadius: '16px',
              border: '1px solid rgba(20, 184, 166, 0.3)',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              textAlign: 'center'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-5px)'
              e.currentTarget.style.boxShadow = 'var(--shadow-lg)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = 'var(--shadow-sm)'
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📊</div>
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>История</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Все сессии и звонки
            </p>
          </div>

          <div
            onClick={() => navigate('/settings')}
            style={{
              padding: '2rem',
              background: 'rgba(251, 191, 36, 0.1)',
              borderRadius: '16px',
              border: '1px solid rgba(251, 191, 36, 0.3)',
              cursor: 'pointer',
              transition: 'all 0.3s ease',
              textAlign: 'center'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-5px)'
              e.currentTarget.style.boxShadow = 'var(--shadow-lg)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = 'var(--shadow-sm)'
            }}
          >
            <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>⚙️</div>
            <h3 style={{ color: 'var(--text-primary)', marginBottom: '0.5rem' }}>Настройки</h3>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.9rem' }}>
              Конфигурация системы
            </p>
          </div>
        </div>
      </div>
    </>
  )
}

export default Dashboard
