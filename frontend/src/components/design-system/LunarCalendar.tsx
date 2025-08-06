/**
 * Astroloh Design System - Lunar Calendar Component
 * Interactive calendar showing lunar phases and astrological events
 */

import React, { useState, useMemo } from 'react';
import { LUNAR_PHASES, ZODIAC_SIGNS } from '../../design-system/icons';
import { format, startOfMonth, endOfMonth, eachDayOfInterval, isSameDay, addMonths, subMonths } from 'date-fns';

interface LunarEvent {
  date: Date;
  type: 'phase' | 'transit' | 'aspect' | 'special';
  phase?: keyof typeof LUNAR_PHASES;
  title: string;
  description: string;
  intensity: 'low' | 'medium' | 'high';
  sign?: keyof typeof ZODIAC_SIGNS;
}

interface LunarCalendarProps {
  events?: LunarEvent[];
  selectedDate?: Date;
  onDateSelect?: (date: Date) => void;
  onEventClick?: (event: LunarEvent) => void;
  showToday?: boolean;
  size?: 'compact' | 'normal' | 'large';
  className?: string;
}

const PHASE_STYLES = {
  newMoon: 'bg-dark-300',
  waxingCrescent: 'bg-gradient-to-r from-dark-300 to-mystical-silver',
  firstQuarter: 'bg-gradient-to-r from-dark-300 to-mystical-silver',
  waxingGibbous: 'bg-gradient-to-r from-dark-200 to-mystical-silver',
  fullMoon: 'bg-mystical-silver shadow-lg shadow-mystical-silver/50',
  waningGibbous: 'bg-gradient-to-l from-dark-200 to-mystical-silver',
  lastQuarter: 'bg-gradient-to-l from-dark-300 to-mystical-silver',
  waningCrescent: 'bg-gradient-to-l from-dark-300 to-mystical-silver'
};

const INTENSITY_COLORS = {
  low: 'border-mystical-purple/30 bg-mystical-purple/10',
  medium: 'border-mystical-gold/50 bg-mystical-gold/20',
  high: 'border-error/60 bg-error/30'
};

