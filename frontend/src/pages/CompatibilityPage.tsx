import { useState } from 'react'
import { motion } from 'framer-motion'
import { Heart, Star, Calendar, Clock, MapPin, Users, TrendingUp, AlertCircle } from 'lucide-react'
import { astrologyApi } from '../services/api'

interface Person {
  name: string
  birthDate: string
  birthTime: string
  birthPlace: string
}

interface CompatibilityResult {
  overall_score: number
  compatibility_level: 'low' | 'medium' | 'high' | 'excellent'
  strengths: string[]
  challenges: string[]
  love_compatibility: number
  friendship_compatibility: number
  business_compatibility: number
  emotional_harmony: number
  communication_style: string
  relationship_advice: string[]
  favorable_periods: string[]
  challenging_periods: string[]
}

export default function CompatibilityPage() {
  const [person1, setPerson1] = useState<Person>({
    name: '',
    birthDate: '',
    birthTime: '',
    birthPlace: ''
  })
  
  const [person2, setPerson2] = useState<Person>({
    name: '',
    birthDate: '',
    birthTime: '',
    birthPlace: ''
  })

  const [result, setResult] = useState<CompatibilityResult | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const compatibilityLevels = {
    low: { color: '#ef4444', label: 'Низкая', description: 'Потребуется много работы над отношениями' },
    medium: { color: '#f59e0b', label: 'Средняя', description: 'Есть потенциал при взаимных усилиях' },
    high: { color: '#10b981', label: 'Высокая', description: 'Отличные перспективы для отношений' },
    excellent: { color: '#8b5cf6', label: 'Превосходная', description: 'Идеальная совместимость' }
  }

  const handlePersonChange = (personNumber: 1 | 2, field: keyof Person, value: string) => {
    if (personNumber === 1) {
      setPerson1(prev => ({ ...prev, [field]: value }))
    } else {
      setPerson2(prev => ({ ...prev, [field]: value }))
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const data = await astrologyApi.getCompatibility(person1, person2)
      setResult(data)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Ошибка анализа совместимости')
      // Mock data for demonstration
      setResult({
        overall_score: 78,
        compatibility_level: 'high',
        strengths: [
          'Прекрасное эмоциональное понимание',
          'Схожие жизненные ценности',
          'Взаимодополняющие качества характера',
          'Хорошая коммуникация'
        ],
        challenges: [
          'Различие в подходах к финансам',
          'Разные темпы принятия решений',
          'Необходимость компромиссов в карьерных вопросах'
        ],
        love_compatibility: 85,
        friendship_compatibility: 72,
        business_compatibility: 68,
        emotional_harmony: 90,
        communication_style: 'Открытый и честный диалог с элементами игривости',
        relationship_advice: [
          'Развивайте общие хобби и интересы',
          'Обсуждайте финансовые планы открыто',
          'Поддерживайте личное пространство друг друга',
          'Регулярно выражайте признательность'
        ],
        favorable_periods: ['Весна 2024', 'Лето 2024', 'Зима 2024-2025'],
        challenging_periods: ['Осень 2024']
      })
    } finally {
      setLoading(false)
    }
  }

  const PersonForm = ({ personNumber, person, title }: { personNumber: 1 | 2, person: Person, title: string }) => (
    <div className="mystical-card p-6">
      <h3 className="text-xl font-mystical text-mystical-gold mb-4 flex items-center space-x-2">
        <Users className="w-5 h-5" />
        <span>{title}</span>
      </h3>
      
      <div className="space-y-4">
        <div>
          <label className="block text-sm font-medium text-mystical-silver mb-2">
            Имя
          </label>
          <input
            type="text"
            required
            className="mystical-input w-full"
            placeholder="Введите имя"
            value={person.name}
            onChange={(e) => handlePersonChange(personNumber, 'name', e.target.value)}
          />
        </div>

        <div>
          <label className="block text-sm font-medium text-mystical-silver mb-2">
            Дата рождения
          </label>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
            <input
              type="date"
              required
              className="mystical-input pl-10 w-full"
              value={person.birthDate}
              onChange={(e) => handlePersonChange(personNumber, 'birthDate', e.target.value)}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-mystical-silver mb-2">
            Время рождения
          </label>
          <div className="relative">
            <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
            <input
              type="time"
              required
              className="mystical-input pl-10 w-full"
              value={person.birthTime}
              onChange={(e) => handlePersonChange(personNumber, 'birthTime', e.target.value)}
            />
          </div>
        </div>

        <div>
          <label className="block text-sm font-medium text-mystical-silver mb-2">
            Место рождения
          </label>
          <div className="relative">
            <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
            <input
              type="text"
              required
              className="mystical-input pl-10 w-full"
              placeholder="Город, страна"
              value={person.birthPlace}
              onChange={(e) => handlePersonChange(personNumber, 'birthPlace', e.target.value)}
            />
          </div>
        </div>
      </div>
    </div>
  )

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <motion.div
          animate={{ 
            scale: [1, 1.1, 1],
            rotate: [0, 5, -5, 0]
          }}
          transition={{ duration: 3, repeat: Infinity, ease: "easeInOut" }}
          className="mx-auto w-16 h-16 bg-gradient-to-r from-pink-500 to-red-500 rounded-full flex items-center justify-center mb-6"
        >
          <Heart className="w-8 h-8 text-white" />
        </motion.div>
        <h1 className="text-4xl font-mystical text-mystical-gold mb-2">
          Анализ совместимости
        </h1>
        <p className="text-mystical-silver/80 max-w-2xl mx-auto">
          Узнайте, насколько вы подходите друг другу по звездам
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-8">
        {error && (
          <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-300 text-center">
            {error}
          </div>
        )}

        {/* Input Forms */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
          >
            <PersonForm personNumber={1} person={person1} title="Первый партнер" />
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.1 }}
          >
            <PersonForm personNumber={2} person={person2} title="Второй партнер" />
          </motion.div>
        </div>

        {/* Submit Button */}
        <div className="text-center">
          <button
            type="submit"
            disabled={loading}
            className="mystical-button text-lg px-12 py-3 flex items-center justify-center space-x-2 mx-auto disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                <Heart className="w-6 h-6" />
              </motion.div>
            ) : (
              <>
                <Heart className="w-6 h-6" />
                <span>Анализировать совместимость</span>
              </>
            )}
          </button>
        </div>
      </form>

      {/* Results */}
      {result && (
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="space-y-8"
        >
          {/* Overall Score */}
          <div className="mystical-card p-8 text-center">
            <div className="flex items-center justify-center space-x-4 mb-6">
              <div className="text-6xl">💕</div>
              <div>
                <h2 className="text-3xl font-mystical text-mystical-gold mb-2">
                  Общая совместимость
                </h2>
                <div className="flex items-center justify-center space-x-4">
                  <div className="text-4xl font-bold text-mystical-gold">
                    {result.overall_score}%
                  </div>
                  <div
                    className="px-4 py-2 rounded-full text-sm font-medium"
                    style={{ 
                      backgroundColor: `${compatibilityLevels[result.compatibility_level].color}20`,
                      color: compatibilityLevels[result.compatibility_level].color
                    }}
                  >
                    {compatibilityLevels[result.compatibility_level].label}
                  </div>
                </div>
                <p className="text-mystical-silver/80 mt-2">
                  {compatibilityLevels[result.compatibility_level].description}
                </p>
              </div>
            </div>

            {/* Score Breakdown */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              {[
                { label: 'Любовь', value: result.love_compatibility, icon: '❤️' },
                { label: 'Дружба', value: result.friendship_compatibility, icon: '🤝' },
                { label: 'Бизнес', value: result.business_compatibility, icon: '💼' },
                { label: 'Эмоции', value: result.emotional_harmony, icon: '🎭' }
              ].map((item) => (
                <div key={item.label} className="bg-dark-300/30 rounded-lg p-4">
                  <div className="text-2xl mb-2">{item.icon}</div>
                  <div className="text-xl font-bold text-mystical-gold">{item.value}%</div>
                  <div className="text-sm text-mystical-silver/80">{item.label}</div>
                </div>
              ))}
            </div>
          </div>

          {/* Strengths & Challenges */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="mystical-card p-6"
            >
              <div className="flex items-center space-x-2 mb-4">
                <Star className="w-5 h-5 text-green-400" />
                <h3 className="text-xl font-mystical text-mystical-gold">
                  Сильные стороны
                </h3>
              </div>
              <ul className="space-y-2">
                {result.strengths.map((strength, index) => (
                  <li key={index} className="flex items-start space-x-2 text-mystical-silver/80">
                    <div className="w-2 h-2 rounded-full bg-green-400 mt-2 flex-shrink-0" />
                    <span>{strength}</span>
                  </li>
                ))}
              </ul>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="mystical-card p-6"
            >
              <div className="flex items-center space-x-2 mb-4">
                <AlertCircle className="w-5 h-5 text-yellow-400" />
                <h3 className="text-xl font-mystical text-mystical-gold">
                  Вызовы
                </h3>
              </div>
              <ul className="space-y-2">
                {result.challenges.map((challenge, index) => (
                  <li key={index} className="flex items-start space-x-2 text-mystical-silver/80">
                    <div className="w-2 h-2 rounded-full bg-yellow-400 mt-2 flex-shrink-0" />
                    <span>{challenge}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          </div>

          {/* Communication & Advice */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="mystical-card p-6"
            >
              <div className="flex items-center space-x-2 mb-4">
                <TrendingUp className="w-5 h-5 text-mystical-gold" />
                <h3 className="text-xl font-mystical text-mystical-gold">
                  Стиль общения
                </h3>
              </div>
              <p className="text-mystical-silver/80 leading-relaxed">
                {result.communication_style}
              </p>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="mystical-card p-6"
            >
              <div className="flex items-center space-x-2 mb-4">
                <Heart className="w-5 h-5 text-pink-400" />
                <h3 className="text-xl font-mystical text-mystical-gold">
                  Советы для отношений
                </h3>
              </div>
              <ul className="space-y-2">
                {result.relationship_advice.map((advice, index) => (
                  <li key={index} className="flex items-start space-x-2 text-mystical-silver/80 text-sm">
                    <Heart className="w-3 h-3 text-pink-400 mt-1 flex-shrink-0" />
                    <span>{advice}</span>
                  </li>
                ))}
              </ul>
            </motion.div>
          </div>

          {/* Timing */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="mystical-card p-6"
            >
              <h3 className="text-xl font-mystical text-mystical-gold mb-4">
                Благоприятные периоды
              </h3>
              <div className="space-y-2">
                {result.favorable_periods.map((period, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-green-400" />
                    <span className="text-mystical-silver/80">{period}</span>
                  </div>
                ))}
              </div>
            </motion.div>

            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.7 }}
              className="mystical-card p-6"
            >
              <h3 className="text-xl font-mystical text-mystical-gold mb-4">
                Сложные периоды
              </h3>
              <div className="space-y-2">
                {result.challenging_periods.map((period, index) => (
                  <div key={index} className="flex items-center space-x-2">
                    <div className="w-3 h-3 rounded-full bg-yellow-400" />
                    <span className="text-mystical-silver/80">{period}</span>
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </motion.div>
      )}
    </div>
  )
}