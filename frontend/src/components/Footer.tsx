import { Heart, Mail, Phone } from 'lucide-react'

export default function Footer() {
  return (
    <footer className="bg-dark-200/50 border-t border-mystical-gold/20 py-12">
      <div className="container mx-auto px-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          {/* About */}
          <div>
            <h3 className="text-xl font-mystical text-mystical-gold mb-4">
              О нас
            </h3>
            <p className="text-mystical-silver/80 leading-relaxed">
              Astroloh — это современный сервис астрологических консультаций, 
              который помогает людям лучше понять себя и свое место во вселенной 
              через древние знания астрологии.
            </p>
          </div>

          {/* Services */}
          <div>
            <h3 className="text-xl font-mystical text-mystical-gold mb-4">
              Услуги
            </h3>
            <ul className="space-y-2 text-mystical-silver/80">
              <li>Построение натальных карт</li>
              <li>Персональные гороскопы</li>
              <li>Анализ совместимости</li>
              <li>Лунный календарь</li>
              <li>Транзитные прогнозы</li>
            </ul>
          </div>

          {/* Contact */}
          <div>
            <h3 className="text-xl font-mystical text-mystical-gold mb-4">
              Контакты
            </h3>
            <div className="space-y-3">
              <div className="flex items-center space-x-3 text-mystical-silver/80">
                <Mail className="w-5 h-5 text-mystical-gold" />
                <span>info@astroloh.ru</span>
              </div>
              <div className="flex items-center space-x-3 text-mystical-silver/80">
                <Phone className="w-5 h-5 text-mystical-gold" />
                <span>+7 (800) 123-45-67</span>
              </div>
            </div>
          </div>
        </div>

        <div className="mt-8 pt-8 border-t border-mystical-gold/20 text-center">
          <p className="text-mystical-silver/60 flex items-center justify-center space-x-2">
            <span>&copy; 2024 Astroloh. Создано с</span>
            <Heart className="w-4 h-4 text-red-500 animate-pulse" />
            <span>для познания себя</span>
          </p>
        </div>
      </div>
    </footer>
  )
}