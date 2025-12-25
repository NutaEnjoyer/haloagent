import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { demoAPI } from '../api/client'

function DemoAnalytics() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [analytics, setAnalytics] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchAnalytics = async () => {
      try {
        const data = await demoAPI.getDemoAnalytics(sessionId)
        setAnalytics(data)
      } catch (err) {
        setError(err.response?.data?.detail || 'Ошибка при загрузке аналитики')
      } finally {
        setLoading(false)
      }
    }

    fetchAnalytics()
  }, [sessionId])

  const getInterestBadge = (interest) => {
    const badges = {
      interested: {
        text: 'Заинтересован',
        style: { backgroundColor: '#d1f4e0', color: '#1e7e34', border: '1px solid #c3e6cb' }
      },
      not_interested: {
        text: 'Не заинтересован',
        style: { backgroundColor: '#f8d7da', color: '#721c24', border: '1px solid #f5c6cb' }
      },
      maybe: {
        text: 'Возможно заинтересован',
        style: { backgroundColor: '#fff3cd', color: '#856404', border: '1px solid #ffeeba' }
      },
      unknown: {
        text: 'Неизвестно',
        style: { backgroundColor: '#e2e3e5', color: '#383d41', border: '1px solid #d6d8db' }
      }
    }
    const badge = badges[interest] || badges.unknown
    return (
      <span style={{
        display: 'inline-block',
        padding: '0.375rem 0.75rem',
        borderRadius: '6px',
        fontSize: '0.875rem',
        fontWeight: '500',
        ...badge.style
      }}>
        {badge.text}
      </span>
    )
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
        <div className="alert alert-error" style={{ textAlign: 'center' }}>
          <h3>Ошибка</h3>
          <p>{error}</p>
          <button
            onClick={() => navigate('/')}
            className="btn btn-secondary"
            style={{ marginTop: '1rem' }}
          >
            Вернуться назад
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <h2 className="card-title">Результаты анализа</h2>

      {/* Analysis Summary */}
      <div style={{
        marginBottom: '2rem',
        padding: '1.5rem',
        backgroundColor: '#f8f9fa',
        borderRadius: '12px',
        border: '1px solid #e9ecef'
      }}>
        <h3 style={{ marginBottom: '1.5rem', fontSize: '1.2rem', color: '#212529', fontWeight: '600' }}>
          Анализ разговора
        </h3>

        <div style={{ marginBottom: '1.5rem' }}>
          <div style={{ fontSize: '0.875rem', color: '#6c757d', marginBottom: '0.5rem' }}>
            Уровень интереса
          </div>
          {getInterestBadge(analytics.analysis?.interest)}
        </div>

        {analytics.analysis?.summary && (
          <div style={{ marginBottom: '1.5rem' }}>
            <div style={{ fontSize: '0.875rem', color: '#6c757d', marginBottom: '0.5rem' }}>
              Краткое резюме
            </div>
            <p style={{ margin: 0, lineHeight: '1.6', color: '#212529' }}>
              {analytics.analysis.summary}
            </p>
          </div>
        )}

        {analytics.analysis?.key_points && analytics.analysis.key_points.length > 0 && (
          <div>
            <div style={{ fontSize: '0.875rem', color: '#6c757d', marginBottom: '0.5rem' }}>
              Ключевые моменты
            </div>
            <ul style={{ margin: 0, paddingLeft: '1.25rem', color: '#212529' }}>
              {analytics.analysis.key_points.map((point, index) => (
                <li key={index} style={{ marginBottom: '0.5rem', lineHeight: '1.6' }}>{point}</li>
              ))}
            </ul>
          </div>
        )}
      </div>

      {/* Follow-up Message */}
      {analytics.followup_message && (
        <div style={{
          marginBottom: '2rem',
          padding: '1.5rem',
          backgroundColor: '#f8f9fa',
          borderRadius: '12px',
          border: '1px solid #e9ecef'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#6c757d', marginBottom: '0.5rem' }}>
            Follow-up сообщение
          </div>
          <p style={{ margin: 0, lineHeight: '1.6', color: '#212529' }}>
            {analytics.followup_message}
          </p>
        </div>
      )}

      {/* Transcript */}
      {analytics.transcript && analytics.transcript.length > 0 && (
        <div style={{
          marginBottom: '2rem',
          padding: '1.5rem',
          backgroundColor: '#f8f9fa',
          borderRadius: '12px',
          border: '1px solid #e9ecef'
        }}>
          <div style={{ fontSize: '0.875rem', color: '#6c757d', marginBottom: '1rem' }}>
            Транскрипт разговора
          </div>
          <div style={{
            maxHeight: '400px',
            overflowY: 'auto',
            marginTop: '0.75rem'
          }}>
            {analytics.transcript.map((message, index) => (
              <div
                key={index}
                style={{
                  marginBottom: '1rem',
                  paddingBottom: '1rem',
                  borderBottom: index < analytics.transcript.length - 1 ? '1px solid #dee2e6' : 'none'
                }}
              >
                <div style={{
                  fontSize: '0.875rem',
                  fontWeight: '600',
                  color: '#495057',
                  marginBottom: '0.25rem'
                }}>
                  {message.role === 'assistant' ? 'Ассистент' : 'Клиент'}
                </div>
                <div style={{ lineHeight: '1.6', color: '#212529' }}>
                  {message.content}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Back Button */}
      <div style={{ textAlign: 'center', marginTop: '2rem' }}>
        <button
          onClick={() => navigate('/')}
          className="btn btn-secondary"
        >
          Вернуться на главную
        </button>
      </div>
    </div>
  )
}

export default DemoAnalytics
