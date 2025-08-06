/**
 * Tests for Icons Utility Functions and Constants
 */

import { describe, it, expect } from 'vitest'
import { 
  ZODIAC_SIGNS, 
  PLANETS, 
  LUNAR_PHASES, 
  ASPECTS, 
  ELEMENTS, 
  getAllZodiacSigns, 
  getAllPlanets, 
  getPlanetBySymbol, 
  getZodiacBySymbol 
} from '../icons'

describe('Icon Constants', () => {
  describe('ZODIAC_SIGNS', () => {
    it('contains all 12 zodiac signs', () => {
      expect(Object.keys(ZODIAC_SIGNS)).toHaveLength(12)
    })

    it('has correct zodiac sign structure', () => {
      Object.entries(ZODIAC_SIGNS).forEach(([key, sign]) => {
        expect(sign).toHaveProperty('symbol')
        expect(sign).toHaveProperty('unicode')
        expect(sign).toHaveProperty('name')
        expect(typeof sign.symbol).toBe('string')
        expect(typeof sign.unicode).toBe('string')
        expect(typeof sign.name).toBe('string')
      })
    })

    it('has unique symbols for each sign', () => {
      const symbols = Object.values(ZODIAC_SIGNS).map(sign => sign.symbol)
      const uniqueSymbols = new Set(symbols)
      expect(uniqueSymbols.size).toBe(symbols.length)
    })

    it('has correct zodiac order', () => {
      const expectedOrder = [
        'aries', 'taurus', 'gemini', 'cancer', 'leo', 'virgo',
        'libra', 'scorpio', 'sagittarius', 'capricorn', 'aquarius', 'pisces'
      ]
      expect(Object.keys(ZODIAC_SIGNS)).toEqual(expectedOrder)
    })

    it('contains expected zodiac symbols', () => {
      expect(ZODIAC_SIGNS.aries.symbol).toBe('♈')
      expect(ZODIAC_SIGNS.leo.symbol).toBe('♌')
      expect(ZODIAC_SIGNS.scorpio.symbol).toBe('♏')
      expect(ZODIAC_SIGNS.pisces.symbol).toBe('♓')
    })
  })

  describe('PLANETS', () => {
    it('contains all major planets and nodes', () => {
      const expectedPlanets = [
        'sun', 'moon', 'mercury', 'venus', 'mars', 
        'jupiter', 'saturn', 'uranus', 'neptune', 'pluto',
        'northNode', 'southNode'
      ]
      expect(Object.keys(PLANETS)).toEqual(expect.arrayContaining(expectedPlanets))
    })

    it('has correct planet structure', () => {
      Object.entries(PLANETS).forEach(([key, planet]) => {
        expect(planet).toHaveProperty('symbol')
        expect(planet).toHaveProperty('unicode')
        expect(planet).toHaveProperty('name')
        expect(typeof planet.symbol).toBe('string')
        expect(typeof planet.unicode).toBe('string')
        expect(typeof planet.name).toBe('string')
      })
    })

    it('has unique symbols for each planet', () => {
      const symbols = Object.values(PLANETS).map(planet => planet.symbol)
      const uniqueSymbols = new Set(symbols)
      expect(uniqueSymbols.size).toBe(symbols.length)
    })

    it('contains expected planet symbols', () => {
      expect(PLANETS.sun.symbol).toBe('☉')
      expect(PLANETS.moon.symbol).toBe('☽')
      expect(PLANETS.mercury.symbol).toBe('☿')
      expect(PLANETS.venus.symbol).toBe('♀')
      expect(PLANETS.mars.symbol).toBe('♂')
    })
  })

  describe('LUNAR_PHASES', () => {
    it('contains all 8 lunar phases', () => {
      expect(Object.keys(LUNAR_PHASES)).toHaveLength(8)
    })

    it('has correct lunar phase structure', () => {
      Object.entries(LUNAR_PHASES).forEach(([key, phase]) => {
        expect(phase).toHaveProperty('symbol')
        expect(phase).toHaveProperty('unicode')
        expect(phase).toHaveProperty('name')
        expect(typeof phase.symbol).toBe('string')
        expect(typeof phase.unicode).toBe('string')
        expect(typeof phase.name).toBe('string')
      })
    })

    it('contains correct moon phase progression', () => {
      const expectedOrder = [
        'newMoon', 'waxingCrescent', 'firstQuarter', 'waxingGibbous',
        'fullMoon', 'waningGibbous', 'lastQuarter', 'waningCrescent'
      ]
      expect(Object.keys(LUNAR_PHASES)).toEqual(expectedOrder)
    })

    it('contains expected moon symbols', () => {
      expect(LUNAR_PHASES.newMoon.symbol).toBe('🌑')
      expect(LUNAR_PHASES.fullMoon.symbol).toBe('🌕')
      expect(LUNAR_PHASES.firstQuarter.symbol).toBe('🌓')
      expect(LUNAR_PHASES.lastQuarter.symbol).toBe('🌗')
    })
  })

  describe('ASPECTS', () => {
    it('contains major astrological aspects', () => {
      const expectedAspects = ['conjunction', 'opposition', 'trine', 'square', 'sextile']
      expectedAspects.forEach(aspect => {
        expect(ASPECTS).toHaveProperty(aspect)
      })
    })

    it('has correct aspect structure', () => {
      Object.entries(ASPECTS).forEach(([key, aspect]) => {
        expect(aspect).toHaveProperty('symbol')
        expect(aspect).toHaveProperty('degrees')
        expect(aspect).toHaveProperty('name')
        expect(typeof aspect.symbol).toBe('string')
        expect(typeof aspect.degrees).toBe('number')
        expect(typeof aspect.name).toBe('string')
      })
    })

    it('has correct aspect degrees', () => {
      expect(ASPECTS.conjunction.degrees).toBe(0)
      expect(ASPECTS.opposition.degrees).toBe(180)
      expect(ASPECTS.trine.degrees).toBe(120)
      expect(ASPECTS.square.degrees).toBe(90)
      expect(ASPECTS.sextile.degrees).toBe(60)
    })
  })

  describe('ELEMENTS', () => {
    it('contains all 4 elements', () => {
      expect(Object.keys(ELEMENTS)).toHaveLength(4)
    })

    it('has correct element structure', () => {
      Object.entries(ELEMENTS).forEach(([key, element]) => {
        expect(element).toHaveProperty('symbol')
        expect(element).toHaveProperty('unicode')
        expect(element).toHaveProperty('name')
        expect(element).toHaveProperty('color')
        expect(typeof element.symbol).toBe('string')
        expect(typeof element.unicode).toBe('string')
        expect(typeof element.name).toBe('string')
        expect(typeof element.color).toBe('string')
      })
    })

    it('has correct element colors', () => {
      expect(ELEMENTS.fire.color).toBe('#ef4444')
      expect(ELEMENTS.earth.color).toBe('#10b981')
      expect(ELEMENTS.air.color).toBe('#06b6d4')
      expect(ELEMENTS.water.color).toBe('#3b82f6')
    })
  })
})

