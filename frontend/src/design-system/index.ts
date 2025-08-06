/**
 * Astroloh Design System - Main Entry Point
 * Exports all design system components, utilities, and constants
 */

// Design tokens and icons
export * from './icons';

// React Components
export { default as NatalChart } from '../components/design-system/NatalChart';
export { default as PlanetCard } from '../components/design-system/PlanetCard';  
export { default as LunarCalendar } from '../components/design-system/LunarCalendar';

// Type definitions for components
export type { 
  ZodiacSign, 
  Planet, 
  LunarPhase, 
  Aspect, 
  Element, 
  Quality, 
  House 
} from './icons';

// CSS classes for common patterns (as constants for consistency)
export const DESIGN_CLASSES = {
  // Cards
  CARD: 'astro-card',
  CARD_ELEVATED: 'astro-card astro-card--elevated',
  CARD_COMPACT: 'astro-card astro-card--compact',

  // Typography
  HEADING_1: 'astro-heading astro-heading--1',
  HEADING_2: 'astro-heading astro-heading--2', 
  HEADING_3: 'astro-heading astro-heading--3',
  HEADING_4: 'astro-heading astro-heading--4',
  HEADING_5: 'astro-heading astro-heading--5',
  HEADING_6: 'astro-heading astro-heading--6',
  
  BODY: 'astro-body astro-body--base',
  BODY_LARGE: 'astro-body astro-body--large',
  BODY_SMALL: 'astro-body astro-body--small',
  
  TEXT_MYSTICAL: 'astro-text--mystical',
  TEXT_SECONDARY: 'astro-text--secondary',
  TEXT_MUTED: 'astro-text--muted',
  TEXT_ACCENT: 'astro-text--accent',
  TEXT_GLOW: 'astro-text--glow',
  TEXT_GRADIENT: 'astro-text--gradient',

  // Buttons
  BUTTON_PRIMARY: 'astro-button astro-button--primary',
  BUTTON_SECONDARY: 'astro-button astro-button--secondary',
  BUTTON_GHOST: 'astro-button astro-button--ghost',

  // Form Elements
  INPUT: 'astro-input',
  LABEL: 'astro-label',
  SELECT: 'astro-select',

  // Progress
  PROGRESS: 'astro-progress',
  PROGRESS_COMPATIBILITY: 'astro-progress__bar astro-progress__bar--compatibility',
  PROGRESS_INFLUENCE: 'astro-progress__bar astro-progress__bar--influence',
  PROGRESS_ENERGY: 'astro-progress__bar astro-progress__bar--energy',

  // Modal
  MODAL_OVERLAY: 'astro-modal-overlay',
  MODAL: 'astro-modal',
  MODAL_HEADER: 'astro-modal__header',
  MODAL_TITLE: 'astro-modal__title',
  MODAL_CLOSE: 'astro-modal__close',

  // Symbols
  ZODIAC_SYMBOL: 'zodiac-symbol',
  PLANET_SYMBOL: 'astro-symbol astro-symbol--planet',

  // Platform specific
  PLATFORM_WEB: 'platform-web',
  PLATFORM_MOBILE: 'platform-mobile',
  PLATFORM_TELEGRAM: 'platform-telegram',
  PLATFORM_YANDEX: 'platform-yandex',

  // Layouts
  WEB_DASHBOARD_GRID: 'web-dashboard-grid',
  WEB_CHART_SECTION: 'web-chart-section',
  WEB_PLANET_GRID: 'web-planet-grid',
  MOBILE_SINGLE_COLUMN: 'mobile-single-column',
  MOBILE_CHART_CONTAINER: 'mobile-chart-container'
} as const;

// Animation utilities
export const ANIMATIONS = {
  DURATION: {
    FAST: 150,
    NORMAL: 200,
    SLOW: 300,
    VERY_SLOW: 500
  },
  EASING: {
    LINEAR: 'linear',
    EASE_IN: 'cubic-bezier(0.4, 0, 1, 1)',
    EASE_OUT: 'cubic-bezier(0, 0, 0.2, 1)', 
    EASE_IN_OUT: 'cubic-bezier(0.4, 0, 0.2, 1)'
  }
} as const;

