import { useState, useEffect } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { demoAPI } from '../api/client'

function StatusDemo() {
  const { sessionId } = useParams()
  const navigate = useNavigate()
  const [status, setStatus] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const data = await demoAPI.getDemoSessionStatus(sessionId)
        setStatus(data)

        // If all stages are completed, wait a bit then redirect to analytics
        if (data.call_status === 'completed' && data.crm_status === 'added') {
          setTimeout(() => {
            navigate(`/analytics/${sessionId}`)
          }, 2000)
        }
      } catch (err) {
        setError(err.response?.data?.detail || 'Ошибка при загрузке статуса')
      } finally {
        setLoading(false)
      }
    }

    fetchStatus()

    // Poll every 2 seconds
    const interval = setInterval(fetchStatus, 2000)

    return () => clearInterval(interval)
  }, [sessionId, navigate])

  const getStatusIcon = (statusValue) => {
    if (statusValue === 'done' || statusValue === 'sent' || statusValue === 'added' || statusValue === 'completed') {
      return '✓'
    } else if (statusValue === 'in_progress' || statusValue === 'sending' || statusValue === 'adding') {
      return <span className="spinner"></span>
    } else if (statusValue === 'failed') {
      return '✗'
    } else {
      return '○'
    }
  }

  const getStatusClass = (statusValue) => {
    if (statusValue === 'done' || statusValue === 'sent' || statusValue === 'added' || statusValue === 'completed') {
      return 'completed'
    } else if (statusValue === 'in_progress' || statusValue === 'sending' || statusValue === 'adding') {
      return 'active'
    } else {
      return ''
    }
  }

  const getStatusText = (key, value) => {
    const texts = {
      call_status: {
        pending: 'Выполняем звонок...',
        in_progress: 'Идет разговор...',
        completed: 'Звонок завершен',
        failed: 'Ошибка звонка'
      },
      analysis_status: {
        pending: 'Ожидание анализа...',
        in_progress: 'Анализируем разговор...',
        done: 'Анализ завершен'
      },
      followup_status: {
        pending: 'Ожидание генерации...',
        in_progress: 'Готовим follow-up...',
        done: 'Follow-up готов'
      },
      sms_status: {
        pending: 'Ожидание отправки...',
        sending: 'Отправляем SMS...',
        sent: 'SMS отправлено'
      },
      crm_status: {
        pending: 'Ожидание добавления...',
        adding: 'Добавляем в CRM...',
        added: 'Добавлено в CRM'
      }
    }

    return texts[key]?.[value] || value
  }

  if (loading) {
    return (
      <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
        <span className="spinner" style={{ width: '40px', height: '40px', borderWidth: '4px' }}></span>
        <p style={{ marginTop: '1rem', color: '#666' }}>Загрузка статуса...</p>
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
      <h2 className="card-title">Статус демо</h2>

      <div style={{ marginBottom: '2rem' }}>
        <div className={`status-indicator ${getStatusClass(status.call_status)}`}>
          <div className="status-icon">{getStatusIcon(status.call_status)}</div>
          <div>
            <strong>{getStatusText('call_status', status.call_status)}</strong>
          </div>
        </div>

        <div className={`status-indicator ${getStatusClass(status.analysis_status)}`}>
          <div className="status-icon">{getStatusIcon(status.analysis_status)}</div>
          <div>
            <strong>{getStatusText('analysis_status', status.analysis_status)}</strong>
          </div>
        </div>

        <div className={`status-indicator ${getStatusClass(status.followup_status)}`}>
          <div className="status-icon">{getStatusIcon(status.followup_status)}</div>
          <div>
            <strong>{getStatusText('followup_status', status.followup_status)}</strong>
          </div>
        </div>

        <div className={`status-indicator ${getStatusClass(status.sms_status)}`}>
          <div className="status-icon">{getStatusIcon(status.sms_status)}</div>
          <div>
            <strong>{getStatusText('sms_status', status.sms_status)}</strong>
          </div>
        </div>

        <div className={`status-indicator ${getStatusClass(status.crm_status)}`}>
          <div className="status-icon">{getStatusIcon(status.crm_status)}</div>
          <div>
            <strong>{getStatusText('crm_status', status.crm_status)}</strong>
          </div>
        </div>
      </div>

      {status.call_status === 'completed' && status.crm_status === 'added' && (
        <div className="alert alert-success" style={{ textAlign: 'center' }}>
          <h3 style={{ marginBottom: '0.5rem' }}>Демо завершено успешно!</h3>
          <p style={{ marginBottom: '1rem' }}>
            Перенаправляем на страницу аналитики...
          </p>
          <button
            onClick={() => navigate(`/analytics/${sessionId}`)}
            className="btn btn-primary"
          >
            Перейти к аналитике
          </button>
        </div>
      )}
    </div>
  )
}

export default StatusDemo
