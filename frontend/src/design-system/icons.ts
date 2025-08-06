/**
 * Astroloh Design System - Astrological Icons
 * Unicode symbols and SVG icons for astrological elements
 */

// Zodiac Signs
export const ZODIAC_SIGNS = {
  aries: { symbol: '♈', unicode: '\u2648', name: 'Aries' },
  taurus: { symbol: '♉', unicode: '\u2649', name: 'Taurus' },
  gemini: { symbol: '♊', unicode: '\u264A', name: 'Gemini' },
  cancer: { symbol: '♋', unicode: '\u264B', name: 'Cancer' },
  leo: { symbol: '♌', unicode: '\u264C', name: 'Leo' },
  virgo: { symbol: '♍', unicode: '\u264D', name: 'Virgo' },
  libra: { symbol: '♎', unicode: '\u264E', name: 'Libra' },
  scorpio: { symbol: '♏', unicode: '\u264F', name: 'Scorpio' },
  sagittarius: { symbol: '♐', unicode: '\u2650', name: 'Sagittarius' },
  capricorn: { symbol: '♑', unicode: '\u2651', name: 'Capricorn' },
  aquarius: { symbol: '♒', unicode: '\u2652', name: 'Aquarius' },
  pisces: { symbol: '♓', unicode: '\u2653', name: 'Pisces' }
} as const;

// Planets
export const PLANETS = {
  sun: { symbol: '☉', unicode: '\u2609', name: 'Sun' },
  moon: { symbol: '☽', unicode: '\u263D', name: 'Moon' },
  mercury: { symbol: '☿', unicode: '\u263F', name: 'Mercury' },
  venus: { symbol: '♀', unicode: '\u2640', name: 'Venus' },
  mars: { symbol: '♂', unicode: '\u2642', name: 'Mars' },
  jupiter: { symbol: '♃', unicode: '\u2643', name: 'Jupiter' },
  saturn: { symbol: '♄', unicode: '\u2644', name: 'Saturn' },
  uranus: { symbol: '♅', unicode: '\u2645', name: 'Uranus' },
  neptune: { symbol: '♆', unicode: '\u2646', name: 'Neptune' },
  pluto: { symbol: '♇', unicode: '\u2647', name: 'Pluto' },
  northNode: { symbol: '☊', unicode: '\u260A', name: 'North Node' },
  southNode: { symbol: '☋', unicode: '\u260B', name: 'South Node' }
} as const;

// Lunar Phases
export const LUNAR_PHASES = {
  newMoon: { symbol: '🌑', unicode: '\u1F311', name: 'New Moon' },
  waxingCrescent: { symbol: '🌒', unicode: '\u1F312', name: 'Waxing Crescent' },
  firstQuarter: { symbol: '🌓', unicode: '\u1F313', name: 'First Quarter' },
  waxingGibbous: { symbol: '🌔', unicode: '\u1F314', name: 'Waxing Gibbous' },
  fullMoon: { symbol: '🌕', unicode: '\u1F315', name: 'Full Moon' },
  waningGibbous: { symbol: '🌖', unicode: '\u1F316', name: 'Waning Gibbous' },
  lastQuarter: { symbol: '🌗', unicode: '\u1F317', name: 'Last Quarter' },
  waningCrescent: { symbol: '🌘', unicode: '\u1F318', name: 'Waning Crescent' }
} as const;

// Aspects
export const ASPECTS = {
  conjunction: { symbol: '☌', unicode: '\u260C', name: 'Conjunction', degrees: 0 },
  sextile: { symbol: '⚹', unicode: '\u26B9', name: 'Sextile', degrees: 60 },
  square: { symbol: '□', unicode: '\u25A1', name: 'Square', degrees: 90 },
  trine: { symbol: '△', unicode: '\u25B3', name: 'Trine', degrees: 120 },
  opposition: { symbol: '☍', unicode: '\u260D', name: 'Opposition', degrees: 180 },
  quincunx: { symbol: '⚻', unicode: '\u26BB', name: 'Quincunx', degrees: 150 },
  semisextile: { symbol: '⚺', unicode: '\u26BA', name: 'Semi-sextile', degrees: 30 },
  sesquiquadrate: { symbol: '⚼', unicode: '\u26BC', name: 'Sesquiquadrate', degrees: 135 }
} as const;

