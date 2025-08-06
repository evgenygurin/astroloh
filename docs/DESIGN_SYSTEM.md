# Astroloh Design System

## Overview

The Astroloh Design System is a comprehensive UI/UX framework designed specifically for astrological applications. It provides a cohesive visual language that embodies mystical and cosmic themes while maintaining accessibility and usability across multiple platforms.

## Design Philosophy

### Core Principles
- **Mystical & Cosmic**: Dark themes with golden accents reflecting the night sky and celestial bodies
- **Accessible**: WCAG 2.1 AA compliant with high contrast and keyboard navigation
- **Platform Agnostic**: Adaptive design that works across web, mobile, voice, and messaging platforms
- **Astrologically Authentic**: Uses proper astrological symbols and follows traditional conventions

### Visual Identity
- **Primary Colors**: Mystical gold (#fbbf24) representing celestial illumination
- **Background**: Deep cosmic colors (#1e1b4b to #0a0a0f) representing the night sky
- **Accent Colors**: Mystical purple (#6366f1) for interactive elements
- **Typography**: Cinzel for headers (mystical feel), Inter for body text (readability)

## Design Tokens

### Color Palette

```css
/* Primary Colors - Mystical Gold */
--color-primary-400: #fbbf24;  /* Main brand color */
--color-primary-500: #f59e0b;  /* Hover states */
--color-primary-600: #d97706;  /* Active states */

/* Dark/Cosmic Colors */
--color-dark-100: #181825;     /* Card backgrounds */
--color-dark-200: #11111b;     /* Input backgrounds */
--color-dark-500: #0a0a0f;     /* Page background */

/* Mystical Colors */
--color-mystical-purple: #6366f1;  /* Interactive elements */
--color-mystical-silver: #e5e7eb;  /* Primary text */
--color-mystical-cosmic: #1e1b4b;  /* Gradient starts */
```

### Typography Scale

```css
/* Font Families */
--font-mystical: 'Cinzel', serif;      /* Headers and mystical text */
--font-body: 'Inter', sans-serif;      /* Body text and UI */

/* Font Sizes */
--font-size-xs: 0.75rem;    /* 12px - Small labels */
--font-size-sm: 0.875rem;   /* 14px - UI text */
--font-size-base: 1rem;     /* 16px - Body text */
--font-size-xl: 1.25rem;    /* 20px - Subheadings */
--font-size-4xl: 2.25rem;   /* 36px - Main headings */
```

### Spacing System

```css
/* Based on 0.25rem (4px) scale */
--space-1: 0.25rem;   /* 4px */
--space-2: 0.5rem;    /* 8px */
--space-4: 1rem;      /* 16px - Base unit */
--space-6: 1.5rem;    /* 24px */
--space-8: 2rem;      /* 32px */
```

## Components

### Cards

#### Astro Card
The foundation component for all content containers.

```html
<div class="astro-card">
  <h3 class="astro-heading astro-heading--4">Title</h3>
  <p class="astro-text">Content goes here...</p>
</div>
```

**Variants:**
- `astro-card--elevated`: Higher shadow for important content
- `astro-card--compact`: Reduced padding for tight spaces

#### Planet Card
Specialized card for displaying planetary information.

```tsx
<PlanetCard
  planet="sun"
  sign="leo"
  house={1}
  degree={15}
  influence={{
    love: 85,
    career: 70,
    health: 90,
    money: 65
  }}
  size="medium"
/>
```

### Charts

#### Natal Chart
Interactive circular chart for birth chart visualization.

```tsx
<NatalChart
  planets={planetPositions}
  aspects={aspectData}
  size="large"
  interactive={true}
  showAspects={true}
/>
```

#### Lunar Calendar
Calendar component with lunar phases and astrological events.

```tsx
<LunarCalendar
  events={lunarEvents}
  selectedDate={selectedDate}
  onDateSelect={handleDateSelect}
  size="normal"
/>
```

### Interactive Elements

#### Buttons

```html
<!-- Primary button -->
<button class="astro-button astro-button--primary">
  Get Reading
</button>

<!-- Secondary button -->
<button class="astro-button astro-button--secondary">
  Learn More
</button>

<!-- Ghost button -->
<button class="astro-button astro-button--ghost">
  Cancel
</button>
```

#### Form Elements

```html
<!-- Input field -->
<label class="astro-label">Birth Date</label>
<input type="date" class="astro-input" placeholder="Enter your birth date">

<!-- Select dropdown -->
<select class="astro-select">
  <option>Choose your zodiac sign</option>
  <option value="aries">♈ Aries</option>
</select>
```

### Progress Indicators

```html
<!-- Compatibility progress -->
<div class="astro-progress">
  <div class="astro-progress__bar astro-progress__bar--compatibility" style="width: 75%">
    <div class="astro-progress__shimmer"></div>
  </div>
</div>
```

## Astrological Elements

### Symbols and Icons

The design system includes comprehensive astrological symbol sets:

```typescript
import { ZODIAC_SIGNS, PLANETS, LUNAR_PHASES, ASPECTS } from './design-system/icons';

// Usage examples
const ariesSymbol = ZODIAC_SIGNS.aries.symbol; // ♈
const sunSymbol = PLANETS.sun.symbol;          // ☉
const fullMoon = LUNAR_PHASES.fullMoon.symbol; // 🌕
```

### Color Coding

- **Fire Signs**: Red tones (#ef4444)
- **Earth Signs**: Green tones (#10b981)  
- **Air Signs**: Blue tones (#06b6d4)
- **Water Signs**: Deep blue tones (#3b82f6)

## Platform Adaptations

### Web Interface
- Full desktop experience with sidebar navigation
- Grid-based layouts for dashboards
- Interactive charts and detailed information panels

### Mobile Applications
- Touch-optimized with 44px minimum touch targets
- Bottom navigation for thumb accessibility
- Simplified single-column layouts

### Yandex Alice (Voice)
- High contrast cards for voice UI companion
- Large text and clear visual hierarchy
- Rich content cards for horoscope delivery

### Telegram Bot
- Compact design for messaging context
- Inline keyboards for interaction
- 300px maximum width for readability

## UX Guidelines

### User Journey

1. **Discovery**: User learns about astrology features
2. **Onboarding**: Birth data collection with clear privacy messaging
3. **Core Experience**: Daily horoscopes, natal chart exploration
4. **Engagement**: Regular insights, compatibility readings
5. **Growth**: Advanced features, detailed consultations

### Interaction Patterns

#### Information Hierarchy
1. **Primary**: Main horoscope content, zodiac sign
2. **Secondary**: Planetary influences, aspects
3. **Tertiary**: Dates, technical details, fine print

#### Progressive Disclosure
- Start with essential information
- Provide "Learn More" options for deeper content
- Use expandable sections for advanced features

#### Feedback & States
- **Loading**: Shimmer effects and cosmic animations
- **Success**: Golden glow and positive messaging
- **Errors**: Gentle red highlights with helpful guidance
- **Empty States**: Mystical imagery with encouraging calls-to-action

### Accessibility

#### Color & Contrast
- Minimum 4.5:1 contrast ratio for normal text
- Minimum 3:1 contrast ratio for large text
- Never rely solely on color to convey information

#### Keyboard Navigation
- All interactive elements are keyboard accessible
- Clear focus indicators with golden outline
- Logical tab order through content

#### Screen Readers
- Semantic HTML structure
- ARIA labels for complex widgets
- Alt text for all astrological symbols

#### Responsive Design
- Mobile-first approach
- Flexible layouts that adapt to screen size
- Touch targets minimum 44px for mobile

### Animation & Motion

#### Principles
- **Subtle**: Enhance without overwhelming
- **Purposeful**: Guide attention and provide feedback
- **Respectful**: Honor reduced motion preferences

#### Common Animations
- **Hover**: Gentle scale (1.02x) and glow effects
- **Loading**: Shimmer effects and particle floating
- **Transitions**: 200-300ms ease-in-out for most interactions
- **Planet Orbits**: Slow rotation (20s) for background elements

## Implementation Guidelines

### CSS Architecture

```
src/design-system/
├── tokens.css          # Design tokens and CSS variables
├── components.css      # Component styles
├── typography.css      # Text styles and font imports
├── platform-styles.css # Platform-specific adaptations
└── icons.ts           # Astrological symbols and SVGs
```

### React Components

```
src/components/design-system/
├── NatalChart.tsx      # Interactive birth chart
├── PlanetCard.tsx      # Planet information display
├── LunarCalendar.tsx   # Lunar phase calendar
└── index.ts           # Component exports
```

### Usage in Applications

```typescript
// Import design system styles
import './design-system/tokens.css';
import './design-system/components.css';
import './design-system/typography.css';
import './design-system/platform-styles.css';

// Use platform classes
<div className="platform-web">
  <div className="web-dashboard-grid">
    <PlanetCard planet="sun" size="medium" />
    <NatalChart planets={planets} />
  </div>
</div>
```

## Testing & Quality Assurance

### Visual Regression Testing
- Test all components in different themes
- Verify responsive behavior at breakpoints
- Check accessibility with screen readers

### Browser Support
- Modern browsers (Chrome, Firefox, Safari, Edge)
- iOS Safari 12+
- Android Chrome 80+

### Performance
- Lazy load heavy components (charts, animations)
- Optimize images and SVGs
- Use CSS-in-JS sparingly for better performance

## Maintenance & Evolution

### Versioning
- Follow semantic versioning for design tokens
- Document breaking changes in component APIs
- Provide migration guides for major updates

### Contribution Guidelines
- All new components must include accessibility testing
- Follow established naming conventions
- Include usage examples and documentation

### Review Process
- Design review for visual consistency
- Code review for technical implementation
- UX review for usability and accessibility

---

**Last Updated**: August 2025
**Version**: 1.0.0
**Maintainers**: Astroloh Design Team