import { useState } from 'react'

function Settings() {
  const [settings, setSettings] = useState({
    // API Settings
    apiUrl: 'http://localhost:8000',
    apiKey: '',

    // Default Call Settings
    defaultLanguage: 'auto',
    defaultVoice: 'shimmer',
    callTimeout: 120,

    // Notifications
    enableNotifications: true,
    emailNotifications: false,
    email: '',

    // Advanced
    autoRetry: true,
    maxRetries: 3,
    debugMode: false
  })

  const [saved, setSaved] = useState(false)

  const handleChange = (e) => {
    const { name, value, type, checked } = e.target
    setSettings(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }))
    setSaved(false)
  }

  const handleSave = () => {
    // Save to localStorage
    localStorage.setItem('haloSettings', JSON.stringify(settings))
    setSaved(true)
    setTimeout(() => setSaved(false), 3000)
  }

  const handleReset = () => {
    if (confirm('Сбросить все настройки?')) {
      localStorage.removeItem('haloSettings')
      setSettings({
        apiUrl: 'http://localhost:8000',
        apiKey: '',
        defaultLanguage: 'auto',
        defaultVoice: 'shimmer',
        callTimeout: 120,
        enableNotifications: true,
        emailNotifications: false,
        email: '',
        autoRetry: true,
        maxRetries: 3,
        debugMode: false
      })
    }
  }

  return (
    <>
      <div className="card">
        <h2 className="card-title">Настройки системы</h2>

        {saved && (
          <div className="alert alert-success" style={{ marginBottom: '2rem' }}>
            ✓ Настройки успешно сохранены
          </div>
        )}

        {/* API Settings */}
        <div style={{
          marginBottom: '3rem',
          padding: '2rem',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '16px',
          border: '1px solid var(--border-primary)'
        }}>
          <h3 style={{
            color: 'var(--accent-purple)',
            fontSize: '1.5rem',
            marginBottom: '1.5rem',
            fontWeight: '700'
          }}>
            API Configuration
          </h3>

          <div className="form-group">
            <label className="form-label">API URL</label>
            <input
              type="text"
              name="apiUrl"
              className="form-input"
              value={settings.apiUrl}
              onChange={handleChange}
              placeholder="http://localhost:8000"
            />
            <small className="form-hint">
              Адрес backend API
            </small>
          </div>

          <div className="form-group">
            <label className="form-label">API Key (опционально)</label>
            <input
              type="password"
              name="apiKey"
              className="form-input"
              value={settings.apiKey}
              onChange={handleChange}
              placeholder="Введите API ключ"
            />
            <small className="form-hint">
              Оставьте пустым если не требуется
            </small>
          </div>
        </div>

        {/* Default Call Settings */}
        <div style={{
          marginBottom: '3rem',
          padding: '2rem',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '16px',
          border: '1px solid var(--border-primary)'
        }}>
          <h3 style={{
            color: 'var(--accent-purple)',
            fontSize: '1.5rem',
            marginBottom: '1.5rem',
            fontWeight: '700'
          }}>
            Настройки звонков по умолчанию
          </h3>

          <div className="form-group">
            <label className="form-label">Язык по умолчанию</label>
            <select
              name="defaultLanguage"
              className="form-select"
              value={settings.defaultLanguage}
              onChange={handleChange}
            >
              <option value="auto">Auto (определить автоматически)</option>
              <option value="ru">Русский (RU)</option>
              <option value="en">Английский (EN)</option>
              <option value="uz">Узбекский (UZ)</option>
              <option value="kk">Казахский (KK)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Голос по умолчанию</label>
            <select
              name="defaultVoice"
              className="form-select"
              value={settings.defaultVoice}
              onChange={handleChange}
            >
              <option value="alloy">Alloy (нейтральный)</option>
              <option value="echo">Echo (мужской)</option>
              <option value="fable">Fable (британский мужской)</option>
              <option value="onyx">Onyx (глубокий мужской)</option>
              <option value="nova">Nova (женский)</option>
              <option value="shimmer">Shimmer (мягкий женский)</option>
            </select>
          </div>

          <div className="form-group">
            <label className="form-label">Таймаут звонка (секунды)</label>
            <input
              type="number"
              name="callTimeout"
              className="form-input"
              value={settings.callTimeout}
              onChange={handleChange}
              min="30"
              max="300"
            />
            <small className="form-hint">
              Максимальная длительность звонка (30-300 секунд)
            </small>
          </div>
        </div>

        {/* Notifications */}
        <div style={{
          marginBottom: '3rem',
          padding: '2rem',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '16px',
          border: '1px solid var(--border-primary)'
        }}>
          <h3 style={{
            color: 'var(--accent-purple)',
            fontSize: '1.5rem',
            marginBottom: '1.5rem',
            fontWeight: '700'
          }}>
            Уведомления
          </h3>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="enableNotifications"
                checked={settings.enableNotifications}
                onChange={handleChange}
                style={{
                  width: '20px',
                  height: '20px',
                  cursor: 'pointer',
                  accentColor: 'var(--accent-purple)'
                }}
              />
              <span style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}>
                Включить браузерные уведомления
              </span>
            </label>
          </div>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="emailNotifications"
                checked={settings.emailNotifications}
                onChange={handleChange}
                style={{
                  width: '20px',
                  height: '20px',
                  cursor: 'pointer',
                  accentColor: 'var(--accent-purple)'
                }}
              />
              <span style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}>
                Email уведомления
              </span>
            </label>
          </div>

          {settings.emailNotifications && (
            <div className="form-group">
              <label className="form-label">Email адрес</label>
              <input
                type="email"
                name="email"
                className="form-input"
                value={settings.email}
                onChange={handleChange}
                placeholder="your@email.com"
              />
            </div>
          )}
        </div>

        {/* Advanced Settings */}
        <div style={{
          marginBottom: '2rem',
          padding: '2rem',
          background: 'rgba(255, 255, 255, 0.02)',
          borderRadius: '16px',
          border: '1px solid var(--border-primary)'
        }}>
          <h3 style={{
            color: 'var(--accent-purple)',
            fontSize: '1.5rem',
            marginBottom: '1.5rem',
            fontWeight: '700'
          }}>
            Расширенные настройки
          </h3>

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="autoRetry"
                checked={settings.autoRetry}
                onChange={handleChange}
                style={{
                  width: '20px',
                  height: '20px',
                  cursor: 'pointer',
                  accentColor: 'var(--accent-purple)'
                }}
              />
              <span style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}>
                Автоматический повтор при ошибке
              </span>
            </label>
          </div>

          {settings.autoRetry && (
            <div className="form-group">
              <label className="form-label">Максимум попыток</label>
              <input
                type="number"
                name="maxRetries"
                className="form-input"
                value={settings.maxRetries}
                onChange={handleChange}
                min="1"
                max="10"
              />
            </div>
          )}

          <div className="form-group">
            <label style={{ display: 'flex', alignItems: 'center', gap: '1rem', cursor: 'pointer' }}>
              <input
                type="checkbox"
                name="debugMode"
                checked={settings.debugMode}
                onChange={handleChange}
                style={{
                  width: '20px',
                  height: '20px',
                  cursor: 'pointer',
                  accentColor: 'var(--accent-purple)'
                }}
              />
              <span style={{ color: 'var(--text-secondary)', fontSize: '1rem' }}>
                Режим отладки (Debug Mode)
              </span>
            </label>
            <small className="form-hint">
              Включает детальное логирование в консоль браузера
            </small>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center' }}>
          <button
            onClick={handleSave}
            className="btn btn-primary"
            style={{ minWidth: '200px' }}
          >
            Сохранить настройки
          </button>
          <button
            onClick={handleReset}
            className="btn btn-secondary"
            style={{ minWidth: '200px' }}
          >
            Сбросить
          </button>
        </div>
      </div>

      {/* System Info */}
      <div className="card">
        <h2 className="card-title">Информация о системе</h2>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
          gap: '1.5rem'
        }}>
          <div style={{
            padding: '1.5rem',
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: '12px',
            border: '1px solid var(--border-primary)'
          }}>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>Версия</p>
            <p style={{ color: 'var(--text-primary)', fontSize: '1.2rem', fontWeight: '700' }}>1.0.0</p>
          </div>

          <div style={{
            padding: '1.5rem',
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: '12px',
            border: '1px solid var(--border-primary)'
          }}>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>Backend API</p>
            <p style={{ color: 'var(--text-primary)', fontSize: '1.2rem', fontWeight: '700' }}>
              {settings.apiUrl}
            </p>
          </div>

          <div style={{
            padding: '1.5rem',
            background: 'rgba(255, 255, 255, 0.03)',
            borderRadius: '12px',
            border: '1px solid var(--border-primary)'
          }}>
            <p style={{ color: 'var(--text-muted)', fontSize: '0.85rem', marginBottom: '0.5rem' }}>Статус</p>
            <p style={{ color: '#34d399', fontSize: '1.2rem', fontWeight: '700' }}>● Online</p>
          </div>
        </div>
      </div>
    </>
  )
}

export default Settings
