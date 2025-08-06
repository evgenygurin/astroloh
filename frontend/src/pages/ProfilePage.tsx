import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { User, Mail, Calendar, Clock, MapPin, Edit2, Save, X } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

export default function ProfilePage() {
  const { user } = useAuth()
  const [isEditing, setIsEditing] = useState(false)
  const [formData, setFormData] = useState({
    name: user?.name || '',
    email: user?.email || '',
    birthDate: user?.birthDate || '',
    birthTime: user?.birthTime || '',
    birthPlace: user?.birthPlace || ''
  })

  useEffect(() => {
    if (user) {
      setFormData({
        name: user.name || '',
        email: user.email || '',
        birthDate: user.birthDate || '',
        birthTime: user.birthTime || '',
        birthPlace: user.birthPlace || ''
      })
    }
  }, [user])

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleSave = async () => {
    // TODO: Implement API call to update user data
    console.log('Saving user data:', formData)
    setIsEditing(false)
  }

  const handleCancel = () => {
    if (user) {
      setFormData({
        name: user.name || '',
        email: user.email || '',
        birthDate: user.birthDate || '',
        birthTime: user.birthTime || '',
        birthPlace: user.birthPlace || ''
      })
    }
    setIsEditing(false)
  }

  if (!user) {
    return (
      <div className="text-center py-20">
        <p className="text-mystical-silver/80">Загрузка профиля...</p>
      </div>
    )
  }

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="mx-auto w-20 h-20 bg-gradient-to-r from-mystical-gold to-primary-600 rounded-full flex items-center justify-center mb-6"
        >
          <User className="w-10 h-10 text-dark-900" />
        </motion.div>
        <h1 className="text-4xl font-mystical text-mystical-gold mb-2">
          Личный кабинет
        </h1>
        <p className="text-mystical-silver/80">
          Управляйте своим астрологическим профилем
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Profile Information */}
        <div className="lg:col-span-2">
          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.6 }}
            className="mystical-card p-8"
          >
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-mystical text-mystical-gold">
                Основная информация
              </h2>
              <div className="flex space-x-2">
                {isEditing ? (
                  <>
                    <button
                      onClick={handleSave}
                      className="flex items-center space-x-2 bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg transition-colors"
                    >
                      <Save className="w-4 h-4" />
                      <span>Сохранить</span>
                    </button>
                    <button
                      onClick={handleCancel}
                      className="flex items-center space-x-2 bg-gray-600 hover:bg-gray-700 text-white px-4 py-2 rounded-lg transition-colors"
                    >
                      <X className="w-4 h-4" />
                      <span>Отменить</span>
                    </button>
                  </>
                ) : (
                  <button
                    onClick={() => setIsEditing(true)}
                    className="flex items-center space-x-2 text-mystical-gold hover:text-primary-400 transition-colors"
                  >
                    <Edit2 className="w-4 h-4" />
                    <span>Редактировать</span>
                  </button>
                )}
              </div>
            </div>

            <div className="space-y-6">
              {/* Personal Data */}
              <div>
                <label className="block text-sm font-medium text-mystical-silver mb-2">
                  Полное имя
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
                  <input
                    name="name"
                    type="text"
                    disabled={!isEditing}
                    className={`mystical-input pl-10 w-full ${!isEditing ? 'opacity-70 cursor-not-allowed' : ''}`}
                    value={formData.name}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-mystical-silver mb-2">
                  Email
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
                  <input
                    name="email"
                    type="email"
                    disabled={!isEditing}
                    className={`mystical-input pl-10 w-full ${!isEditing ? 'opacity-70 cursor-not-allowed' : ''}`}
                    value={formData.email}
                    onChange={handleChange}
                  />
                </div>
              </div>

              {/* Birth Data */}
              <div className="border-t border-mystical-gold/20 pt-6">
                <h3 className="text-lg font-mystical text-mystical-gold mb-4">
                  Астрологические данные
                </h3>
                
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-mystical-silver mb-2">
                      Дата рождения
                    </label>
                    <div className="relative">
                      <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
                      <input
                        name="birthDate"
                        type="date"
                        disabled={!isEditing}
                        className={`mystical-input pl-10 w-full ${!isEditing ? 'opacity-70 cursor-not-allowed' : ''}`}
                        value={formData.birthDate}
                        onChange={handleChange}
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
                        name="birthTime"
                        type="time"
                        disabled={!isEditing}
                        className={`mystical-input pl-10 w-full ${!isEditing ? 'opacity-70 cursor-not-allowed' : ''}`}
                        value={formData.birthTime}
                        onChange={handleChange}
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
                        name="birthPlace"
                        type="text"
                        disabled={!isEditing}
                        className={`mystical-input pl-10 w-full ${!isEditing ? 'opacity-70 cursor-not-allowed' : ''}`}
                        placeholder="Город, страна"
                        value={formData.birthPlace}
                        onChange={handleChange}
                      />
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </motion.div>
        </div>

        {/* Quick Actions */}
        <div className="space-y-6">
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mystical-card p-6"
          >
            <h3 className="text-xl font-mystical text-mystical-gold mb-4">
              Быстрые действия
            </h3>
            <div className="space-y-3">
              <button className="w-full text-left p-3 rounded-lg bg-dark-300/50 hover:bg-dark-300/70 text-mystical-silver hover:text-mystical-gold transition-all duration-200">
                Построить натальную карту
              </button>
              <button className="w-full text-left p-3 rounded-lg bg-dark-300/50 hover:bg-dark-300/70 text-mystical-silver hover:text-mystical-gold transition-all duration-200">
                Получить гороскоп
              </button>
              <button className="w-full text-left p-3 rounded-lg bg-dark-300/50 hover:bg-dark-300/70 text-mystical-silver hover:text-mystical-gold transition-all duration-200">
                Анализ совместимости
              </button>
              <button className="w-full text-left p-3 rounded-lg bg-dark-300/50 hover:bg-dark-300/70 text-mystical-silver hover:text-mystical-gold transition-all duration-200">
                Лунный календарь
              </button>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.4 }}
            className="mystical-card p-6"
          >
            <h3 className="text-xl font-mystical text-mystical-gold mb-4">
              История консультаций
            </h3>
            <p className="text-mystical-silver/80 text-sm mb-4">
              Ваши последние астрологические сессии
            </p>
            <div className="space-y-2">
              <div className="text-sm text-mystical-silver/60">
                Пока нет сохраненных консультаций
              </div>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.6 }}
            className="mystical-card p-6"
          >
            <h3 className="text-xl font-mystical text-mystical-gold mb-4">
              Статистика
            </h3>
            <div className="space-y-3">
              <div className="flex justify-between">
                <span className="text-mystical-silver/80">Консультаций:</span>
                <span className="text-mystical-gold">0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-mystical-silver/80">Натальных карт:</span>
                <span className="text-mystical-gold">0</span>
              </div>
              <div className="flex justify-between">
                <span className="text-mystical-silver/80">Анализов:</span>
                <span className="text-mystical-gold">0</span>
              </div>
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}