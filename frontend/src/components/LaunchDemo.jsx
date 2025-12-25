import { useState, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import { demoAPI } from '../api/client'

function LaunchDemo() {
  const navigate = useNavigate()
  const [formData, setFormData] = useState({
    phone: '',
    language: 'auto',
    voice: 'female',
    greeting: 'Здравствуйте! Я голосовой ассистент HALO. Чем могу помочь?',
    prompt: 'Ты — живой человек, который позвонил по делу. Не оператор колл-центра, не робот. Ты ведёшь нормальный разговор, реагируешь на собеседника, говоришь коротко и по делу. Если человек говорит просто — ты отвечаешь просто. Используй живую разговорную речь. Не спорь, не давишь, разговариваешь на равных.'
  })
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const isSubmitting = useRef(false)

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({
      ...prev,
      [name]: value
    }))
  }

  const handleSubmit = async (e) => {
    e.preventDefault()

    // Prevent double submission
    if (isSubmitting.current) {
      console.log('Submission already in progress, ignoring duplicate')
      return
    }

    isSubmitting.current = true
    setError('')
    setLoading(true)

    try {
      console.log('Creating demo session...')
      const response = await demoAPI.createDemoSession(
        formData.phone,
        formData.language,
        formData.voice,
        formData.greeting,
        formData.prompt
      )

      console.log('Demo session created:', response.demo_session_id)

      // Navigate to status page
      navigate(`/status/${response.demo_session_id}`)
    } catch (err) {
      setError(err.response?.data?.detail || 'Ошибка при создании демо-сессии')
      isSubmitting.current = false // Reset on error
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="card">
      <h2 className="card-title">Запустить демо HALO</h2>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label className="form-label" htmlFor="phone">
            Номер телефона
          </label>
          <input
            type="tel"
            id="phone"
            name="phone"
            className="form-input"
            placeholder="+79991234567"
            value={formData.phone}
            onChange={handleChange}
            required
          />
          <small className="form-hint">
            Формат: +7XXXXXXXXXX
          </small>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="language">
            Язык ассистента
          </label>
          <select
            id="language"
            name="language"
            className="form-select"
            value={formData.language}
            onChange={handleChange}
          >
            <option value="auto">Auto (определить автоматически)</option>
            <option value="ru">Русский (RU)</option>
            <option value="uz">Узбекский (UZ)</option>
            <option value="tj">Таджикский (TJ)</option>
            <option value="kk">Казахский (KK)</option>
            <option value="ky">Киргизский (KY)</option>
            <option value="tm">Туркменский (TM)</option>
            <option value="az">Азербайджанский (AZ)</option>
            <option value="fa-af">Дари / Афганский (FA-AF)</option>
            <option value="en">Английский (EN)</option>
            <option value="tr">Турецкий (TR)</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="voice">
            Голос ассистента
          </label>
          <select
            id="voice"
            name="voice"
            className="form-select"
            value={formData.voice}
            onChange={handleChange}
          >
            <option value="male">Мужской</option>
            <option value="female">Женский</option>
            <option value="neutral">Нейтральный</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="greeting">
            Приветствие ассистента
          </label>
          <textarea
            id="greeting"
            name="greeting"
            className="form-textarea"
            value={formData.greeting}
            onChange={handleChange}
            rows="2"
            required
          />
          <small className="form-hint">
            Первая фраза, которую скажет ассистент при ответе
          </small>
        </div>

        <div className="form-group">
          <label className="form-label" htmlFor="prompt">
            Промпт ассистента
          </label>
          <textarea
            id="prompt"
            name="prompt"
            className="form-textarea"
            value={formData.prompt}
            onChange={handleChange}
            required
          />
          <small className="form-hint">
            Опишите роль и задачу ассистента
          </small>
        </div>

        {error && (
          <div className="alert alert-error">
            {error}
          </div>
        )}

        <button
          type="submit"
          className="btn btn-primary"
          disabled={loading}
          style={{ width: '100%' }}
        >
          {loading ? (
            <>
              <span className="spinner" style={{ marginRight: '0.5rem' }}></span>
              Запускаем демо...
            </>
          ) : (
            'Запустить демо'
          )}
        </button>
      </form>

      <div className="info-box">
        <h3>Что произойдет?</h3>
        <ol>
          <li>HALO выполнит реальный звонок на указанный номер</li>
          <li>При ответе ассистент поведет диалог согласно промпту</li>
          <li>После звонка система проанализирует разговор</li>
          <li>Вам придет SMS со ссылкой в Telegram</li>
          <li>Будет создана CRM-карточка и follow-up сообщение</li>
          <li>Вы увидите аналитику и демо-данные в кабинете</li>
        </ol>
      </div>
    </div>
  )
}

export default LaunchDemo