// Elements
export const ELEMENTS = {
  fire: { symbol: '🔥', unicode: '\u1F525', name: 'Fire', color: '#ef4444' },
  earth: { symbol: '🌍', unicode: '\u1F30D', name: 'Earth', color: '#10b981' },
  air: { symbol: '💨', unicode: '\u1F4A8', name: 'Air', color: '#06b6d4' },
  water: { symbol: '💧', unicode: '\u1F4A7', name: 'Water', color: '#3b82f6' }
} as const;

// Qualities
export const QUALITIES = {
  cardinal: { name: 'Cardinal', description: 'Initiative, Leadership' },
  fixed: { name: 'Fixed', description: 'Stability, Determination' },
  mutable: { name: 'Mutable', description: 'Adaptability, Flexibility' }
} as const;

// Houses
export const HOUSES = {
  1: { name: '1st House', area: 'Self, Identity, Appearance' },
  2: { name: '2nd House', area: 'Money, Possessions, Values' },
  3: { name: '3rd House', area: 'Communication, Siblings, Local Travel' },
  4: { name: '4th House', area: 'Home, Family, Roots' },
  5: { name: '5th House', area: 'Creativity, Romance, Children' },
  6: { name: '6th House', area: 'Health, Work, Service' },
  7: { name: '7th House', area: 'Partnerships, Marriage, Open Enemies' },
  8: { name: '8th House', area: 'Transformation, Shared Resources, Occult' },
  9: { name: '9th House', area: 'Higher Learning, Philosophy, Foreign Travel' },
  10: { name: '10th House', area: 'Career, Reputation, Public Image' },
  11: { name: '11th House', area: 'Friends, Groups, Hopes and Dreams' },
  12: { name: '12th House', area: 'Spirituality, Hidden Things, Subconscious' }
} as const;

// SVG Icons for complex symbols
export const SVG_ICONS = {
  natalChart: `
    <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
      <circle cx="100" cy="100" r="90" stroke="#fbbf24" stroke-width="2" fill="none"/>
      <circle cx="100" cy="100" r="70" stroke="#fbbf24" stroke-width="1" fill="none" opacity="0.5"/>
      <circle cx="100" cy="100" r="50" stroke="#fbbf24" stroke-width="1" fill="none" opacity="0.3"/>
      <line x1="10" y1="100" x2="190" y2="100" stroke="#6366f1" stroke-width="1" opacity="0.6"/>
      <line x1="100" y1="10" x2="100" y2="190" stroke="#6366f1" stroke-width="1" opacity="0.6"/>
      <line x1="29" y1="29" x2="171" y2="171" stroke="#6366f1" stroke-width="1" opacity="0.4"/>
      <line x1="171" y1="29" x2="29" y2="171" stroke="#6366f1" stroke-width="1" opacity="0.4"/>
    </svg>
  `,
  
  constellation: `
    <svg viewBox="0 0 100 100" xmlns="http://www.w3.org/2000/svg">
      <circle cx="20" cy="20" r="2" fill="#fbbf24"/>
      <circle cx="50" cy="15" r="2" fill="#fbbf24"/>
      <circle cx="80" cy="25" r="2" fill="#fbbf24"/>
      <circle cx="30" cy="50" r="2" fill="#fbbf24"/>
      <circle cx="70" cy="60" r="2" fill="#fbbf24"/>
      <circle cx="15" cy="80" r="2" fill="#fbbf24"/>
      <circle cx="85" cy="85" r="2" fill="#fbbf24"/>
      <line x1="20" y1="20" x2="50" y2="15" stroke="#6366f1" stroke-width="1" opacity="0.6"/>
      <line x1="50" y1="15" x2="80" y2="25" stroke="#6366f1" stroke-width="1" opacity="0.6"/>
      <line x1="20" y1="20" x2="30" y2="50" stroke="#6366f1" stroke-width="1" opacity="0.6"/>
      <line x1="80" y1="25" x2="70" y2="60" stroke="#6366f1" stroke-width="1" opacity="0.6"/>
      <line x1="30" y1="50" x2="15" y2="80" stroke="#6366f1" stroke-width="1" opacity="0.6"/>
      <line x1="70" y1="60" x2="85" y2="85" stroke="#6366f1" stroke-width="1" opacity="0.6"/>
    </svg>
  `,
  
  planetOrbit: `
    <svg viewBox="0 0 120 120" xmlns="http://www.w3.org/2000/svg">
      <circle cx="60" cy="60" r="50" stroke="#fbbf24" stroke-width="1" fill="none" opacity="0.3"/>
      <circle cx="60" cy="60" r="35" stroke="#fbbf24" stroke-width="1" fill="none" opacity="0.4"/>
      <circle cx="60" cy="60" r="20" stroke="#fbbf24" stroke-width="1" fill="none" opacity="0.5"/>
      <circle cx="60" cy="60" r="4" fill="#f59e0b"/>
      <circle cx="110" cy="60" r="3" fill="#6366f1">
        <animateTransform
          attributeName="transform"
          type="rotate"
          values="0 60 60;360 60 60"
          dur="10s"
          repeatCount="indefinite"/>
      </circle>
      <circle cx="95" cy="60" r="2" fill="#8b5cf6">
        <animateTransform
          attributeName="transform"
          type="rotate"
          values="0 60 60;360 60 60"
          dur="7s"
          repeatCount="indefinite"/>
      </circle>
    </svg>
  `,

  starField: `
    <svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">
      <defs>
        <radialGradient id="starGlow" cx="50%" cy="50%" r="50%">
          <stop offset="0%" stop-color="#fbbf24" stop-opacity="0.8"/>
          <stop offset="100%" stop-color="#fbbf24" stop-opacity="0"/>
        </radialGradient>
      </defs>
      <circle cx="30" cy="20" r="1" fill="url(#starGlow)"/>
      <circle cx="70" cy="35" r="1.5" fill="url(#starGlow)"/>
      <circle cx="120" cy="25" r="1" fill="url(#starGlow)"/>
      <circle cx="160" cy="40" r="1.2" fill="url(#starGlow)"/>
      <circle cx="40" cy="70" r="1.3" fill="url(#starGlow)"/>
      <circle cx="90" cy="80" r="1" fill="url(#starGlow)"/>
      <circle cx="140" cy="90" r="1.4" fill="url(#starGlow)"/>
      <circle cx="180" cy="75" r="1.1" fill="url(#starGlow)"/>
      <circle cx="25" cy="120" r="1.2" fill="url(#starGlow)"/>
      <circle cx="80" cy="140" r="1" fill="url(#starGlow)"/>
      <circle cx="130" cy="130" r="1.5" fill="url(#starGlow)"/>
      <circle cx="170" cy="150" r="1" fill="url(#starGlow)"/>
      <circle cx="50" cy="180" r="1.3" fill="url(#starGlow)"/>
      <circle cx="110" cy="170" r="1.1" fill="url(#starGlow)"/>
      <circle cx="150" cy="185" r="1" fill="url(#starGlow)"/>
    </svg>
  `
} as const;

