/**
 * Tests for PlanetCard Component
 */

import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { PlanetCard } from '../PlanetCard'
import { PLANETS } from '../../../design-system/icons'

describe('PlanetCard', () => {
  const mockInfluence = {
    love: 75,
    career: 60,
    health: 85,
    money: 40
  }

  const mockAspects = [
    { type: 'positive' as const, description: 'Harmonious conjunction with Venus' },
    { type: 'negative' as const, description: 'Challenging square with Mars' }
  ]

  describe('Basic Rendering', () => {
    it('renders with minimum props', () => {
      render(<PlanetCard planet="sun" />)
      
      expect(screen.getByText('Sun')).toBeInTheDocument()
      expect(screen.getByText('☉')).toBeInTheDocument()
    })

    it('renders all planet information when provided', () => {
      render(
        <PlanetCard
          planet="mercury"
          sign="gemini"
          house={3}
          degree={15.5}
          influence={mockInfluence}
          aspects={mockAspects}
        />
      )

      expect(screen.getByText('Mercury')).toBeInTheDocument()
      expect(screen.getByText('☿')).toBeInTheDocument()
      expect(screen.getByText('♊ Gemini')).toBeInTheDocument()
      expect(screen.getByText('House 3')).toBeInTheDocument()
      expect(screen.getByText('16°')).toBeInTheDocument()
    })

    it('displays influence bars when provided', () => {
      render(<PlanetCard planet="venus" influence={mockInfluence} />)
      
      expect(screen.getByText('Influence Strength')).toBeInTheDocument()
      expect(screen.getByText('love')).toBeInTheDocument()
      expect(screen.getByText('75%')).toBeInTheDocument()
      expect(screen.getByText('career')).toBeInTheDocument()
      expect(screen.getByText('60%')).toBeInTheDocument()
    })

    it('displays aspects when provided', () => {
      render(<PlanetCard planet="mars" aspects={mockAspects} />)
      
      expect(screen.getByText('Current Aspects')).toBeInTheDocument()
      expect(screen.getByText('Harmonious conjunction with Venus')).toBeInTheDocument()
      expect(screen.getByText('Challenging square with Mars')).toBeInTheDocument()
    })
  })

  describe('Size Variants', () => {
    it('applies small size classes correctly', () => {
      const { container } = render(<PlanetCard planet="moon" size="small" />)
      
      const card = container.querySelector('.planet-card')
      expect(card).toHaveClass('min-h-48', 'max-w-64')
    })

    it('applies large size classes correctly', () => {
      const { container } = render(<PlanetCard planet="jupiter" size="large" />)
      
      const card = container.querySelector('.planet-card')
      expect(card).toHaveClass('min-h-64', 'max-w-96')
    })

    it('defaults to medium size', () => {
      const { container } = render(<PlanetCard planet="saturn" />)
      
      const card = container.querySelector('.planet-card')
      expect(card).toHaveClass('min-h-56', 'max-w-80')
    })
  })

  describe('Interactivity', () => {
    it('applies hover effects when interactive', () => {
      const { container } = render(<PlanetCard planet="uranus" interactive={true} />)
      
      const card = container.querySelector('.planet-card')
      expect(card).toHaveClass('hover:scale-105', 'hover:shadow-2xl', 'cursor-pointer')
    })

    it('does not apply hover effects when not interactive', () => {
      const { container } = render(<PlanetCard planet="neptune" interactive={false} />)
      
      const card = container.querySelector('.planet-card')
      expect(card).not.toHaveClass('hover:scale-105', 'hover:shadow-2xl', 'cursor-pointer')
    })
  })

  describe('Accessibility', () => {
    it('has proper heading hierarchy', () => {
      render(<PlanetCard planet="pluto" />)
      
      const heading = screen.getByRole('heading', { level: 3 })
      expect(heading).toBeInTheDocument()
      expect(heading).toHaveTextContent('Pluto')
    })

    it('provides accessible text for screen readers', () => {
      render(
        <PlanetCard
          planet="sun" 
          sign="leo" 
          house={5}
          degree={20}
          data-testid="sun-card"
        />
      )
      
      expect(screen.getByText('Sun')).toBeInTheDocument()
      expect(screen.getByText('♌ Leo')).toBeInTheDocument()
      expect(screen.getByText('House 5')).toBeInTheDocument()
    })
  })

  describe('Error Handling', () => {
    it('handles unknown planets gracefully', () => {
      const consoleWarn = vi.spyOn(console, 'warn').mockImplementation(() => {})
      
      // Test with invalid planet that should be caught
      render(<PlanetCard planet={'invalid' as any} />)
      
      consoleWarn.mockRestore()
    })

    it('handles missing sign information', () => {
      render(<PlanetCard planet="moon" sign={undefined} />)
      
      // Should not crash and should not show sign information
      expect(screen.queryByText('♊ Gemini')).not.toBeInTheDocument()
    })

    it('rounds degrees to nearest integer', () => {
      render(<PlanetCard planet="venus" degree={15.7} />)
      
      expect(screen.getByText('16°')).toBeInTheDocument()
    })
  })

  describe('Custom Styling', () => {
    it('applies custom className', () => {
      const { container } = render(
        <PlanetCard planet="mars" className="custom-class" />
      )
      
      const card = container.querySelector('.planet-card')
      expect(card).toHaveClass('custom-class')
    })

    it('applies planet-specific colors', () => {
      const { container } = render(<PlanetCard planet="mars" />)
      
      const icon = container.querySelector('.planet-card__icon')
      expect(icon).toBeDefined()
      // Mars should have red color (#ef4444)
      expect(icon).toHaveStyle('background: linear-gradient(135deg, #ef4444, #ef4444cc)')
    })
  })

  describe('Content Validation', () => {
    it('shows default description when none provided', () => {
      render(<PlanetCard planet="mercury" />)
      
      expect(screen.getByText(/Communication, thinking, and learning/)).toBeInTheDocument()
    })

    it('shows custom description when provided', () => {
      const customDescription = 'Custom planet description for testing'
      render(<PlanetCard planet="venus" description={customDescription} />)
      
      expect(screen.getByText(customDescription)).toBeInTheDocument()
    })

    it('validates all planets have required properties', () => {
      Object.keys(PLANETS).forEach(planet => {
        const planetKey = planet as keyof typeof PLANETS
        render(<PlanetCard planet={planetKey} />)
        
        const planetInfo = PLANETS[planetKey]
        expect(screen.getByText(planetInfo.name)).toBeInTheDocument()
        expect(screen.getByText(planetInfo.symbol)).toBeInTheDocument()
      })
    })
  })
})