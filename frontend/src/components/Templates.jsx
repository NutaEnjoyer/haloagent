import { useState } from 'react'
import { useNavigate } from 'react-router-dom'

function Templates() {
  const navigate = useNavigate()
  const [templates, setTemplates] = useState([
    {
      id: 1,
      name: 'Стандартный оператор',
      category: 'sales',
      prompt: 'Вы - вежливый оператор call-центра HALO. Ваша задача: представить продукт, узнать интерес клиента и предложить следующие шаги.',
      language: 'auto',
      voice: 'female'
    },
    {
      id: 2,
      name: 'Агрессивные продажи',
      category: 'sales',
      prompt: 'Вы - активный менеджер по продажам. Ваша цель - максимально заинтересовать клиента и закрыть сделку. Будьте настойчивы, но вежливы.',
      language: 'ru',
      voice: 'male'
    },
    {
      id: 3,
      name: 'Техподдержка',
      category: 'support',
      prompt: 'Вы - сотрудник технической поддержки. Помогите клиенту решить его проблему, задавайте уточняющие вопросы и предлагайте решения.',
      language: 'auto',
      voice: 'neutral'
    },
    {
      id: 4,
      name: 'Опрос клиентов',
      category: 'survey',
      prompt: 'Вы проводите опрос удовлетворенности клиентов. Задайте 3-5 вопросов о качестве обслуживания и запишите ответы.',
      language: 'ru',
      voice: 'female'
    }
  ])

  const [selectedTemplate, setSelectedTemplate] = useState(null)
  const [isEditing, setIsEditing] = useState(false)
  const [isCreating, setIsCreating] = useState(false)

  const [formData, setFormData] = useState({
    name: '',
    category: 'sales',
    prompt: '',
    language: 'auto',
    voice: 'female'
  })

  const handleEdit = (template) => {
    setSelectedTemplate(template)
    setFormData(template)
    setIsEditing(true)
  }

  const handleCreate = () => {
    setFormData({
      name: '',
      category: 'sales',
      prompt: '',
      language: 'auto',
      voice: 'female'
    })
    setIsCreating(true)
  }

  const handleSave = () => {
    if (isCreating) {
      setTemplates([...templates, { ...formData, id: Date.now() }])
      setIsCreating(false)
    } else {
      setTemplates(templates.map(t => t.id === selectedTemplate.id ? formData : t))
      setIsEditing(false)
    }
    setSelectedTemplate(null)
  }

  const handleDelete = (id) => {
    if (confirm('Удалить этот шаблон?')) {
      setTemplates(templates.filter(t => t.id !== id))
    }
  }

  const handleUseTemplate = (template) => {
    // Store template in localStorage for LaunchDemo
    localStorage.setItem('selectedTemplate', JSON.stringify(template))
    navigate('/launch')
  }

  const handleChange = (e) => {
    const { name, value } = e.target
    setFormData(prev => ({ ...prev, [name]: value }))
  }

  const getCategoryBadge = (category) => {
    const categories = {
      sales: { label: 'Продажи', color: 'rgba(99, 102, 241, 0.15)', border: 'rgba(99, 102, 241, 0.3)', text: '#60a5fa' },
      support: { label: 'Поддержка', color: 'rgba(16, 185, 129, 0.15)', border: 'rgba(16, 185, 129, 0.3)', text: '#34d399' },
      survey: { label: 'Опрос', color: 'rgba(168, 85, 247, 0.15)', border: 'rgba(168, 85, 247, 0.3)', text: '#a855f7' }
    }
    const cat = categories[category] || categories.sales
    return (
      <span style={{
        padding: '0.4rem 0.8rem',
        borderRadius: '12px',
        fontSize: '0.75rem',
        fontWeight: '700',
        letterSpacing: '0.5px',
        textTransform: 'uppercase',
        background: cat.color,
        color: cat.text,
        border: `1px solid ${cat.border}`
      }}>
        {cat.label}
      </span>
    )
  }

  if (isEditing || isCreating) {
    return (
      <div className="card">
        <h2 className="card-title">{isCreating ? 'Создать шаблон' : 'Редактировать шаблон'}</h2>

        <div className="form-group">
          <label className="form-label">Название шаблона</label>
          <input
            type="text"
            name="name"
            className="form-input"
            value={formData.name}
            onChange={handleChange}
            placeholder="Название шаблона"
          />
        </div>

        <div className="form-group">
          <label className="form-label">Категория</label>
          <select
            name="category"
            className="form-select"
            value={formData.category}
            onChange={handleChange}
          >
            <option value="sales">Продажи</option>
            <option value="support">Поддержка</option>
            <option value="survey">Опрос</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Промпт</label>
          <textarea
            name="prompt"
            className="form-textarea"
            value={formData.prompt}
            onChange={handleChange}
            placeholder="Опишите роль и задачу ассистента"
            style={{ minHeight: '200px' }}
          />
        </div>

        <div className="form-group">
          <label className="form-label">Язык</label>
          <select
            name="language"
            className="form-select"
            value={formData.language}
            onChange={handleChange}
          >
            <option value="auto">Auto (определить автоматически)</option>
            <option value="ru">Русский (RU)</option>
            <option value="en">Английский (EN)</option>
            <option value="uz">Узбекский (UZ)</option>
          </select>
        </div>

        <div className="form-group">
          <label className="form-label">Голос</label>
          <select
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

        <div style={{ display: 'flex', gap: '1rem', marginTop: '2rem' }}>
          <button
            onClick={handleSave}
            className="btn btn-primary"
            disabled={!formData.name || !formData.prompt}
          >
            Сохранить
          </button>
          <button
            onClick={() => {
              setIsEditing(false)
              setIsCreating(false)
              setSelectedTemplate(null)
            }}
            className="btn btn-secondary"
          >
            Отмена
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="card">
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '2rem' }}>
        <h2 className="card-title" style={{ marginBottom: 0 }}>Шаблоны промптов</h2>
        <button
          onClick={handleCreate}
          className="btn btn-primary"
        >
          + Создать шаблон
        </button>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
        gap: '1.5rem'
      }}>
        {templates.map(template => (
          <div
            key={template.id}
            style={{
              padding: '1.5rem',
              background: 'rgba(255, 255, 255, 0.03)',
              borderRadius: '16px',
              border: '1px solid var(--border-primary)',
              transition: 'all 0.3s ease'
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.transform = 'translateY(-5px)'
              e.currentTarget.style.boxShadow = 'var(--shadow-lg)'
              e.currentTarget.style.borderColor = 'var(--border-accent)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.transform = 'translateY(0)'
              e.currentTarget.style.boxShadow = 'none'
              e.currentTarget.style.borderColor = 'var(--border-primary)'
            }}
          >
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start', marginBottom: '1rem' }}>
              <h3 style={{ color: 'var(--text-primary)', fontSize: '1.2rem', fontWeight: '700' }}>
                {template.name}
              </h3>
              {getCategoryBadge(template.category)}
            </div>

            <p style={{
              color: 'var(--text-secondary)',
              fontSize: '0.95rem',
              lineHeight: '1.6',
              marginBottom: '1rem',
              maxHeight: '80px',
              overflow: 'hidden',
              textOverflow: 'ellipsis'
            }}>
              {template.prompt}
            </p>

            <div style={{
              display: 'flex',
              gap: '0.5rem',
              marginBottom: '1rem',
              flexWrap: 'wrap'
            }}>
              <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.05)' }}>
                {template.language === 'auto' ? 'Auto' : template.language.toUpperCase()}
              </span>
              <span className="badge" style={{ background: 'rgba(255, 255, 255, 0.05)' }}>
                {template.voice === 'male' ? '🎙️ Мужской' : template.voice === 'female' ? '🎤 Женский' : '🔊 Нейтральный'}
              </span>
            </div>

            <div style={{ display: 'flex', gap: '0.5rem' }}>
              <button
                onClick={() => handleUseTemplate(template)}
                className="btn btn-primary"
                style={{ flex: 1, padding: '0.75rem', fontSize: '0.9rem' }}
              >
                Использовать
              </button>
              <button
                onClick={() => handleEdit(template)}
                className="btn btn-secondary"
                style={{ padding: '0.75rem 1rem', fontSize: '0.9rem' }}
              >
                ✏️
              </button>
              <button
                onClick={() => handleDelete(template.id)}
                className="btn btn-secondary"
                style={{
                  padding: '0.75rem 1rem',
                  fontSize: '0.9rem',
                  background: 'rgba(239, 68, 68, 0.1)',
                  borderColor: 'rgba(239, 68, 68, 0.3)'
                }}
              >
                🗑️
              </button>
            </div>
          </div>
        ))}
      </div>

      {templates.length === 0 && (
        <div style={{ textAlign: 'center', padding: '3rem' }}>
          <p style={{ color: 'var(--text-muted)', fontSize: '1.1rem', marginBottom: '1.5rem' }}>
            Нет доступных шаблонов
          </p>
          <button
            onClick={handleCreate}
            className="btn btn-primary"
          >
            Создать первый шаблон
          </button>
        </div>
      )}
    </div>
  )
}

export default Templates