// Helper functions
export const getZodiacSymbol = (sign: keyof typeof ZODIAC_SIGNS) => ZODIAC_SIGNS[sign];
export const getPlanetSymbol = (planet: keyof typeof PLANETS) => PLANETS[planet];
export const getLunarPhaseSymbol = (phase: keyof typeof LUNAR_PHASES) => LUNAR_PHASES[phase];
export const getAspectSymbol = (aspect: keyof typeof ASPECTS) => ASPECTS[aspect];
export const getElementInfo = (element: keyof typeof ELEMENTS) => ELEMENTS[element];
export const getHouseInfo = (house: keyof typeof HOUSES) => HOUSES[house];

// Generate all zodiac symbols as array
export const getAllZodiacSigns = () => Object.values(ZODIAC_SIGNS);

// Generate all planet symbols as array
export const getAllPlanets = () => Object.values(PLANETS);

// Generate all lunar phases as array
export const getAllLunarPhases = () => Object.values(LUNAR_PHASES);

// Reverse lookup functions
export const getPlanetBySymbol = (symbol: string) => {
  const entry = Object.entries(PLANETS).find(([_, planet]) => planet.symbol === symbol);
  return entry ? { key: entry[0] as Planet, planet: entry[1] } : undefined;
};

export const getZodiacBySymbol = (symbol: string) => {
  const entry = Object.entries(ZODIAC_SIGNS).find(([_, sign]) => sign.symbol === symbol);
  return entry ? { key: entry[0] as ZodiacSign, sign: entry[1] } : undefined;
};

// Type definitions
export type ZodiacSign = keyof typeof ZODIAC_SIGNS;
export type Planet = keyof typeof PLANETS;
export type LunarPhase = keyof typeof LUNAR_PHASES;
export type Aspect = keyof typeof ASPECTS;
export type Element = keyof typeof ELEMENTS;
export type Quality = keyof typeof QUALITIES;
export type House = keyof typeof HOUSES;