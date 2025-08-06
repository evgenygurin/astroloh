import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Star, Sun, Calendar, TrendingUp, Heart, Briefcase, Zap } from 'lucide-react'
import { astrologyApi } from '../services/api'

interface HoroscopeData {
  sign: string
  date: string
  general: string
  love: string
  career: string
  health: string
  lucky_numbers: number[]
  lucky_colors: string[]
}

export default function HoroscopePage() {
  const [selectedSign, setSelectedSign] = useState('aries')
  const [selectedPeriod, setSelectedPeriod] = useState<'daily' | 'weekly' | 'monthly'>('daily')
  const [horoscopeData, setHoroscopeData] = useState<HoroscopeData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const zodiacSigns = [
    { key: 'aries', name: 'Овен', symbol: '♈', dates: '21 мар - 19 апр', color: '#FF6B6B' },
    { key: 'taurus', name: 'Телец', symbol: '♉', dates: '20 апр - 20 мая', color: '#4ECDC4' },
    { key: 'gemini', name: 'Близнецы', symbol: '♊', dates: '21 мая - 20 июн', color: '#45B7D1' },
    { key: 'cancer', name: 'Рак', symbol: '♋', dates: '21 июн - 22 июл', color: '#96CEB4' },
    { key: 'leo', name: 'Лев', symbol: '♌', dates: '23 июл - 22 авг', color: '#FFEAA7' },
    { key: 'virgo', name: 'Дева', symbol: '♍', dates: '23 авг - 22 сен', color: '#DDA0DD' },
    { key: 'libra', name: 'Весы', symbol: '♎', dates: '23 сен - 22 окт', color: '#74B9FF' },
    { key: 'scorpio', name: 'Скорпион', symbol: '♏', dates: '23 окт - 21 ноя', color: '#FD79A8' },
    { key: 'sagittarius', name: 'Стрелец', symbol: '♐', dates: '22 ноя - 21 дек', color: '#FDCB6E' },
    { key: 'capricorn', name: 'Козерог', symbol: '♑', dates: '22 дек - 19 янв', color: '#6C5CE7' },
    { key: 'aquarius', name: 'Водолей', symbol: '♒', dates: '20 янв - 18 фев', color: '#A29BFE' },
    { key: 'pisces', name: 'Рыбы', symbol: '♓', dates: '19 фев - 20 мар', color: '#FD79A8' }
  ]

  const periods = [
    { key: 'daily', name: 'Сегодня', icon: Sun },
    { key: 'weekly', name: 'Эта неделя', icon: Calendar },
    { key: 'monthly', name: 'Этот месяц', icon: TrendingUp }
  ]

  useEffect(() => {
    fetchHoroscope()
  }, [selectedSign, selectedPeriod])

  const fetchHoroscope = async () => {
    setLoading(true)
    setError('')

    try {
      const data = await astrologyApi.getHoroscope(selectedSign, selectedPeriod)
      setHoroscopeData(data)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Ошибка получения гороскопа')
      // Mock data for demonstration
      setHoroscopeData({
        sign: selectedSign,
        date: new Date().toLocaleDateString('ru-RU'),
        general: 'Сегодня звезды благосклонны к вам. Это хорошее время для новых начинаний и важных решений. Ваша интуиция особенно остра, доверяйте внутреннему голосу.',
        love: 'В отношениях наступает период гармонии. Одиноким представителям знака стоит быть более открытыми к новым знакомствам.',
        career: 'Профессиональная сфера требует вашего внимания. Возможны интересные предложения или продвижение по службе.',
        health: 'Общее самочувствие хорошее, но стоит уделить больше внимания режиму дня и качественному отдыху.',
        lucky_numbers: [7, 15, 23, 31, 42],
        lucky_colors: ['золотой', 'синий', 'зеленый']
      })
    } finally {
      setLoading(false)
    }
  }

  const currentSign = zodiacSigns.find(sign => sign.key === selectedSign)

  return (
    <div className="max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="mx-auto w-16 h-16 bg-gradient-to-r from-mystical-gold to-primary-600 rounded-full flex items-center justify-center mb-6"
        >
          <Star className="w-8 h-8 text-dark-900" />
        </motion.div>
        <h1 className="text-4xl font-mystical text-mystical-gold mb-2">
          Гороскопы
        </h1>
        <p className="text-mystical-silver/80 max-w-2xl mx-auto">
          Узнайте, что говорят вам звезды на сегодня, эту неделю или месяц
        </p>
      </div>

      {/* Period Selection */}
      <div className="flex justify-center">
        <div className="inline-flex bg-dark-200/50 rounded-lg p-1">
          {periods.map((period) => (
            <button
              key={period.key}
              onClick={() => setSelectedPeriod(period.key as 'daily' | 'weekly' | 'monthly')}
              className={`flex items-center space-x-2 px-4 py-2 rounded-md transition-all duration-200 ${
                selectedPeriod === period.key
                  ? 'bg-mystical-gold text-dark-900'
                  : 'text-mystical-silver hover:text-mystical-gold'
              }`}
            >
              <period.icon className="w-4 h-4" />
              <span>{period.name}</span>
            </button>
          ))}
        </div>
      </div>

      {/* Zodiac Signs Grid */}
      <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
        {zodiacSigns.map((sign, index) => (
          <motion.button
            key={sign.key}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, delay: index * 0.05 }}
            onClick={() => setSelectedSign(sign.key)}
            className={`mystical-card p-4 text-center hover:scale-105 transition-all duration-300 ${
              selectedSign === sign.key
                ? 'border-mystical-gold shadow-lg shadow-mystical-gold/20'
                : 'hover:border-mystical-gold/40'
            }`}
          >
            <div
              className="text-3xl mb-2"
              style={{ color: selectedSign === sign.key ? sign.color : '#fbbf24' }}
            >
              {sign.symbol}
            </div>
            <h3 className={`font-mystical text-sm ${
              selectedSign === sign.key ? 'text-mystical-gold' : 'text-mystical-silver'
            }`}>
              {sign.name}
            </h3>
            <p className="text-xs text-mystical-silver/60 mt-1">
              {sign.dates}
            </p>
          </motion.button>
        ))}
      </div>

      {/* Horoscope Content */}
      {loading ? (
        <div className="text-center py-12">
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
            className="mx-auto w-8 h-8 text-mystical-gold"
          >
            <Star className="w-full h-full" />
          </motion.div>
          <p className="text-mystical-silver/80 mt-4">Консультируемся со звездами...</p>
        </div>
      ) : horoscopeData && currentSign ? (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="space-y-8"
        >
          {/* Header for selected sign */}
          <div className="mystical-card p-8 text-center">
            <div
              className="text-6xl mb-4"
              style={{ color: currentSign.color }}
            >
              {currentSign.symbol}
            </div>
            <h2 className="text-3xl font-mystical text-mystical-gold mb-2">
              {currentSign.name}
            </h2>
            <p className="text-mystical-silver/80">
              {currentSign.dates} • {horoscopeData.date}
            </p>
          </div>

          {/* General Forecast */}
          <div className="mystical-card p-8">
            <div className="flex items-center space-x-3 mb-6">
              <Star className="w-6 h-6 text-mystical-gold" />
              <h3 className="text-2xl font-mystical text-mystical-gold">
                Общий прогноз
              </h3>
            </div>
            <p className="text-mystical-silver/90 leading-relaxed text-lg">
              {horoscopeData.general}
            </p>
          </div>

          {/* Detailed Forecasts */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            {/* Love */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.1 }}
              className="mystical-card p-6"
            >
              <div className="flex items-center space-x-3 mb-4">
                <Heart className="w-5 h-5 text-pink-400" />
                <h4 className="text-xl font-mystical text-mystical-gold">
                  Любовь
                </h4>
              </div>
              <p className="text-mystical-silver/80 leading-relaxed">
                {horoscopeData.love}
              </p>
            </motion.div>

            {/* Career */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="mystical-card p-6"
            >
              <div className="flex items-center space-x-3 mb-4">
                <Briefcase className="w-5 h-5 text-blue-400" />
                <h4 className="text-xl font-mystical text-mystical-gold">
                  Карьера
                </h4>
              </div>
              <p className="text-mystical-silver/80 leading-relaxed">
                {horoscopeData.career}
              </p>
            </motion.div>

            {/* Health */}
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.3 }}
              className="mystical-card p-6"
            >
              <div className="flex items-center space-x-3 mb-4">
                <Zap className="w-5 h-5 text-green-400" />
                <h4 className="text-xl font-mystical text-mystical-gold">
                  Здоровье
                </h4>
              </div>
              <p className="text-mystical-silver/80 leading-relaxed">
                {horoscopeData.health}
              </p>
            </motion.div>
          </div>

          {/* Lucky Elements */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Lucky Numbers */}
            <motion.div
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="mystical-card p-6"
            >
              <h4 className="text-xl font-mystical text-mystical-gold mb-4">
                Счастливые числа
              </h4>
              <div className="flex flex-wrap gap-3">
                {horoscopeData.lucky_numbers.map((number, index) => (
                  <div
                    key={index}
                    className="w-12 h-12 rounded-full bg-gradient-to-br from-mystical-gold to-primary-600 flex items-center justify-center text-dark-900 font-bold"
                  >
                    {number}
                  </div>
                ))}
              </div>
            </motion.div>

            {/* Lucky Colors */}
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6, delay: 0.5 }}
              className="mystical-card p-6"
            >
              <h4 className="text-xl font-mystical text-mystical-gold mb-4">
                Счастливые цвета
              </h4>
              <div className="flex flex-wrap gap-3">
                {horoscopeData.lucky_colors.map((color, index) => (
                  <div
                    key={index}
                    className="px-4 py-2 rounded-full bg-dark-300/50 border border-mystical-gold/30 text-mystical-silver capitalize"
                  >
                    {color}
                  </div>
                ))}
              </div>
            </motion.div>
          </div>
        </motion.div>
      ) : error && (
        <div className="text-center py-12">
          <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-6 max-w-md mx-auto">
            <p className="text-red-300">{error}</p>
          </div>
        </div>
      )}
    </div>
  )
}