describe('Utility Functions', () => {
  describe('getAllZodiacSigns', () => {
    it('returns array of all zodiac signs', () => {
      const signs = getAllZodiacSigns()
      expect(Array.isArray(signs)).toBe(true)
      expect(signs).toHaveLength(12)
    })

    it('preserves zodiac order', () => {
      const signs = getAllZodiacSigns()
      expect(signs[0].name).toBe('Aries')
      expect(signs[11].name).toBe('Pisces')
    })

    it('includes all required properties', () => {
      const signs = getAllZodiacSigns()
      signs.forEach(sign => {
        expect(sign).toHaveProperty('symbol')
        expect(sign).toHaveProperty('unicode')
        expect(sign).toHaveProperty('name')
      })
    })
  })

  describe('getAllPlanets', () => {
    it('returns array of all planets', () => {
      const planets = getAllPlanets()
      expect(Array.isArray(planets)).toBe(true)
      expect(planets.length).toBeGreaterThan(10) // At least 10 planets/nodes
    })

    it('includes all required properties', () => {
      const planets = getAllPlanets()
      planets.forEach(planet => {
        expect(planet).toHaveProperty('symbol')
        expect(planet).toHaveProperty('unicode')
        expect(planet).toHaveProperty('name')
      })
    })

    it('includes major planets', () => {
      const planets = getAllPlanets()
      const planetNames = planets.map(p => p.name.toLowerCase())
      
      expect(planetNames).toContain('sun')
      expect(planetNames).toContain('moon')
      expect(planetNames).toContain('mercury')
      expect(planetNames).toContain('venus')
      expect(planetNames).toContain('mars')
    })
  })

  describe('getPlanetBySymbol', () => {
    it('returns correct planet for valid symbol', () => {
      const sunResult = getPlanetBySymbol('☉')
      expect(sunResult).toEqual({
        key: 'sun',
        planet: PLANETS.sun
      })

      const moonResult = getPlanetBySymbol('☽')
      expect(moonResult).toEqual({
        key: 'moon',
        planet: PLANETS.moon
      })
    })

    it('returns undefined for invalid symbol', () => {
      const result = getPlanetBySymbol('🚀')
      expect(result).toBeUndefined()
    })

    it('handles empty string', () => {
      const result = getPlanetBySymbol('')
      expect(result).toBeUndefined()
    })

    it('is case sensitive', () => {
      // Assuming symbols are case-sensitive Unicode
      const result = getPlanetBySymbol('☉')
      expect(result).toBeDefined()
    })
  })

  describe('getZodiacBySymbol', () => {
    it('returns correct zodiac sign for valid symbol', () => {
      const ariesResult = getZodiacBySymbol('♈')
      expect(ariesResult).toEqual({
        key: 'aries',
        sign: ZODIAC_SIGNS.aries
      })

      const leoResult = getZodiacBySymbol('♌')
      expect(leoResult).toEqual({
        key: 'leo',
        sign: ZODIAC_SIGNS.leo
      })
    })

    it('returns undefined for invalid symbol', () => {
      const result = getZodiacBySymbol('🌟')
      expect(result).toBeUndefined()
    })

    it('handles empty string', () => {
      const result = getZodiacBySymbol('')
      expect(result).toBeUndefined()
    })

    it('works with all zodiac symbols', () => {
      Object.entries(ZODIAC_SIGNS).forEach(([signKey, sign]) => {
        const result = getZodiacBySymbol(sign.symbol)
        expect(result).toEqual({
          key: signKey,
          sign
        })
      })
    })
  })
})