export const LunarCalendar: React.FC<LunarCalendarProps> = ({
  events = [],
  selectedDate,
  onDateSelect,
  onEventClick,
  showToday = true,
  size = 'normal',
  className = ''
}) => {
  const [currentMonth, setCurrentMonth] = useState(new Date());
  const [hoveredDate, setHoveredDate] = useState<Date | null>(null);

  const monthStart = startOfMonth(currentMonth);
  const monthEnd = endOfMonth(currentMonth);
  const daysInMonth = eachDayOfInterval({ start: monthStart, end: monthEnd });

  const sizeClasses = {
    compact: 'text-xs',
    normal: 'text-sm',
    large: 'text-base'
  };

  const cellSizes = {
    compact: 'w-8 h-8',
    normal: 'w-12 h-12',
    large: 'w-16 h-16'
  };

  // Group events by date
  const eventsByDate = useMemo(() => {
    const grouped = new Map<string, LunarEvent[]>();
    events.forEach(event => {
      const dateKey = format(event.date, 'yyyy-MM-dd');
      if (!grouped.has(dateKey)) {
        grouped.set(dateKey, []);
      }
      grouped.get(dateKey)!.push(event);
    });
    return grouped;
  }, [events]);

  const getEventsForDate = (date: Date) => {
    const dateKey = format(date, 'yyyy-MM-dd');
    return eventsByDate.get(dateKey) || [];
  };

  const getPrimaryPhaseForDate = (date: Date) => {
    const dayEvents = getEventsForDate(date);
    const phaseEvent = dayEvents.find(event => event.type === 'phase' && event.phase);
    return phaseEvent?.phase || null;
  };

  const navigateMonth = (direction: 'prev' | 'next') => {
    setCurrentMonth(prev => direction === 'next' ? addMonths(prev, 1) : subMonths(prev, 1));
  };

  const handleDateClick = (date: Date) => {
    onDateSelect?.(date);
  };

  const handleEventClick = (event: LunarEvent, e: React.MouseEvent) => {
    e.stopPropagation();
    onEventClick?.(event);
  };

  const isToday = (date: Date) => isSameDay(date, new Date());
  const isSelected = (date: Date) => selectedDate && isSameDay(date, selectedDate);
  const isHovered = (date: Date) => hoveredDate && isSameDay(date, hoveredDate);

  return (
    <div className={`lunar-calendar ${className}`}>
      {/* Calendar Header */}
      <div className="flex items-center justify-between mb-6">
        <button
          onClick={() => navigateMonth('prev')}
          className="astro-button astro-button--ghost p-2"
        >
          ←
        </button>
        
        <h2 className="astro-heading astro-heading--4">
          {format(currentMonth, 'MMMM yyyy')}
        </h2>
        
        <button
          onClick={() => navigateMonth('next')}
          className="astro-button astro-button--ghost p-2"
        >
          →
        </button>
      </div>

      {/* Days of week header */}
      <div className="grid grid-cols-7 gap-1 mb-2">
        {['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'].map(day => (
          <div
            key={day}
            className={`${cellSizes[size]} flex items-center justify-center`}
          >
            <span className="astro-text--mystical text-xs font-medium">
              {day}
            </span>
          </div>
        ))}
      </div>

      {/* Calendar Grid */}
      <div className="grid grid-cols-7 gap-1">
        {daysInMonth.map(date => {
          const dayEvents = getEventsForDate(date);
          const primaryPhase = getPrimaryPhaseForDate(date);
          const hasEvents = dayEvents.length > 0;
          const highIntensityEvent = dayEvents.find(e => e.intensity === 'high');
          
          return (
            <div
              key={date.toISOString()}
              className={`
                ${cellSizes[size]} relative cursor-pointer rounded-lg border transition-all duration-200
                ${isSelected(date) ? 'border-mystical-gold bg-mystical-gold/20' : 'border-transparent'}
                ${isHovered(date) ? 'border-mystical-gold/50 bg-mystical-gold/10' : ''}
                ${isToday(date) && showToday ? 'ring-2 ring-mystical-purple' : ''}
                ${hasEvents ? 'bg-dark-100/80' : 'bg-dark-200/40'}
                hover:bg-mystical-gold/10 hover:border-mystical-gold/30
              `}
              onClick={() => handleDateClick(date)}
              onMouseEnter={() => setHoveredDate(date)}
              onMouseLeave={() => setHoveredDate(null)}
            >
              {/* Date number */}
              <div className={`absolute top-1 left-1 ${sizeClasses[size]} astro-text font-medium`}>
                {format(date, 'd')}
              </div>

              {/* Lunar phase indicator */}
              {primaryPhase && (
                <div
                  className={`
                    absolute top-1 right-1 w-3 h-3 rounded-full border
                    ${PHASE_STYLES[primaryPhase]}
                  `}
                  title={LUNAR_PHASES[primaryPhase].name}
                />
              )}

              {/* Event indicators */}
              {hasEvents && (
                <div className="absolute bottom-1 left-1 right-1 flex justify-center">
                  <div className="flex gap-0.5">
                    {dayEvents.slice(0, 3).map((event, index) => (
                      <div
                        key={index}
                        className={`
                          w-1.5 h-1.5 rounded-full cursor-pointer transition-all
                          ${INTENSITY_COLORS[event.intensity]}
                          hover:scale-125
                        `}
                        title={event.title}
                        onClick={(e) => handleEventClick(event, e)}
                      />
                    ))}
                    {dayEvents.length > 3 && (
                      <div className="w-1.5 h-1.5 rounded-full bg-mystical-silver/50" />
                    )}
                  </div>
                </div>
              )}

              {/* High intensity event glow */}
              {highIntensityEvent && (
                <div className="absolute inset-0 rounded-lg border border-error/60 animate-pulse" />
              )}
            </div>
          );
        })}
      </div>

      {/* Event Details for Selected/Hovered Date */}
      {(hoveredDate || selectedDate) && (
        <div className="mt-6">
          {(() => {
            const targetDate = hoveredDate || selectedDate!;
            const dateEvents = getEventsForDate(targetDate);
            
            if (dateEvents.length === 0) return null;

            return (
              <div className="astro-card">
                <h3 className="astro-heading astro-heading--5 mb-4">
                  {format(targetDate, 'MMMM d, yyyy')}
                </h3>
                
                <div className="space-y-3">
                  {dateEvents.map((event, index) => (
                    <div
                      key={index}
                      className={`
                        lunar-event cursor-pointer transition-all duration-200
                        ${INTENSITY_COLORS[event.intensity]}
                        hover:scale-102 hover:shadow-md
                      `}
                      onClick={() => onEventClick?.(event)}
                    >
                      <div className="lunar-event__title flex items-center gap-2">
                        {event.phase && (
                          <span className="text-lg">
                            {LUNAR_PHASES[event.phase].symbol}
                          </span>
                        )}
                        {event.sign && (
                          <span className="text-mystical-purple">
                            {ZODIAC_SIGNS[event.sign].symbol}
                          </span>
                        )}
                        {event.title}
                      </div>
                      
                      <div className="lunar-event__description">
                        {event.description}
                      </div>

                      <div className="flex items-center justify-between mt-2">
                        <span className={`
                          text-xs px-2 py-1 rounded-full capitalize
                          ${event.intensity === 'high' ? 'bg-error/20 text-error' : ''}
                          ${event.intensity === 'medium' ? 'bg-warning/20 text-warning' : ''}
                          ${event.intensity === 'low' ? 'bg-info/20 text-info' : ''}
                        `}>
                          {event.intensity} intensity
                        </span>
                        
                        <span className="text-xs astro-text--muted capitalize">
                          {event.type}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            );
          })()}
        </div>
      )}
    </div>
  );
};

export default LunarCalendar;