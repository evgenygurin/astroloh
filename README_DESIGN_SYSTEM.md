# Astroloh Design System

## 🎨 Overview

The Astroloh Design System is a comprehensive UI/UX framework specifically crafted for astrological applications. It combines mystical aesthetics with modern usability principles to create engaging and accessible user experiences across all platforms.

## ✨ Features

### 🎯 Core Components
- **Natal Charts**: Interactive circular birth chart visualizations
- **Planet Cards**: Informative displays of planetary influences  
- **Lunar Calendar**: Calendar with lunar phases and astrological events
- **Progress Bars**: Visual indicators for compatibility and influences
- **Form Elements**: Styled inputs, selects, and buttons with cosmic themes

### 🌙 Mystical Design Language
- **Dark cosmic backgrounds** with starfield effects
- **Golden accent colors** representing celestial illumination
- **Cinzel typography** for mystical headers
- **Authentic astrological symbols** (♈♉♊♋♌♍♎♏♐♑♒♓)
- **Smooth animations** with floating particles and glowing effects

### 📱 Multi-Platform Support
- **Web Interface**: Full desktop experience with responsive design
- **Mobile Apps**: Touch-optimized with 44px minimum targets
- **Yandex Alice**: Voice-first with rich visual cards
- **Telegram Bot**: Compact design for messaging context

### ♿ Accessibility First
- **WCAG 2.1 AA compliant** with high contrast ratios
- **Keyboard navigation** with clear focus indicators  
- **Screen reader support** with semantic HTML and ARIA labels
- **Reduced motion** respect for user preferences

## 🚀 Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/evgenygurin/astroloh.git
cd astroloh/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### Basic Usage

```tsx
import React from 'react';
import { NatalChart, PlanetCard, DESIGN_CLASSES } from './src/design-system';
import './src/design-system/tokens.css';
import './src/design-system/components.css';

function App() {
  const planets = [
    { planet: 'sun', sign: 'leo', degree: 15, house: 1 },
    { planet: 'moon', sign: 'cancer', degree: 28, house: 12 }
  ];

  return (
    <div className={DESIGN_CLASSES.PLATFORM_WEB}>
      <div className={DESIGN_CLASSES.WEB_DASHBOARD_GRID}>
        <NatalChart planets={planets} size="large" />
        <PlanetCard 
          planet="sun" 
          sign="leo" 
          house={1}
          influence={{
            love: 85,
            career: 70,
            health: 90,
            money: 65
          }}
        />
      </div>
    </div>
  );
}
```

## 📚 Documentation

### Design System Files
- 📄 **[Design System Guide](./docs/DESIGN_SYSTEM.md)** - Complete component library and usage guidelines
- 📋 **[UX Guidelines](./docs/UX_GUIDELINES.md)** - User experience principles and patterns
- 🎨 **[Figma Assets](./design-assets/)** - Visual design files and prototypes *(coming soon)*

### Component Documentation
- 🔮 **[NatalChart](./frontend/src/components/design-system/NatalChart.tsx)** - Interactive birth chart component
- 🪐 **[PlanetCard](./frontend/src/components/design-system/PlanetCard.tsx)** - Planet information display
- 🌙 **[LunarCalendar](./frontend/src/components/design-system/LunarCalendar.tsx)** - Lunar phase calendar

### Design Tokens
- 🎯 **[tokens.css](./frontend/src/design-system/tokens.css)** - Core design variables
- 🔤 **[typography.css](./frontend/src/design-system/typography.css)** - Typography system
- 🧩 **[components.css](./frontend/src/design-system/components.css)** - Component styles

## 🎨 Design Philosophy

### Mystical Aesthetics
Our design embraces the wonder and mystery of astrology through:
- Deep space-inspired color palettes
- Celestial golden accents and glowing effects
- Authentic astrological symbolism
- Floating particle animations

### Accessibility & Usability
While mystical, the interface remains highly usable:
- High contrast ratios (4.5:1 minimum)
- Large touch targets (44px minimum)
- Clear typography hierarchy
- Intuitive navigation patterns

### Platform Adaptation
The design system adapts seamlessly across contexts:
- **Desktop**: Rich layouts with detailed visualizations
- **Mobile**: Touch-optimized single-column layouts
- **Voice**: High-contrast cards for screen-based voice assistants
- **Messaging**: Compact cards optimized for chat interfaces

## 🛠️ Development

### Project Structure
```
frontend/src/design-system/
├── tokens.css          # Design tokens and CSS variables
├── components.css      # Component styles  
├── typography.css      # Typography system
├── platform-styles.css # Platform-specific adaptations
├── icons.ts           # Astrological symbols and constants
└── index.ts           # Main exports

frontend/src/components/design-system/
├── NatalChart.tsx      # Interactive birth chart
├── PlanetCard.tsx      # Planet information display
└── LunarCalendar.tsx   # Lunar calendar with events
```

### Available Scripts
```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run preview      # Preview production build

# Quality
npm run lint         # Run ESLint
npm run type-check   # Run TypeScript checking
```

