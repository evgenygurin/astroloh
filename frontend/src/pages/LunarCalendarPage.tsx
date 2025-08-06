import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import { Moon, ChevronLeft, ChevronRight, Calendar, Star, Info, TrendingUp } from 'lucide-react'
import { lunarApi } from '../services/api'
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameMonth, isSameDay, addMonths, subMonths } from 'date-fns'
import { ru } from 'date-fns/locale'

interface LunarDay {
  date: string
  lunar_day: number
  phase: 'new_moon' | 'waxing_crescent' | 'first_quarter' | 'waxing_gibbous' | 'full_moon' | 'waning_gibbous' | 'last_quarter' | 'waning_crescent'
  phase_name: string
  illumination: number
  recommendations: string[]
  energy_level: 'low' | 'medium' | 'high'
  favorable_activities: string[]
  unfavorable_activities: string[]
}

interface LunarCalendarData {
  month: number
  year: number
  days: LunarDay[]
  current_phase: {
    phase: string
    phase_name: string
    illumination: number
    next_phase: string
    next_phase_date: string
  }
}

export default function LunarCalendarPage() {
  const [currentDate, setCurrentDate] = useState(new Date())
  const [selectedDay, setSelectedDay] = useState<LunarDay | null>(null)
  const [calendarData, setCalendarData] = useState<LunarCalendarData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  const moonPhaseSymbols = {
    new_moon: '🌑',
    waxing_crescent: '🌒',
    first_quarter: '🌓',
    waxing_gibbous: '🌔',
    full_moon: '🌕',
    waning_gibbous: '🌖',
    last_quarter: '🌗',
    waning_crescent: '🌘'
  }

  const phaseColors = {
    new_moon: '#1f2937',
    waxing_crescent: '#374151',
    first_quarter: '#4b5563',
    waxing_gibbous: '#6b7280',
    full_moon: '#fbbf24',
    waning_gibbous: '#d97706',
    last_quarter: '#b45309',
    waning_crescent: '#92400e'
  }

  const energyColors = {
    low: '#6b7280',
    medium: '#f59e0b',
    high: '#ef4444'
  }

  useEffect(() => {
    fetchLunarCalendar()
  }, [currentDate])

  const fetchLunarCalendar = async () => {
    setLoading(true)
    setError('')

    try {
      const data = await lunarApi.getCalendar(
        currentDate.getMonth() + 1,
        currentDate.getFullYear()
      )
      setCalendarData(data)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Ошибка получения лунного календаря')
      // Mock data for demonstration
      const mockDays: LunarDay[] = []
      const monthStart = startOfMonth(currentDate)
      const monthEnd = endOfMonth(currentDate)
      const days = eachDayOfInterval({ start: monthStart, end: monthEnd })

      days.forEach((day, index) => {
        const phase = Object.keys(moonPhaseSymbols)[index % 8] as keyof typeof moonPhaseSymbols
        mockDays.push({
          date: format(day, 'yyyy-MM-dd'),
          lunar_day: (index % 30) + 1,
          phase,
          phase_name: phase.replace('_', ' '),
          illumination: Math.round(Math.random() * 100),
          recommendations: [
            'Благоприятный день для медитации',
            'Хорошее время для новых начинаний'
          ],
          energy_level: ['low', 'medium', 'high'][Math.floor(Math.random() * 3)] as 'low' | 'medium' | 'high',
          favorable_activities: ['Творчество', 'Планирование', 'Отдых'],
          unfavorable_activities: ['Конфликты', 'Важные решения']
        })
      })

      setCalendarData({
        month: currentDate.getMonth() + 1,
        year: currentDate.getFullYear(),
        days: mockDays,
        current_phase: {
          phase: 'waxing_gibbous',
          phase_name: 'Растущая Луна',
          illumination: 85,
          next_phase: 'full_moon',
          next_phase_date: '2024-01-15'
        }
      })
    } finally {
      setLoading(false)
    }
  }

  const handlePrevMonth = () => {
    setCurrentDate(subMonths(currentDate, 1))
    setSelectedDay(null)
  }

  const handleNextMonth = () => {
    setCurrentDate(addMonths(currentDate, 1))
    setSelectedDay(null)
  }

  const handleDayClick = (day: LunarDay) => {
    setSelectedDay(day)
  }

  const monthStart = startOfMonth(currentDate)
  const monthEnd = endOfMonth(currentDate)
  const calendarDays = eachDayOfInterval({ start: monthStart, end: monthEnd })

  return (
    <div className="max-w-7xl mx-auto space-y-8">
      {/* Header */}
      <div className="text-center">
        <motion.div
          animate={{ rotate: 360 }}
          transition={{ duration: 20, repeat: Infinity, ease: "linear" }}
          className="mx-auto w-16 h-16 bg-gradient-to-r from-mystical-gold to-primary-600 rounded-full flex items-center justify-center mb-6"
        >
          <Moon className="w-8 h-8 text-dark-900" />
        </motion.div>
        <h1 className="text-4xl font-mystical text-mystical-gold mb-2">
          Лунный календарь
        </h1>
        <p className="text-mystical-silver/80 max-w-2xl mx-auto">
          Следите за фазами Луны и их влиянием на вашу жизнь
        </p>
      </div>

      {/* Current Phase Info */}
      {calendarData?.current_phase && (
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6 }}
          className="mystical-card p-8 text-center"
        >
          <div className="text-6xl mb-4">
            {moonPhaseSymbols[calendarData.current_phase.phase as keyof typeof moonPhaseSymbols]}
          </div>
          <h2 className="text-2xl font-mystical text-mystical-gold mb-2">
            {calendarData.current_phase.phase_name}
          </h2>
          <p className="text-mystical-silver/80 mb-4">
            Освещенность: {calendarData.current_phase.illumination}%
          </p>
          <div className="flex items-center justify-center space-x-4">
            <div className="text-sm text-mystical-silver/70">
              Следующая фаза: {calendarData.current_phase.next_phase_date}
            </div>
          </div>
        </motion.div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Calendar */}
        <div className="lg:col-span-2">
          <motion.div
            initial={{ opacity: 0, x: -20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6 }}
            className="mystical-card p-6"
          >
            {/* Calendar Header */}
            <div className="flex items-center justify-between mb-6">
              <button
                onClick={handlePrevMonth}
                className="p-2 rounded-lg bg-dark-300/50 text-mystical-gold hover:bg-dark-300/70 transition-colors"
              >
                <ChevronLeft className="w-5 h-5" />
              </button>
              
              <h2 className="text-2xl font-mystical text-mystical-gold">
                {format(currentDate, 'LLLL yyyy', { locale: ru })}
              </h2>
              
              <button
                onClick={handleNextMonth}
                className="p-2 rounded-lg bg-dark-300/50 text-mystical-gold hover:bg-dark-300/70 transition-colors"
              >
                <ChevronRight className="w-5 h-5" />
              </button>
            </div>

            {/* Weekday Headers */}
            <div className="grid grid-cols-7 gap-1 mb-2">
              {['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс'].map((day) => (
                <div key={day} className="p-3 text-center text-mystical-silver/60 font-medium">
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar Grid */}
            {loading ? (
              <div className="text-center py-12">
                <motion.div
                  animate={{ rotate: 360 }}
                  transition={{ duration: 1, repeat: Infinity, ease: "linear" }}
                  className="mx-auto w-8 h-8 text-mystical-gold"
                >
                  <Moon className="w-full h-full" />
                </motion.div>
              </div>
            ) : (
              <div className="grid grid-cols-7 gap-1">
                {calendarDays.map((day) => {
                  const dayData = calendarData?.days.find(d => 
                    isSameDay(new Date(d.date), day)
                  )
                  const isSelected = selectedDay && isSameDay(new Date(selectedDay.date), day)
                  const isToday = isSameDay(day, new Date())

                  return (
                    <motion.button
                      key={day.toString()}
                      whileHover={{ scale: 1.05 }}
                      whileTap={{ scale: 0.95 }}
                      onClick={() => dayData && handleDayClick(dayData)}
                      className={`
                        relative p-3 rounded-lg text-center transition-all duration-200
                        ${isSameMonth(day, currentDate) 
                          ? 'text-mystical-silver hover:bg-dark-300/50' 
                          : 'text-mystical-silver/30 cursor-not-allowed'
                        }
                        ${isSelected ? 'bg-mystical-gold/20 border border-mystical-gold' : ''}
                        ${isToday ? 'bg-mystical-gold/10' : ''}
                      `}
                      disabled={!isSameMonth(day, currentDate) || !dayData}
                    >
                      <div className="text-sm font-medium">
                        {format(day, 'd')}
                      </div>
                      {dayData && (
                        <>
                          <div className="text-xs mt-1">
                            {moonPhaseSymbols[dayData.phase]}
                          </div>
                          <div className="text-xs">
                            {dayData.lunar_day}
                          </div>
                          <div
                            className="absolute bottom-1 right-1 w-2 h-2 rounded-full"
                            style={{ backgroundColor: energyColors[dayData.energy_level] }}
                          />
                        </>
                      )}
                    </motion.button>
                  )
                })}
              </div>
            )}
          </motion.div>
        </div>

        {/* Day Details */}
        <div className="space-y-6">
          {selectedDay ? (
            <motion.div
              key={selectedDay.date}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              className="space-y-6"
            >
              {/* Day Header */}
              <div className="mystical-card p-6 text-center">
                <div className="text-4xl mb-3">
                  {moonPhaseSymbols[selectedDay.phase]}
                </div>
                <h3 className="text-xl font-mystical text-mystical-gold mb-2">
                  {format(new Date(selectedDay.date), 'd MMMM yyyy', { locale: ru })}
                </h3>
                <p className="text-mystical-silver/80 mb-2">
                  {selectedDay.lunar_day} лунный день
                </p>
                <p className="text-mystical-silver/60 text-sm">
                  {selectedDay.phase_name} • {selectedDay.illumination}%
                </p>
                <div
                  className="inline-flex items-center space-x-2 mt-3 px-3 py-1 rounded-full text-xs font-medium"
                  style={{ backgroundColor: `${energyColors[selectedDay.energy_level]}20`, color: energyColors[selectedDay.energy_level] }}
                >
                  <div className="w-2 h-2 rounded-full" style={{ backgroundColor: energyColors[selectedDay.energy_level] }} />
                  <span>Энергия: {selectedDay.energy_level === 'low' ? 'Низкая' : selectedDay.energy_level === 'medium' ? 'Средняя' : 'Высокая'}</span>
                </div>
              </div>

              {/* Recommendations */}
              <div className="mystical-card p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <Info className="w-5 h-5 text-mystical-gold" />
                  <h4 className="text-lg font-mystical text-mystical-gold">
                    Рекомендации
                  </h4>
                </div>
                <ul className="space-y-2">
                  {selectedDay.recommendations.map((rec, index) => (
                    <li key={index} className="text-sm text-mystical-silver/80 flex items-start space-x-2">
                      <Star className="w-3 h-3 text-mystical-gold mt-1 flex-shrink-0" />
                      <span>{rec}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Activities */}
              <div className="mystical-card p-6">
                <div className="flex items-center space-x-2 mb-4">
                  <TrendingUp className="w-5 h-5 text-mystical-gold" />
                  <h4 className="text-lg font-mystical text-mystical-gold">
                    Активности
                  </h4>
                </div>
                
                <div className="space-y-4">
                  <div>
                    <h5 className="text-sm font-medium text-green-400 mb-2">
                      Благоприятно:
                    </h5>
                    <div className="flex flex-wrap gap-2">
                      {selectedDay.favorable_activities.map((activity, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-green-500/20 text-green-300 text-xs rounded-full border border-green-500/30"
                        >
                          {activity}
                        </span>
                      ))}
                    </div>
                  </div>

                  <div>
                    <h5 className="text-sm font-medium text-red-400 mb-2">
                      Не рекомендуется:
                    </h5>
                    <div className="flex flex-wrap gap-2">
                      {selectedDay.unfavorable_activities.map((activity, index) => (
                        <span
                          key={index}
                          className="px-3 py-1 bg-red-500/20 text-red-300 text-xs rounded-full border border-red-500/30"
                        >
                          {activity}
                        </span>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            </motion.div>
          ) : (
            <motion.div
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ duration: 0.6 }}
              className="mystical-card p-8 text-center"
            >
              <Moon className="w-12 h-12 text-mystical-gold/50 mx-auto mb-4" />
              <h3 className="text-lg font-mystical text-mystical-gold mb-2">
                Выберите день
              </h3>
              <p className="text-mystical-silver/60 text-sm">
                Нажмите на любой день в календаре, чтобы узнать лунные рекомендации
              </p>
            </motion.div>
          )}

          {/* Legend */}
          <motion.div
            initial={{ opacity: 0, x: 20 }}
            animate={{ opacity: 1, x: 0 }}
            transition={{ duration: 0.6, delay: 0.2 }}
            className="mystical-card p-6"
          >
            <h4 className="text-lg font-mystical text-mystical-gold mb-4">
              Обозначения
            </h4>
            <div className="space-y-3">
              <div className="text-sm">
                <span className="text-mystical-silver/80">Уровни энергии:</span>
              </div>
              {Object.entries(energyColors).map(([level, color]) => (
                <div key={level} className="flex items-center space-x-2">
                  <div className="w-3 h-3 rounded-full" style={{ backgroundColor: color }} />
                  <span className="text-xs text-mystical-silver/80">
                    {level === 'low' ? 'Низкая' : level === 'medium' ? 'Средняя' : 'Высокая'}
                  </span>
                </div>
              ))}
            </div>
          </motion.div>
        </div>
      </div>
    </div>
  )
}