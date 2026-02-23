import React, { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import { Zap } from 'lucide-react';
import { PulsingDot } from '../shared/PulsingDot';
import { Badge } from '../shared/Badge';
import { ping } from '../../lib/api';

export const Navbar: React.FC = () => {
  const [isOnline, setIsOnline] = useState(false);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    const check = async () => {
      try {
        await ping();
        setIsOnline(true);
      } catch {
        setIsOnline(false);
      }
    };

    check();
    interval = setInterval(check, 15_000); // Poll every 15s

    return () => clearInterval(interval);
  }, []);

  const navLinks = [
    { name: 'Dashboard', path: '/dashboard' },
    { name: 'Chat', path: '/chat' },
    { name: 'Agents', path: '/agents' },
    { name: 'Signals', path: '/signals' },
    { name: 'Settings', path: '/settings' },
  ];

  return (
    <nav className="sticky top-0 z-50 h-14 bg-bg-primary/80 backdrop-blur-md border-b border-border-subtle px-6 flex items-center justify-between">
      <div className="flex items-center gap-8">
        <NavLink to="/" className="flex items-center gap-2 group">
          <Zap className="w-5 h-5 text-accent-primary group-hover:scale-110 transition-transform" />
          <span className="font-bold text-lg tracking-tight">DevPulseAI</span>
        </NavLink>

        <div className="hidden md:flex items-center gap-6">
          {navLinks.map((link) => (
            <NavLink
              key={link.path}
              to={link.path}
              className={({ isActive }) => `
                text-sm font-medium transition-all hover:text-accent-primary
                ${isActive ? 'text-accent-primary' : 'text-text-secondary'}
              `}
            >
              {link.name}
            </NavLink>
          ))}
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-bg-secondary border border-border-subtle">
          <PulsingDot color={isOnline ? '#63ffd1' : '#ff6b6b'} />
          <span className="text-[10px] font-bold text-text-secondary uppercase tracking-widest">
            {isOnline ? 'Connected' : 'Offline'}
          </span>
        </div>
        <Badge variant="muted">v3.0.0</Badge>
      </div>
    </nav>
  );
};
