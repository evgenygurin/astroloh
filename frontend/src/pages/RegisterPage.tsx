import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { Eye, EyeOff, Mail, Lock, User, Star, Calendar, MapPin, Clock } from 'lucide-react'
import { useAuth } from '../contexts/AuthContext'

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    name: '',
    email: '',
    password: '',
    confirmPassword: '',
    birthDate: '',
    birthTime: '',
    birthPlace: ''
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const { register } = useAuth()
  const navigate = useNavigate()

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')

    if (formData.password !== formData.confirmPassword) {
      setError('Пароли не совпадают')
      return
    }

    if (formData.password.length < 8) {
      setError('Пароль должен содержать минимум 8 символов')
      return
    }

    setLoading(true)

    try {
      await register(formData.email, formData.password, formData.name)
      navigate('/')
    } catch (err: any) {
      setError(err.response?.data?.message || 'Ошибка регистрации')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-[80vh] flex items-center justify-center py-12">
      <motion.div
        initial={{ opacity: 0, y: 30 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6 }}
        className="max-w-lg w-full space-y-8"
      >
        {/* Header */}
        <div className="text-center">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
            className="mx-auto w-16 h-16 bg-gradient-to-r from-mystical-gold to-primary-600 rounded-full flex items-center justify-center mb-6"
          >
            <Star className="w-8 h-8 text-dark-900" />
          </motion.div>
          <h2 className="text-3xl font-mystical text-mystical-gold">
            Начните путешествие
          </h2>
          <p className="mt-2 text-mystical-silver/80">
            Создайте свой астрологический профиль
          </p>
        </div>

        {/* Form */}
        <motion.form
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          transition={{ duration: 0.6, delay: 0.2 }}
          className="mystical-card p-8 space-y-6"
          onSubmit={handleSubmit}
        >
          {error && (
            <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-300 text-center">
              {error}
            </div>
          )}

          {/* Personal Information */}
          <div>
            <h3 className="text-lg font-mystical text-mystical-gold mb-4">
              Личные данные
            </h3>
            
            <div className="space-y-4">
              <div>
                <label htmlFor="name" className="block text-sm font-medium text-mystical-silver mb-2">
                  Полное имя
                </label>
                <div className="relative">
                  <User className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
                  <input
                    id="name"
                    name="name"
                    type="text"
                    required
                    className="mystical-input pl-10 w-full"
                    placeholder="Иван Иванов"
                    value={formData.name}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="email" className="block text-sm font-medium text-mystical-silver mb-2">
                  Email адрес
                </label>
                <div className="relative">
                  <Mail className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    className="mystical-input pl-10 w-full"
                    placeholder="your@email.com"
                    value={formData.email}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-mystical-silver mb-2">
                    Пароль
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      required
                      className="mystical-input pl-10 pr-10 w-full"
                      placeholder="••••••••"
                      value={formData.password}
                      onChange={handleChange}
                    />
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-mystical-silver/50 hover:text-mystical-gold transition-colors"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>

                <div>
                  <label htmlFor="confirmPassword" className="block text-sm font-medium text-mystical-silver mb-2">
                    Подтвердите пароль
                  </label>
                  <div className="relative">
                    <Lock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
                    <input
                      id="confirmPassword"
                      name="confirmPassword"
                      type={showConfirmPassword ? 'text' : 'password'}
                      required
                      className="mystical-input pl-10 pr-10 w-full"
                      placeholder="••••••••"
                      value={formData.confirmPassword}
                      onChange={handleChange}
                    />
                    <button
                      type="button"
                      className="absolute right-3 top-1/2 transform -translate-y-1/2 text-mystical-silver/50 hover:text-mystical-gold transition-colors"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      {showConfirmPassword ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Birth Information */}
          <div>
            <h3 className="text-lg font-mystical text-mystical-gold mb-2">
              Данные рождения
            </h3>
            <p className="text-sm text-mystical-silver/70 mb-4">
              Эти данные необходимы для построения точной натальной карты
            </p>
            
            <div className="space-y-4">
              <div>
                <label htmlFor="birthDate" className="block text-sm font-medium text-mystical-silver mb-2">
                  Дата рождения
                </label>
                <div className="relative">
                  <Calendar className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
                  <input
                    id="birthDate"
                    name="birthDate"
                    type="date"
                    className="mystical-input pl-10 w-full"
                    value={formData.birthDate}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="birthTime" className="block text-sm font-medium text-mystical-silver mb-2">
                  Время рождения (по возможности)
                </label>
                <div className="relative">
                  <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
                  <input
                    id="birthTime"
                    name="birthTime"
                    type="time"
                    className="mystical-input pl-10 w-full"
                    value={formData.birthTime}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="birthPlace" className="block text-sm font-medium text-mystical-silver mb-2">
                  Место рождения (город, страна)
                </label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
                  <input
                    id="birthPlace"
                    name="birthPlace"
                    type="text"
                    className="mystical-input pl-10 w-full"
                    placeholder="Москва, Россия"
                    value={formData.birthPlace}
                    onChange={handleChange}
                  />
                </div>
              </div>
            </div>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="mystical-button w-full py-3 flex items-center justify-center space-x-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? (
              <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
              >
                <Star className="w-5 h-5" />
              </motion.div>
            ) : (
              <>
                <span>Создать аккаунт</span>
                <Star className="w-5 h-5" />
              </>
            )}
          </button>

          <div className="text-center">
            <span className="text-mystical-silver/80">Уже есть аккаунт? </span>
            <Link
              to="/login"
              className="text-mystical-gold hover:text-primary-400 transition-colors font-medium"
            >
              Войти
            </Link>
          </div>
        </motion.form>
      </motion.div>
    </div>
  )
}