// Breakpoints for responsive design
export const BREAKPOINTS = {
  MOBILE: 640,
  TABLET: 768,
  DESKTOP: 1024,
  LARGE: 1280,
  XLARGE: 1536
} as const;

// Design system utility functions
export const designUtils = {
  /**
   * Get responsive class based on screen size
   */
  getResponsiveClass: (baseClass: string, size: 'mobile' | 'tablet' | 'desktop') => {
    const prefixes = {
      mobile: 'sm:',
      tablet: 'md:',
      desktop: 'lg:'
    };
    return `${prefixes[size]}${baseClass}`;
  },

  /**
   * Combine platform and component classes
   */
  combineClasses: (platform: 'web' | 'mobile' | 'telegram' | 'yandex', componentClasses: string) => {
    const platformClass = DESIGN_CLASSES[`PLATFORM_${platform.toUpperCase()}` as keyof typeof DESIGN_CLASSES];
    return `${platformClass} ${componentClasses}`;
  },

  /**
   * Get element color for astrological elements
   */
  getElementColor: (element: Element) => {
    const colors = {
      fire: '#ef4444',
      earth: '#10b981',
      air: '#06b6d4',
      water: '#3b82f6'
    };
    return colors[element];
  },

  /**
   * Get planet color for visualization
   */
  getPlanetColor: (planet: Planet) => {
    const colors = {
      sun: '#f59e0b',
      moon: '#e5e7eb',
      mercury: '#06b6d4',
      venus: '#10b981',
      mars: '#ef4444',
      jupiter: '#8b5cf6',
      saturn: '#6b7280',
      uranus: '#3b82f6',
      neptune: '#1e40af',
      pluto: '#7c2d12',
      northNode: '#a855f7',
      southNode: '#9333ea'
    };
    return colors[planet];
  }
};

// Theme configuration
export const THEME_CONFIG = {
  colors: {
    primary: {
      50: '#fefce8',
      100: '#fef3c7', 
      200: '#fde68a',
      300: '#fcd34d',
      400: '#fbbf24',
      500: '#f59e0b',
      600: '#d97706',
      700: '#b45309',
      800: '#92400e',
      900: '#78350f'
    },
    dark: {
      50: '#1e1e2e',
      100: '#181825',
      200: '#11111b',
      300: '#0f0f19',
      400: '#0d0d14',
      500: '#0a0a0f',
      600: '#08080c',
      700: '#06060a',
      800: '#040407',
      900: '#020204'
    },
    mystical: {
      purple: '#6366f1',
      gold: '#fbbf24',
      silver: '#e5e7eb',
      cosmic: '#1e1b4b'
    }
  },
  fonts: {
    mystical: ['Cinzel', 'Times New Roman', 'serif'],
    body: ['Inter', 'Helvetica Neue', 'sans-serif'],
    mono: ['JetBrains Mono', 'Courier New', 'monospace']
  },
  spacing: {
    xs: '0.25rem',
    sm: '0.5rem', 
    md: '1rem',
    lg: '1.5rem',
    xl: '2rem',
    '2xl': '3rem',
    '3xl': '4rem'
  },
  shadows: {
    mystical: '0 10px 25px -5px rgba(251, 191, 36, 0.2), 0 10px 10px -5px rgba(99, 102, 241, 0.1)',
    goldGlow: '0 0 20px rgba(251, 191, 36, 0.4)',
    purpleGlow: '0 0 20px rgba(99, 102, 241, 0.4)'
  }
} as const;

// Export version info for compatibility checking
export const DESIGN_SYSTEM_VERSION = '1.0.0';

// Default export with everything bundled
const AstrolohDesignSystem = {
  DESIGN_CLASSES,
  ANIMATIONS,
  BREAKPOINTS,
  THEME_CONFIG,
  designUtils,
  version: DESIGN_SYSTEM_VERSION
};

export default AstrolohDesignSystem;