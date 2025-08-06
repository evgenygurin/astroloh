import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
import { Star, Moon, Zap, Heart, User } from 'lucide-react'

export default function HomePage() {
  const features = [
    {
      icon: User,
      title: 'Натальная карта',
      description: 'Персональная астрологическая карта на момент рождения',
      link: '/natal-chart',
      color: 'from-blue-500 to-purple-600'
    },
    {
      icon: Star,
      title: 'Гороскопы',
      description: 'Ежедневные, еженедельные и месячные прогнозы',
      link: '/horoscope',
      color: 'from-yellow-400 to-orange-500'
    },
    {
      icon: Moon,
      title: 'Лунный календарь',
      description: 'Фазы Луны и их влияние на жизнь',
      link: '/lunar-calendar',
      color: 'from-indigo-400 to-blue-500'
    },
    {
      icon: Heart,
      title: 'Совместимость',
      description: 'Анализ отношений и совместимости пар',
      link: '/compatibility',
      color: 'from-pink-400 to-red-500'
    }
  ]

  const zodiacSigns = [
    '♈', '♉', '♊', '♋', '♌', '♍',
    '♎', '♏', '♐', '♑', '♒', '♓'
  ]

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="text-center py-20 relative overflow-hidden">
        {/* Animated zodiac signs background */}
        <div className="absolute inset-0 opacity-10">
          {zodiacSigns.map((sign, index) => (
            <motion.div
              key={index}
              className="absolute text-6xl text-mystical-gold"
              style={{
                left: `${Math.random() * 100}%`,
                top: `${Math.random() * 100}%`,
              }}
              animate={{
                rotate: 360,
                scale: [1, 1.2, 1],
              }}
              transition={{
                duration: 10 + index * 2,
                repeat: Infinity,
                ease: "linear"
              }}
            >
              {sign}
            </motion.div>
          ))}
        </div>

        <div className="relative z-10">
          <motion.div
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
            className="mb-8"
          >
            <h1 className="text-5xl md:text-7xl font-mystical text-mystical-gold mb-6">
              Astroloh
            </h1>
            <p className="text-xl md:text-2xl text-mystical-silver/80 max-w-3xl mx-auto leading-relaxed">
              Откройте тайны вселенной через персональные астрологические консультации
            </p>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8, delay: 0.3 }}
            className="flex flex-col sm:flex-row gap-4 justify-center items-center"
          >
            <Link
              to="/natal-chart"
              className="mystical-button text-lg px-8 py-3"
            >
              Построить натальную карту
            </Link>
            <Link
              to="/horoscope"
              className="border border-mystical-gold text-mystical-gold hover:bg-mystical-gold hover:text-dark-900 font-semibold py-3 px-8 rounded-full transition-all duration-300"
            >
              Узнать гороскоп
            </Link>
          </motion.div>
        </div>
      </section>

      {/* Features Grid */}
      <section className="py-20">
        <div className="text-center mb-16">
          <h2 className="text-4xl font-mystical text-mystical-gold mb-4">
            Наши услуги
          </h2>
          <p className="text-lg text-mystical-silver/80 max-w-2xl mx-auto">
            Современные технологии встречают древние знания астрологии
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {features.map((feature, index) => (
            <motion.div
              key={feature.title}
              initial={{ opacity: 0, y: 30 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="group"
            >
              <Link to={feature.link}>
                <div className="mystical-card p-8 h-full hover:scale-105 transition-all duration-300 group-hover:border-mystical-gold/40">
                  <div className={`w-16 h-16 rounded-full bg-gradient-to-br ${feature.color} flex items-center justify-center mb-6 group-hover:scale-110 transition-transform duration-300`}>
                    <feature.icon className="w-8 h-8 text-white" />
                  </div>
                  <h3 className="text-2xl font-mystical text-mystical-gold mb-4">
                    {feature.title}
                  </h3>
                  <p className="text-mystical-silver/80 leading-relaxed">
                    {feature.description}
                  </p>
                  <div className="mt-6 flex items-center text-mystical-gold group-hover:translate-x-2 transition-transform duration-300">
                    <span className="mr-2">Узнать больше</span>
                    <motion.div
                      animate={{ x: [0, 5, 0] }}
                      transition={{ duration: 1.5, repeat: Infinity }}
                    >
                      <Zap className="w-4 h-4" />
                    </motion.div>
                  </div>
                </div>
              </Link>
            </motion.div>
          ))}
        </div>
      </section>

      {/* Statistics */}
      <section className="py-20 bg-gradient-to-r from-dark-200/30 to-dark-100/30 rounded-2xl">
        <div className="text-center mb-12">
          <h2 className="text-4xl font-mystical text-mystical-gold mb-4">
            Доверие тысяч людей
          </h2>
        </div>
        
        <div className="grid grid-cols-1 md:grid-cols-4 gap-8 text-center">
          {[
            { number: '10,000+', label: 'Построенных карт' },
            { number: '50,000+', label: 'Прогнозов' },
            { number: '5,000+', label: 'Довольных клиентов' },
            { number: '99%', label: 'Точность прогнозов' }
          ].map((stat, index) => (
            <motion.div
              key={index}
              initial={{ opacity: 0, scale: 0.5 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ duration: 0.6, delay: index * 0.1 }}
              className="group"
            >
              <div className="text-4xl font-mystical text-mystical-gold mb-2 group-hover:scale-110 transition-transform duration-300">
                {stat.number}
              </div>
              <div className="text-mystical-silver/80">
                {stat.label}
              </div>
            </motion.div>
          ))}
        </div>
      </section>

      {/* CTA Section */}
      <section className="py-20 text-center">
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="max-w-4xl mx-auto"
        >
          <h2 className="text-4xl font-mystical text-mystical-gold mb-6">
            Готовы узнать свое будущее?
          </h2>
          <p className="text-xl text-mystical-silver/80 mb-8 leading-relaxed">
            Начните свое астрологическое путешествие прямо сейчас. 
            Создайте аккаунт и получите персональные рекомендации от звезд.
          </p>
          <Link
            to="/register"
            className="mystical-button text-xl px-12 py-4 inline-flex items-center space-x-2"
          >
            <Star className="w-6 h-6" />
            <span>Начать путешествие</span>
          </Link>
        </motion.div>
      </section>
    </div>
  )
}