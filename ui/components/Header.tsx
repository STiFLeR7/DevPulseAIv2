import React from 'react';
import { ServerStatus } from '../types';

interface HeaderProps {
  status: ServerStatus;
}

export const Header: React.FC<HeaderProps> = ({ status }) => {
  const getStatusBadge = () => {
    switch (status) {
      case ServerStatus.ONLINE:
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-teal-500/10 border border-teal-500/30 text-teal-400 text-xs font-mono tracking-wide shadow-[0_0_10px_rgba(45,212,191,0.2)]">
            <span className="relative flex h-2 w-2">
              <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-teal-400 opacity-75"></span>
              <span className="relative inline-flex rounded-full h-2 w-2 bg-teal-500"></span>
            </span>
            ONLINE
          </div>
        );
      case ServerStatus.WAKING_UP:
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-orange-500/10 border border-orange-500/30 text-orange-400 text-xs font-mono tracking-wide">
            <i className="fas fa-circle-notch fa-spin text-[10px]"></i>
            WAKING UP...
          </div>
        );
      case ServerStatus.CHECKING:
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-slate-700/30 border border-slate-600 text-slate-400 text-xs font-mono tracking-wide">
            <i className="fas fa-circle-notch fa-spin text-[10px]"></i>
            CONNECTING
          </div>
        );
      case ServerStatus.ERROR:
        return (
          <div className="flex items-center gap-2 px-3 py-1 rounded-full bg-red-500/10 border border-red-500/30 text-red-400 text-xs font-mono tracking-wide">
            <i className="fas fa-exclamation-triangle"></i>
            OFFLINE
          </div>
        );
    }
  };

  return (
    <header className="sticky top-0 z-50 backdrop-blur-md bg-slate-950/80 border-b border-white/5 px-6 py-4">
      <div className="max-w-7xl mx-auto flex justify-between items-center">
        {/* Logo Area */}
        <div className="flex items-center gap-3 group cursor-pointer">
          <div className="relative w-8 h-8 flex items-center justify-center bg-cyan-950 rounded-lg border border-cyan-500/30 group-hover:border-cyan-400/60 transition-colors">
            <i className="fas fa-wave-square text-cyan-400 text-sm"></i>
            <div className="absolute inset-0 bg-cyan-400/20 blur-lg rounded-full opacity-0 group-hover:opacity-50 transition-opacity"></div>
          </div>
          <h1 className="text-xl font-bold tracking-tight text-white">
            DevPulse<span className="text-cyan-400 animate-pulse">AI</span>
          </h1>
        </div>

        {/* Status */}
        {getStatusBadge()}
      </div>
    </header>
  );
};