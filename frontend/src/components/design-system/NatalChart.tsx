/**
 * Astroloh Design System - Natal Chart Component
 * Beautiful visualization of natal chart data with interactive elements
 */

import React, { useState, useCallback } from 'react';
import { ZODIAC_SIGNS, PLANETS, ASPECTS, getAllZodiacSigns, getAllPlanets } from '../../design-system/icons';

interface PlanetPosition {
  planet: keyof typeof PLANETS;
  sign: keyof typeof ZODIAC_SIGNS;
  degree: number;
  house: number;
}

interface AspectData {
  planet1: keyof typeof PLANETS;
  planet2: keyof typeof PLANETS;
  type: keyof typeof ASPECTS;
  orb: number;
}

interface NatalChartProps {
  planets: PlanetPosition[];
  aspects?: AspectData[];
  size?: 'small' | 'medium' | 'large';
  interactive?: boolean;
  showAspects?: boolean;
  className?: string;
}

export const NatalChart: React.FC<NatalChartProps> = ({
  planets,
  aspects = [],
  size = 'medium',
  interactive = true,
  showAspects = true,
  className = ''
}) => {
  const [hoveredPlanet, setHoveredPlanet] = useState<keyof typeof PLANETS | null>(null);
  const [selectedPlanet, setSelectedPlanet] = useState<keyof typeof PLANETS | null>(null);

  const sizeClasses = {
    small: 'w-64 h-64',
    medium: 'w-80 h-80',
    large: 'w-96 h-96'
  };

  const centerX = 160;
  const centerY = 160;
  const outerRadius = 140;
  const middleRadius = 110;
  const innerRadius = 80;

  // Calculate planet positions on the chart
  const getPlanetPosition = useCallback((degree: number, radius: number) => {
    const radian = (degree - 90) * (Math.PI / 180); // -90 to start from top
    return {
      x: centerX + radius * Math.cos(radian),
      y: centerY + radius * Math.sin(radian)
    };
  }, []);

  // Generate house divisions
  const houseLines = Array.from({ length: 12 }, (_, i) => {
    const degree = i * 30;
    const start = getPlanetPosition(degree, innerRadius);
    const end = getPlanetPosition(degree, outerRadius);
    return (
      <line
        key={`house-${i}`}
        x1={start.x}
        y1={start.y}
        x2={end.x}
        y2={end.y}
        className="constellation-line opacity-30"
      />
    );
  });

  // Generate zodiac signs around the wheel
  const zodiacSigns = getAllZodiacSigns().map((sign, index) => {
    const degree = index * 30 + 15; // Center of each sign
    const position = getPlanetPosition(degree, outerRadius - 20);
    return (
      <g key={sign.name}>
        <text
          x={position.x}
          y={position.y}
          className="zodiac-symbol"
          textAnchor="middle"
          dominantBaseline="middle"
          style={{ fontSize: '18px' }}
        >
          {sign.symbol}
        </text>
      </g>
    );
  });

  // Generate house numbers
  const houseNumbers = Array.from({ length: 12 }, (_, i) => {
    const degree = i * 30 + 15;
    const position = getPlanetPosition(degree, innerRadius + 15);
    return (
      <text
        key={`house-num-${i}`}
        x={position.x}
        y={position.y}
        className="astro-text text-mystical-purple text-sm font-semibold"
        textAnchor="middle"
        dominantBaseline="middle"
      >
        {i + 1}
      </text>
    );
  });

  // Generate planets
  const planetElements = planets.map((planetData) => {
    const position = getPlanetPosition(planetData.degree, middleRadius);
    const planet = PLANETS[planetData.planet];
    const isHovered = hoveredPlanet === planetData.planet;
    const isSelected = selectedPlanet === planetData.planet;

    return (
      <g key={planetData.planet}>
        {/* Planet glow effect when hovered */}
        {(isHovered || isSelected) && (
          <circle
            cx={position.x}
            cy={position.y}
            r="20"
            fill="url(#planetGlow)"
            className="opacity-60"
          />
        )}
        
        {/* Planet circle */}
        <circle
          cx={position.x}
          cy={position.y}
          r="12"
          className={`
            cursor-pointer transition-all duration-200 
            ${isSelected ? 'fill-mystical-gold' : 'fill-gradient-golden'}
            ${isHovered ? 'stroke-mystical-gold stroke-2' : 'stroke-none'}
          `}
          onMouseEnter={() => interactive && setHoveredPlanet(planetData.planet)}
          onMouseLeave={() => interactive && setHoveredPlanet(null)}
          onClick={() => interactive && setSelectedPlanet(
            selectedPlanet === planetData.planet ? null : planetData.planet
          )}
        />
        
        {/* Planet symbol */}
        <text
          x={position.x}
          y={position.y}
          className="text-dark-900 text-sm font-bold pointer-events-none"
          textAnchor="middle"
          dominantBaseline="middle"
        >
          {planet.symbol}
        </text>
        
        {/* Degree marker */}
        <text
          x={position.x}
          y={position.y + 25}
          className="astro-text text-xs opacity-70"
          textAnchor="middle"
        >
          {Math.round(planetData.degree)}°
        </text>
      </g>
    );
  });

  // Generate aspects
  const aspectLines = showAspects ? aspects.map((aspect, index) => {
    const planet1 = planets.find(p => p.planet === aspect.planet1);
    const planet2 = planets.find(p => p.planet === aspect.planet2);
    
    if (!planet1 || !planet2) return null;
    
    const pos1 = getPlanetPosition(planet1.degree, middleRadius);
    const pos2 = getPlanetPosition(planet2.degree, middleRadius);
    
    const aspectInfo = ASPECTS[aspect.type];
    const opacity = Math.max(0.1, 1 - (aspect.orb / 10)); // Fade based on orb
    
    return (
      <line
        key={`aspect-${index}`}
        x1={pos1.x}
        y1={pos1.y}
        x2={pos2.x}
        y2={pos2.y}
        stroke={aspect.type === 'trine' || aspect.type === 'sextile' ? '#10b981' : '#ef4444'}
        strokeWidth="1"
        strokeDasharray={aspect.type === 'opposition' ? '5,5' : 'none'}
        opacity={opacity}
        className="pointer-events-none"
      />
    );
  }).filter(Boolean) : [];

  return (
    <div className={`natal-chart-container ${sizeClasses[size]} ${className}`}>
      <svg
        width="320"
        height="320"
        viewBox="0 0 320 320"
        className="natal-chart-wheel"
      >
        {/* Gradients and definitions */}
        <defs>
          <radialGradient id="chartBackground" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(30, 27, 75, 0.8)" />
            <stop offset="100%" stopColor="rgba(10, 10, 15, 0.9)" />
          </radialGradient>
          
          <radialGradient id="planetGlow" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(251, 191, 36, 0.4)" />
            <stop offset="100%" stopColor="rgba(251, 191, 36, 0)" />
          </radialGradient>
          
          <linearGradient id="goldenGradient" x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor="#fbbf24" />
            <stop offset="50%" stopColor="#f59e0b" />
            <stop offset="100%" stopColor="#d97706" />
          </linearGradient>
        </defs>

        {/* Background circle */}
        <circle
          cx={centerX}
          cy={centerY}
          r={outerRadius}
          fill="url(#chartBackground)"
          className="drop-shadow-lg"
        />

        {/* Outer ring */}
        <circle
          cx={centerX}
          cy={centerY}
          r={outerRadius}
          fill="none"
          stroke="rgba(251, 191, 36, 0.6)"
          strokeWidth="2"
        />

        {/* Middle ring */}
        <circle
          cx={centerX}
          cy={centerY}
          r={middleRadius}
          fill="none"
          stroke="rgba(251, 191, 36, 0.4)"
          strokeWidth="1"
        />

        {/* Inner ring */}
        <circle
          cx={centerX}
          cy={centerY}
          r={innerRadius}
          fill="none"
          stroke="rgba(251, 191, 36, 0.3)"
          strokeWidth="1"
        />

        {/* House division lines */}
        {houseLines}

        {/* Zodiac signs */}
        {zodiacSigns}

        {/* House numbers */}
        {houseNumbers}

        {/* Aspect lines (drawn first so they appear behind planets) */}
        {aspectLines}

        {/* Planets */}
        {planetElements}

        {/* Center dot */}
        <circle
          cx={centerX}
          cy={centerY}
          r="3"
          fill="url(#goldenGradient)"
        />
      </svg>

      {/* Planet information tooltip */}
      {selectedPlanet && (
        <div className="absolute top-4 left-4 astro-card astro-card--compact max-w-48 z-10">
          <div className="astro-text--mystical text-sm font-semibold mb-1">
            {PLANETS[selectedPlanet].name}
          </div>
          <div className="astro-text text-xs">
            {(() => {
              const planetData = planets.find(p => p.planet === selectedPlanet);
              if (!planetData) return null;
              const sign = ZODIAC_SIGNS[planetData.sign];
              return (
                <>
                  <div>Sign: {sign.symbol} {sign.name}</div>
                  <div>House: {planetData.house}</div>
                  <div>Degree: {Math.round(planetData.degree)}°</div>
                </>
              );
            })()}
          </div>
        </div>
      )}
    </div>
  );
};

export default NatalChart;