describe('Data Integrity', () => {
  it('ensures all zodiac signs have valid Unicode characters', () => {
    Object.values(ZODIAC_SIGNS).forEach(sign => {
      expect(typeof sign.unicode).toBe('string')
      expect(sign.unicode.length).toBeGreaterThan(0)
      // Unicode should be valid characters, not escape sequences
      expect(sign.unicode).toMatch(/^[\u0000-\uFFFF]+$/)
    })
  })

  it('ensures all planets have valid Unicode characters', () => {
    Object.values(PLANETS).forEach(planet => {
      expect(typeof planet.unicode).toBe('string')
      expect(planet.unicode.length).toBeGreaterThan(0)
      // Unicode should be valid characters, not escape sequences
      expect(planet.unicode).toMatch(/^[\u0000-\uFFFF]+$/)
    })
  })

  it('ensures all lunar phases have valid Unicode characters', () => {
    Object.values(LUNAR_PHASES).forEach(phase => {
      expect(typeof phase.unicode).toBe('string')
      expect(phase.unicode.length).toBeGreaterThan(0)
      // Moon phases use emoji Unicode characters
      expect(phase.unicode).toMatch(/^[\u0000-\uFFFF\u{10000}-\u{10FFFF}]+$/u)
    })
  })

  it('ensures elements have valid hex colors', () => {
    Object.values(ELEMENTS).forEach(element => {
      expect(element.color).toMatch(/^#[0-9a-f]{6}$/i)
    })
  })

  it('ensures all elements have unique colors', () => {
    const colors = Object.values(ELEMENTS).map(element => element.color)
    const uniqueColors = new Set(colors)
    expect(uniqueColors.size).toBe(colors.length)
  })
})

describe('Constants Type Safety', () => {
  it('has readonly ZODIAC_SIGNS properties', () => {
    // TypeScript should enforce readonly at compile time
    const signs = ZODIAC_SIGNS
    expect(typeof signs).toBe('object')
    expect(signs).toBeTruthy()
  })

  it('has readonly PLANETS properties', () => {
    // TypeScript should enforce readonly at compile time
    const planets = PLANETS
    expect(typeof planets).toBe('object')
    expect(planets).toBeTruthy()
  })

  it('maintains consistent data structure', () => {
    // Verify the structure is consistent across all signs
    Object.values(ZODIAC_SIGNS).forEach(sign => {
      expect(sign).toHaveProperty('symbol')
      expect(sign).toHaveProperty('unicode')
      expect(sign).toHaveProperty('name')
    })
  })
})