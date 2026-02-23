import React from 'react';
import { cn } from '@/src/lib/api';

interface PulsingDotProps {
  color?: string;
  className?: string;
}

export const PulsingDot: React.FC<PulsingDotProps> = ({ color = '#63ffd1', className }) => {
  return (
    <div className={cn("relative flex h-2 w-2", className)}>
      <span 
        className="animate-pulse-slow absolute inline-flex h-full w-full rounded-full opacity-75"
        style={{ backgroundColor: color }}
      ></span>
      <span 
        className="relative inline-flex rounded-full h-2 w-2"
        style={{ backgroundColor: color }}
      ></span>
    </div>
  );
};
