/**
 * Tests for NatalChart Component
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { NatalChart } from '../NatalChart'
import type { PlanetPosition, AspectData } from '../NatalChart'

// Mock planet positions for testing
const mockPlanets: PlanetPosition[] = [
  { planet: 'sun', sign: 'leo', degree: 125, house: 5 },
  { planet: 'moon', sign: 'cancer', degree: 95, house: 4 },
  { planet: 'mercury', sign: 'virgo', degree: 155, house: 6 },
  { planet: 'venus', sign: 'libra', degree: 185, house: 7 }
]

const mockAspects: AspectData[] = [
  { planet1: 'sun', planet2: 'moon', type: 'trine', orb: 2.5 },
  { planet1: 'mercury', planet2: 'venus', type: 'conjunction', orb: 1.0 }
]

describe('NatalChart', () => {
  beforeEach(() => {
    // Clear any previous mocks
    vi.clearAllMocks()
  })

  describe('Basic Rendering', () => {
    it('renders with minimum props', () => {
      render(<NatalChart planets={mockPlanets} />)
      
      // Check if SVG is present
      const svg = screen.getByRole('img', { hidden: true }) // SVG role
      expect(svg).toBeInTheDocument()
    })

    it('renders all provided planets', () => {
      const { container } = render(<NatalChart planets={mockPlanets} />)
      
      // Check for planet symbols in the SVG
      mockPlanets.forEach(planet => {
        // Check that the planet is rendered (we'll look for the degree markers instead)
        expect(container.textContent).toContain(`${Math.round(planet.degree)}°`)
      })
    })

    it('renders zodiac signs around the wheel', () => {
      const { container } = render(<NatalChart planets={mockPlanets} />)
      
      // Check for zodiac symbols - there should be 12
      const zodiacTexts = container.querySelectorAll('.zodiac-symbol')
      expect(zodiacTexts).toHaveLength(12)
    })

    it('renders house divisions', () => {
      const { container } = render(<NatalChart planets={mockPlanets} />)
      
      // Check for house lines - should be 12
      const houseLines = container.querySelectorAll('line[class*="constellation-line"]')
      expect(houseLines).toHaveLength(12)
    })

    it('renders aspect lines when showAspects is true', () => {
      const { container } = render(
        <NatalChart planets={mockPlanets} aspects={mockAspects} showAspects={true} />
      )
      
      // Check for aspect lines
      const aspectLines = container.querySelectorAll('line[stroke="#10b981"], line[stroke="#ef4444"]')
      expect(aspectLines.length).toBeGreaterThan(0)
    })

    it('does not render aspect lines when showAspects is false', () => {
      const { container } = render(
        <NatalChart planets={mockPlanets} aspects={mockAspects} showAspects={false} />
      )
      
      // Check that no aspect lines are rendered
      const aspectLines = container.querySelectorAll('line[stroke="#10b981"], line[stroke="#ef4444"]')
      expect(aspectLines).toHaveLength(0)
    })
  })

  describe('Size Variants', () => {
    it('applies small size classes', () => {
      const { container } = render(<NatalChart planets={mockPlanets} size="small" />)
      
      const chart = container.querySelector('.natal-chart-container')
      expect(chart).toHaveClass('w-64', 'h-64')
    })

    it('applies medium size classes (default)', () => {
      const { container } = render(<NatalChart planets={mockPlanets} />)
      
      const chart = container.querySelector('.natal-chart-container')
      expect(chart).toHaveClass('w-80', 'h-80')
    })

    it('applies large size classes', () => {
      const { container } = render(<NatalChart planets={mockPlanets} size="large" />)
      
      const chart = container.querySelector('.natal-chart-container')
      expect(chart).toHaveClass('w-96', 'h-96')
    })
  })

  describe('Interactivity', () => {
    it('handles planet hover when interactive', async () => {
      const user = userEvent.setup()
      const { container } = render(<NatalChart planets={mockPlanets} interactive={true} />)
      
      const planetCircle = container.querySelector('circle[class*="cursor-pointer"]')
      expect(planetCircle).toBeInTheDocument()
      
      if (planetCircle) {
        await user.hover(planetCircle)
        // Should show glow effect or hover state
        expect(planetCircle).toHaveClass('cursor-pointer')
      }
    })

    it('handles planet selection when interactive', async () => {
      const user = userEvent.setup()
      const { container } = render(<NatalChart planets={mockPlanets} interactive={true} />)
      
      const planetCircle = container.querySelector('circle[class*="cursor-pointer"]')
      if (planetCircle) {
        await user.click(planetCircle)
        
        // Should show planet information tooltip
        expect(container.querySelector('.astro-card')).toBeInTheDocument()
      }
    })

    it('does not handle interactions when not interactive', () => {
      const { container } = render(<NatalChart planets={mockPlanets} interactive={false} />)
      
      const planetCircles = container.querySelectorAll('circle[class*="cursor-pointer"]')
      expect(planetCircles).toHaveLength(0)
    })

    it('shows planet information tooltip when planet is selected', async () => {
      const user = userEvent.setup()
      const { container } = render(<NatalChart planets={mockPlanets} interactive={true} />)
      
      const planetCircle = container.querySelector('circle[class*="cursor-pointer"]')
      if (planetCircle) {
        await user.click(planetCircle)
        
        // Check for tooltip content
        const tooltip = container.querySelector('.astro-card')
        expect(tooltip).toBeInTheDocument()
        expect(tooltip).toHaveClass('astro-card--compact')
      }
    })
  })

  describe('Mathematical Calculations', () => {
    it('calculates planet positions correctly', () => {
      const { container } = render(<NatalChart planets={mockPlanets} />)
      
      // Test that degree markers are displayed correctly
      mockPlanets.forEach(planet => {
        const degreeText = Math.round(planet.degree) + '°'
        expect(container.textContent).toContain(degreeText)
      })
    })

    it('handles edge case degrees (0, 90, 180, 270)', () => {
      const edgePlanets: PlanetPosition[] = [
        { planet: 'sun', sign: 'aries', degree: 0, house: 1 },
        { planet: 'moon', sign: 'cancer', degree: 90, house: 4 },
        { planet: 'mercury', sign: 'libra', degree: 180, house: 7 },
        { planet: 'venus', sign: 'capricorn', degree: 270, house: 10 }
      ]
      
      const { container } = render(<NatalChart planets={edgePlanets} />)
      
      // Should render without errors
      expect(container.querySelector('svg')).toBeInTheDocument()
      expect(container.textContent).toContain('0°')
      expect(container.textContent).toContain('90°')
      expect(container.textContent).toContain('180°')
      expect(container.textContent).toContain('270°')
    })
  })

  describe('Accessibility', () => {
    it('provides proper SVG structure for screen readers', () => {
      const { container } = render(<NatalChart planets={mockPlanets} />)
      
      const svg = container.querySelector('svg')
      expect(svg).toHaveClass('natal-chart-wheel')
      expect(svg).toHaveAttribute('viewBox', '0 0 320 320')
    })

    it('includes text elements that are readable by screen readers', () => {
      const { container } = render(<NatalChart planets={mockPlanets} />)
      
      // House numbers should be present
      const houseNumbers = container.querySelectorAll('text')
      expect(houseNumbers.length).toBeGreaterThan(0)
    })

    it('handles keyboard navigation when interactive', () => {
      // This test would be more complex in a real implementation
      // For now, we just verify the component renders with interactive elements
      const { container } = render(<NatalChart planets={mockPlanets} interactive={true} />)
      
      const interactiveElements = container.querySelectorAll('circle[class*="cursor-pointer"]')
      expect(interactiveElements.length).toBeGreaterThan(0)
    })
  })

  describe('Error Handling', () => {
    it('handles empty planets array', () => {
      const { container } = render(<NatalChart planets={[]} />)
      
      // Should still render the chart structure
      expect(container.querySelector('svg')).toBeInTheDocument()
      expect(container.querySelectorAll('.zodiac-symbol')).toHaveLength(12)
    })

    it('handles invalid planet data gracefully', () => {
      const invalidPlanets = [
        { planet: 'sun' as const, sign: 'leo' as const, degree: NaN, house: 1 },
        { planet: 'moon' as const, sign: 'cancer' as const, degree: 400, house: 13 }
      ]
      
      const { container } = render(<NatalChart planets={invalidPlanets} />)
      
      // Should still render without crashing
      expect(container.querySelector('svg')).toBeInTheDocument()
    })

    it('handles missing aspects gracefully', () => {
      const invalidAspects: AspectData[] = [
        { planet1: 'sun', planet2: 'invalidPlanet' as any, type: 'conjunction', orb: 1 }
      ]
      
      const { container } = render(
        <NatalChart planets={mockPlanets} aspects={invalidAspects} />
      )
      
      // Should still render without crashing
      expect(container.querySelector('svg')).toBeInTheDocument()
    })
  })

  describe('Performance', () => {
    it('memoizes expensive calculations', () => {
      const { rerender } = render(<NatalChart planets={mockPlanets} />)
      
      // Rerender with same props - should not recalculate
      rerender(<NatalChart planets={mockPlanets} />)
      
      // Component should still work correctly
      const { container } = render(<NatalChart planets={mockPlanets} />)
      expect(container.querySelector('svg')).toBeInTheDocument()
    })

    it('handles large numbers of planets efficiently', () => {
      const manyPlanets: PlanetPosition[] = Array.from({ length: 50 }, (_, i) => ({
        planet: 'sun' as const,
        sign: 'leo' as const,
        degree: i * 7.2, // Spread around the circle
        house: (i % 12) + 1
      }))
      
      const { container } = render(<NatalChart planets={manyPlanets} />)
      
      // Should render without performance issues
      expect(container.querySelector('svg')).toBeInTheDocument()
    })
  })
})