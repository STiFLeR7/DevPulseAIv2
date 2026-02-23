import React from 'react';
import { cn } from '@/src/lib/api';

interface BadgeProps {
  children: React.ReactNode;
  variant?: 'primary' | 'secondary' | 'tertiary' | 'warning' | 'danger' | 'muted';
  className?: string;
}

export const Badge: React.FC<BadgeProps> = ({ children, variant = 'primary', className }) => {
  const variants = {
    primary: 'bg-accent-primary/10 text-accent-primary border-accent-primary/20',
    secondary: 'bg-accent-secondary/10 text-accent-secondary border-accent-secondary/20',
    tertiary: 'bg-accent-tertiary/10 text-accent-tertiary border-accent-tertiary/20',
    warning: 'bg-accent-warning/10 text-accent-warning border-accent-warning/20',
    danger: 'bg-accent-danger/10 text-accent-danger border-accent-danger/20',
    muted: 'bg-text-muted/10 text-text-muted border-text-muted/20',
  };

  return (
    <span className={cn(
      "px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider border",
      variants[variant],
      className
    )}>
      {children}
    </span>
  );
};
