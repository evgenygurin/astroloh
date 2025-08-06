/**
 * Astroloh Design System - Planet Card Component
 * Informative cards displaying planetary information and influences
 */

import React from 'react';
import { PLANETS, ZODIAC_SIGNS, ELEMENTS } from '../../design-system/icons';

interface PlanetCardProps {
  planet: keyof typeof PLANETS;
  sign?: keyof typeof ZODIAC_SIGNS;
  house?: number;
  degree?: number;
  influence?: {
    love: number;
    career: number;
    health: number;
    money: number;
  };
  description?: string;
  aspects?: Array<{
    type: 'positive' | 'negative' | 'neutral';
    description: string;
  }>;
  size?: 'small' | 'medium' | 'large';
  interactive?: boolean;
  className?: string;
}

const PLANET_COLORS = {
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

const PLANET_DESCRIPTIONS = {
  sun: 'Your core identity, ego, and life purpose. Represents vitality and self-expression.',
  moon: 'Your emotions, instincts, and subconscious. Governs intuition and inner world.',
  mercury: 'Communication, thinking, and learning. Rules mental processes and expression.',
  venus: 'Love, beauty, and values. Influences relationships and aesthetic preferences.',
  mars: 'Action, passion, and drive. Represents energy, ambition, and assertiveness.',
  jupiter: 'Growth, wisdom, and expansion. Brings opportunities and philosophical insights.',
  saturn: 'Discipline, responsibility, and lessons. Teaches through challenges and structure.',
  uranus: 'Innovation, freedom, and change. Brings sudden insights and rebellion.',
  neptune: 'Dreams, spirituality, and illusion. Rules imagination and mystical experiences.',
  pluto: 'Transformation, power, and rebirth. Governs deep psychological changes.',
  northNode: 'Your karmic path and soul\'s purpose. Points to growth and evolution.',
  southNode: 'Past life talents and tendencies. Comfort zone to transcend.'
};

export const PlanetCard: React.FC<PlanetCardProps> = ({
  planet,
  sign,
  house,
  degree,
  influence,
  description,
  aspects = [],
  size = 'medium',
  interactive = true,
  className = ''
}) => {
  const planetInfo = PLANETS[planet];
  if (!planetInfo) {
    return (
      <div className="astro-card astro-card--error" role="alert">
        <span className="text-error">Unknown Planet: {planet}</span>
      </div>
    );
  }
  
  const signInfo = sign ? ZODIAC_SIGNS[sign] : null;
  const planetColor = PLANET_COLORS[planet];
  const planetDescription = description || PLANET_DESCRIPTIONS[planet];

  const sizeClasses = {
    small: 'min-h-48 max-w-64',
    medium: 'min-h-56 max-w-80',
    large: 'min-h-64 max-w-96'
  };

  const iconSizes = {
    small: 'w-12 h-12 text-xl',
    medium: 'w-16 h-16 text-2xl',
    large: 'w-20 h-20 text-3xl'
  };

  return (
    <div
      className={`
        planet-card ${sizeClasses[size]} ${className}
        ${interactive ? 'hover:scale-105 hover:shadow-2xl cursor-pointer' : ''}
        transition-all duration-300
      `}
      style={{
        boxShadow: interactive 
          ? `0 10px 25px -5px ${planetColor}20, 0 10px 10px -5px ${planetColor}10`
          : undefined
      }}
      role={interactive ? "button" : "article"}
      tabIndex={interactive ? 0 : undefined}
      aria-label={`${planetInfo.name} planet card${signInfo ? ` in ${signInfo.name}` : ''}${house ? ` in house ${house}` : ''}`}
      onKeyDown={(e) => {
        if (interactive && (e.key === 'Enter' || e.key === ' ')) {
          e.preventDefault();
          // Handle card selection/interaction
        }
      }}
    >
      {/* Planet Icon */}
      <div
        className={`planet-card__icon ${iconSizes[size]}`}
        style={{
          background: `linear-gradient(135deg, ${planetColor}, ${planetColor}cc)`,
          boxShadow: `0 0 20px ${planetColor}40`
        }}
      >
        <span className="text-dark-900 font-bold">
          {planetInfo.symbol}
        </span>
      </div>

      {/* Planet Name */}
      <h3 className="planet-card__name">
        {planetInfo.name}
      </h3>

      {/* Position Information */}
      {(signInfo || house || degree !== undefined) && (
        <div className="flex flex-wrap gap-2 mb-3">
          {signInfo && (
            <div className="astro-text text-xs bg-mystical-purple/20 px-2 py-1 rounded-full">
              {signInfo.symbol} {signInfo.name}
            </div>
          )}
          {house && (
            <div className="astro-text text-xs bg-mystical-gold/20 px-2 py-1 rounded-full">
              House {house}
            </div>
          )}
          {degree !== undefined && (
            <div className="astro-text text-xs bg-dark-200/50 px-2 py-1 rounded-full">
              {Math.round(degree)}°
            </div>
          )}
        </div>
      )}

      {/* Description */}
      <p className="planet-card__description flex-1">
        {planetDescription}
      </p>

      {/* Influence Bars */}
      {influence && (
        <div className="mt-4 space-y-2">
          <div className="astro-text--mystical text-xs font-semibold mb-2">
            Influence Strength
          </div>
          {Object.entries(influence).map(([area, value]) => (
            <div key={area} className="flex items-center gap-2">
              <span className="astro-text text-xs capitalize w-12">
                {area}
              </span>
              <div className="flex-1 astro-progress">
                <div
                  className={`astro-progress__bar astro-progress__bar--${area}`}
                  style={{ width: `${value}%` }}
                >
                  <div className="astro-progress__shimmer" />
                </div>
              </div>
              <span className="astro-text text-xs w-8 text-right">
                {value}%
              </span>
            </div>
          ))}
        </div>
      )}

      {/* Aspects */}
      {aspects.length > 0 && (
        <div className="mt-4">
          <div className="astro-text--mystical text-xs font-semibold mb-2">
            Current Aspects
          </div>
          <div className="space-y-1">
            {aspects.map((aspect, index) => (
              <div
                key={index}
                className={`
                  text-xs p-2 rounded-md
                  ${aspect.type === 'positive' ? 'bg-success/20 text-success' : ''}
                  ${aspect.type === 'negative' ? 'bg-error/20 text-error' : ''}
                  ${aspect.type === 'neutral' ? 'bg-info/20 text-info' : ''}
                `}
              >
                {aspect.description}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Floating constellation pattern */}
      <div className="constellation-pattern" />
    </div>
  );
};

export default PlanetCard;