### CSS Architecture
The design system uses a modular CSS approach:

1. **Design Tokens**: Core variables and design decisions
2. **Component Styles**: Reusable UI component styles  
3. **Platform Styles**: Responsive and platform-specific adaptations
4. **Typography**: Text styling and font loading

### Browser Support
- ✅ Chrome 80+
- ✅ Firefox 75+
- ✅ Safari 13+
- ✅ Edge 80+
- ✅ iOS Safari 12+
- ✅ Android Chrome 80+

## 🎯 Platform Implementations

### Web Application
```tsx
<div className="platform-web">
  <div className="web-dashboard-grid">
    <NatalChart planets={planets} size="large" interactive />
    <div className="web-planet-grid">
      {planets.map(planet => (
        <PlanetCard key={planet.planet} {...planet} />
      ))}
    </div>
  </div>
</div>
```

### Mobile Application
```tsx
<div className="platform-mobile">
  <div className="mobile-single-column">
    <div className="mobile-chart-container">
      <NatalChart planets={planets} size="medium" />
    </div>
    {planets.map(planet => (
      <PlanetCard key={planet.planet} {...planet} size="small" />
    ))}
  </div>
</div>
```

### Yandex Alice Integration
```tsx
<div className="platform-yandex">
  <div className="yandex-rich-content">
    <div className="yandex-horoscope-card">
      <h2>Your Daily Horoscope</h2>
      <p>Today brings opportunities for Leo...</p>
    </div>
  </div>
</div>
```

### Telegram Bot Cards
```tsx
<div className="platform-telegram">
  <div className="telegram-keyboard">
    <div className="telegram-keyboard-row">
      <button className="telegram-button">Daily Horoscope</button>
      <button className="telegram-button">Natal Chart</button>
    </div>
  </div>
</div>
```

## 🎭 Design Tokens Reference

### Colors
```css
/* Primary - Mystical Gold */
--color-primary-400: #fbbf24;  /* Main brand */
--color-primary-500: #f59e0b;  /* Hover states */
--color-primary-600: #d97706;  /* Active states */

/* Dark/Cosmic */
--color-dark-100: #181825;     /* Card backgrounds */
--color-dark-500: #0a0a0f;     /* Page background */

/* Mystical Accents */
--color-mystical-purple: #6366f1;  /* Interactive elements */
--color-mystical-silver: #e5e7eb;  /* Primary text */
```

### Typography
```css
/* Fonts */
--font-mystical: 'Cinzel', serif;    /* Headers */
--font-body: 'Inter', sans-serif;    /* Body text */

/* Sizes */
--font-size-xs: 0.75rem;   /* 12px */
--font-size-base: 1rem;    /* 16px */
--font-size-4xl: 2.25rem;  /* 36px */
```

### Spacing
```css
--space-2: 0.5rem;    /* 8px */
--space-4: 1rem;      /* 16px - Base unit */
--space-8: 2rem;      /* 32px */
```

## 🧪 Testing

### Visual Testing
- Component screenshots in different themes
- Responsive behavior validation
- Cross-browser compatibility testing

### Accessibility Testing  
- Screen reader navigation
- Keyboard-only interaction
- Color contrast validation
- WCAG 2.1 compliance checking

### Performance Testing
- Bundle size optimization
- Animation performance
- Mobile device testing

## 🤝 Contributing

### Design Contributions
1. Follow the established mystical aesthetic
2. Maintain accessibility standards
3. Test across all supported platforms
4. Update documentation with changes

### Development Guidelines
1. Use TypeScript for all new components
2. Follow existing naming conventions
3. Include comprehensive prop types
4. Add JSDoc documentation

### Review Process
1. **Design Review**: Visual consistency and brand alignment
2. **Code Review**: Technical implementation and performance
3. **UX Review**: Usability and accessibility validation
4. **Testing**: Cross-platform functionality verification

## 📞 Support

- 📧 **Email**: design-system@astroloh.com
- 💬 **Discord**: [Astroloh Community](https://discord.gg/astroloh)
- 🐛 **Issues**: [GitHub Issues](https://github.com/evgenygurin/astroloh/issues)
- 📖 **Wiki**: [Design System Wiki](https://github.com/evgenygurin/astroloh/wiki)

## 📈 Roadmap

### Version 1.1 (Q1 2025)
- [ ] Advanced chart animations
- [ ] Dark/light theme switching
- [ ] Additional astrological symbols
- [ ] Performance optimizations

### Version 1.2 (Q2 2025) 
- [ ] Figma design kit
- [ ] Storybook component library
- [ ] Advanced accessibility features
- [ ] Mobile app components

### Version 2.0 (Q3 2025)
- [ ] 3D chart visualizations
- [ ] AR constellation overlays
- [ ] Voice UI enhancements
- [ ] AI-powered personalization

## 📄 License

The Astroloh Design System is licensed under the MIT License. See [LICENSE](./LICENSE) for full details.

---

**Created with ✨ by the Astroloh team**  
*Bringing the cosmos to your fingertips through thoughtful design*