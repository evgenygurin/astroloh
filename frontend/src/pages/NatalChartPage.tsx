import { useState, useEffect, useRef } from 'react'
import { motion } from 'framer-motion'
import * as d3 from 'd3'
import { Calendar, Clock, MapPin, Star, Download, Info } from 'lucide-react'
import { astrologyApi } from '../services/api'

interface Planet {
  name: string
  symbol: string
  degree: number
  sign: string
  house: number
  color: string
}

interface NatalChartData {
  planets: Planet[]
  houses: number[]
  aspects: Array<{
    planet1: string
    planet2: string
    aspect: string
    orb: number
  }>
}

export default function NatalChartPage() {
  const [chartData, setChartData] = useState<NatalChartData | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const [formData, setFormData] = useState({
    birthDate: '',
    birthTime: '',
    birthPlace: ''
  })
  
  const svgRef = useRef<SVGSVGElement>(null)

  const planets: Planet[] = [
    { name: 'Sun', symbol: '☉', degree: 45, sign: 'Aries', house: 1, color: '#FFD700' },
    { name: 'Moon', symbol: '☽', degree: 120, sign: 'Leo', house: 5, color: '#C0C0C0' },
    { name: 'Mercury', symbol: '☿', degree: 60, sign: 'Taurus', house: 2, color: '#FFA500' },
    { name: 'Venus', symbol: '♀', degree: 30, sign: 'Aries', house: 1, color: '#FF69B4' },
    { name: 'Mars', symbol: '♂', degree: 200, sign: 'Libra', house: 7, color: '#FF4500' },
    { name: 'Jupiter', symbol: '♃', degree: 150, sign: 'Virgo', house: 6, color: '#4169E1' },
    { name: 'Saturn', symbol: '♄', degree: 280, sign: 'Capricorn', house: 10, color: '#8B4513' },
    { name: 'Uranus', symbol: '♅', degree: 90, sign: 'Gemini', house: 3, color: '#40E0D0' },
    { name: 'Neptune', symbol: '♆', degree: 240, sign: 'Sagittarius', house: 9, color: '#9370DB' },
    { name: 'Pluto', symbol: '♇', degree: 320, sign: 'Aquarius', house: 11, color: '#8B0000' }
  ]

  const zodiacSigns = [
    { name: 'Aries', symbol: '♈', degrees: 0 },
    { name: 'Taurus', symbol: '♉', degrees: 30 },
    { name: 'Gemini', symbol: '♊', degrees: 60 },
    { name: 'Cancer', symbol: '♋', degrees: 90 },
    { name: 'Leo', symbol: '♌', degrees: 120 },
    { name: 'Virgo', symbol: '♍', degrees: 150 },
    { name: 'Libra', symbol: '♎', degrees: 180 },
    { name: 'Scorpio', symbol: '♏', degrees: 210 },
    { name: 'Sagittarius', symbol: '♐', degrees: 240 },
    { name: 'Capricorn', symbol: '♑', degrees: 270 },
    { name: 'Aquarius', symbol: '♒', degrees: 300 },
    { name: 'Pisces', symbol: '♓', degrees: 330 }
  ]

  useEffect(() => {
    if (svgRef.current) {
      drawNatalChart()
    }
  }, [])

  const drawNatalChart = () => {
    const svg = d3.select(svgRef.current)
    svg.selectAll("*").remove()

    const width = 400
    const height = 400
    const radius = 180
    const center = { x: width / 2, y: height / 2 }

    svg.attr('width', width).attr('height', height)

    // Outer circle (zodiac)
    svg.append('circle')
      .attr('cx', center.x)
      .attr('cy', center.y)
      .attr('r', radius)
      .attr('fill', 'none')
      .attr('stroke', '#fbbf24')
      .attr('stroke-width', 2)

    // Inner circle (houses)
    svg.append('circle')
      .attr('cx', center.x)
      .attr('cy', center.y)
      .attr('r', radius * 0.7)
      .attr('fill', 'none')
      .attr('stroke', '#fbbf24')
      .attr('stroke-width', 1)
      .attr('opacity', 0.5)

    // Zodiac divisions
    for (let i = 0; i < 12; i++) {
      const angle = (i * 30 - 90) * (Math.PI / 180)
      const x1 = center.x + Math.cos(angle) * radius * 0.7
      const y1 = center.y + Math.sin(angle) * radius * 0.7
      const x2 = center.x + Math.cos(angle) * radius
      const y2 = center.y + Math.sin(angle) * radius

      svg.append('line')
        .attr('x1', x1)
        .attr('y1', y1)
        .attr('x2', x2)
        .attr('y2', y2)
        .attr('stroke', '#fbbf24')
        .attr('stroke-width', 1)
        .attr('opacity', 0.3)
    }

    // Zodiac signs
    zodiacSigns.forEach((sign, i) => {
      const angle = (sign.degrees + 15 - 90) * (Math.PI / 180)
      const x = center.x + Math.cos(angle) * radius * 0.85
      const y = center.y + Math.sin(angle) * radius * 0.85

      svg.append('text')
        .attr('x', x)
        .attr('y', y)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('font-size', '18px')
        .attr('fill', '#fbbf24')
        .attr('opacity', 0.8)
        .text(sign.symbol)
    })

    // House numbers
    for (let i = 1; i <= 12; i++) {
      const angle = ((i - 1) * 30 + 15 - 90) * (Math.PI / 180)
      const x = center.x + Math.cos(angle) * radius * 0.55
      const y = center.y + Math.sin(angle) * radius * 0.55

      svg.append('text')
        .attr('x', x)
        .attr('y', y)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('font-size', '12px')
        .attr('fill', '#e5e7eb')
        .attr('opacity', 0.6)
        .text(i.toString())
    }

    // Planets
    planets.forEach((planet, i) => {
      const angle = (planet.degree - 90) * (Math.PI / 180)
      const x = center.x + Math.cos(angle) * radius * 0.9
      const y = center.y + Math.sin(angle) * radius * 0.9

      // Planet circle
      svg.append('circle')
        .attr('cx', x)
        .attr('cy', y)
        .attr('r', 8)
        .attr('fill', planet.color)
        .attr('stroke', '#1e1b4b')
        .attr('stroke-width', 2)

      // Planet symbol
      svg.append('text')
        .attr('x', x)
        .attr('y', y)
        .attr('text-anchor', 'middle')
        .attr('dominant-baseline', 'middle')
        .attr('font-size', '12px')
        .attr('fill', '#1e1b4b')
        .attr('font-weight', 'bold')
        .text(planet.symbol)

      // Connection line to center
      svg.append('line')
        .attr('x1', center.x)
        .attr('y1', center.y)
        .attr('x2', x)
        .attr('y2', y)
        .attr('stroke', planet.color)
        .attr('stroke-width', 1)
        .attr('opacity', 0.3)
    })

    // Center point
    svg.append('circle')
      .attr('cx', center.x)
      .attr('cy', center.y)
      .attr('r', 3)
      .attr('fill', '#fbbf24')
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)
    setError('')

    try {
      const data = await astrologyApi.getNatalChart({
        date: formData.birthDate,
        time: formData.birthTime,
        location: formData.birthPlace
      })
      setChartData(data)
    } catch (err: any) {
      setError(err.response?.data?.message || 'Ошибка получения натальной карты')
    } finally {
      setLoading(false)
    }
  }

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData(prev => ({
      ...prev,
      [e.target.name]: e.target.value
    }))
  }

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
          Натальная карта
        </h1>
        <p className="text-mystical-silver/80 max-w-2xl mx-auto">
          Получите детальный анализ своего астрологического портрета на момент рождения
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Form */}
        <motion.div
          initial={{ opacity: 0, x: -20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6 }}
        >
          <div className="mystical-card p-8">
            <h2 className="text-2xl font-mystical text-mystical-gold mb-6">
              Данные рождения
            </h2>

            <form onSubmit={handleSubmit} className="space-y-6">
              {error && (
                <div className="bg-red-500/20 border border-red-500/50 rounded-lg p-4 text-red-300">
                  {error}
                </div>
              )}

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
                    required
                    className="mystical-input pl-10 w-full"
                    value={formData.birthDate}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="birthTime" className="block text-sm font-medium text-mystical-silver mb-2">
                  Время рождения
                </label>
                <div className="relative">
                  <Clock className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
                  <input
                    id="birthTime"
                    name="birthTime"
                    type="time"
                    required
                    className="mystical-input pl-10 w-full"
                    value={formData.birthTime}
                    onChange={handleChange}
                  />
                </div>
              </div>

              <div>
                <label htmlFor="birthPlace" className="block text-sm font-medium text-mystical-silver mb-2">
                  Место рождения
                </label>
                <div className="relative">
                  <MapPin className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-mystical-silver/50" />
                  <input
                    id="birthPlace"
                    name="birthPlace"
                    type="text"
                    required
                    className="mystical-input pl-10 w-full"
                    placeholder="Город, страна"
                    value={formData.birthPlace}
                    onChange={handleChange}
                  />
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
                    <span>Построить карту</span>
                    <Star className="w-5 h-5" />
                  </>
                )}
              </button>
            </form>
          </div>
        </motion.div>

        {/* Chart Visualization */}
        <motion.div
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ duration: 0.6, delay: 0.2 }}
        >
          <div className="mystical-card p-8">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-mystical text-mystical-gold">
                Визуализация
              </h2>
              <button className="flex items-center space-x-2 text-mystical-gold hover:text-primary-400 transition-colors">
                <Download className="w-4 h-4" />
                <span>Скачать</span>
              </button>
            </div>

            <div className="flex justify-center">
              <svg
                ref={svgRef}
                className="border border-mystical-gold/20 rounded-lg bg-dark-300/30"
              />
            </div>
          </div>
        </motion.div>
      </div>

      {/* Planet Positions */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.4 }}
        className="mystical-card p-8"
      >
        <h2 className="text-2xl font-mystical text-mystical-gold mb-6">
          Положения планет
        </h2>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {planets.map((planet) => (
            <div key={planet.name} className="bg-dark-300/30 rounded-lg p-4">
              <div className="flex items-center space-x-3 mb-2">
                <div
                  className="w-6 h-6 rounded-full flex items-center justify-center text-sm font-bold"
                  style={{ backgroundColor: planet.color, color: '#1e1b4b' }}
                >
                  {planet.symbol}
                </div>
                <span className="text-mystical-silver font-medium">{planet.name}</span>
              </div>
              <div className="text-sm space-y-1">
                <div className="text-mystical-silver/80">
                  <span className="text-mystical-gold">{planet.degree}°</span> {planet.sign}
                </div>
                <div className="text-mystical-silver/60">
                  {planet.house} дом
                </div>
              </div>
            </div>
          ))}
        </div>
      </motion.div>

      {/* Interpretation */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.6, delay: 0.6 }}
        className="mystical-card p-8"
      >
        <div className="flex items-center space-x-2 mb-6">
          <Info className="w-6 h-6 text-mystical-gold" />
          <h2 className="text-2xl font-mystical text-mystical-gold">
            Интерпретация
          </h2>
        </div>
        
        <div className="prose prose-invert max-w-none">
          <p className="text-mystical-silver/80 leading-relaxed mb-4">
            Ваша натальная карта представляет уникальную конфигурацию небесных тел на момент вашего рождения. 
            Это космический отпечаток, который раскрывает ваши природные таланты, склонности и жизненный путь.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mt-6">
            <div className="bg-dark-300/30 rounded-lg p-4">
              <h3 className="text-mystical-gold font-mystical mb-3">Личность</h3>
              <p className="text-mystical-silver/80 text-sm">
                Ваше Солнце в Овне указывает на сильную, независимую натуру с природными лидерскими качествами.
              </p>
            </div>
            
            <div className="bg-dark-300/30 rounded-lg p-4">
              <h3 className="text-mystical-gold font-mystical mb-3">Эмоции</h3>
              <p className="text-mystical-silver/80 text-sm">
                Луна во Льве говорит о потребности в признании и творческом самовыражении.
              </p>
            </div>
          </div>
        </div>
      </motion.div>
    </div>
  )
}