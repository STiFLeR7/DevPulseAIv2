import React from 'react';
import { SyncType } from '../types';

interface ControlPanelProps {
  onSync: (type: SyncType) => void;
  loadingState: Record<string, boolean>;
  disabled: boolean;
}

export const ControlPanel: React.FC<ControlPanelProps> = ({ onSync, loadingState, disabled }) => {
  return (
    <section className="py-8 animate-fade-in">
      <div className="glass-panel rounded-2xl p-8 border border-slate-700/50 relative overflow-hidden">
        {/* Background Decorative Glow - Swapped Blue for Sky/Cyan */}
        <div className="absolute -top-20 -right-20 w-64 h-64 bg-cyan-500/10 rounded-full blur-3xl pointer-events-none"></div>
        <div className="absolute -bottom-20 -left-20 w-64 h-64 bg-sky-600/10 rounded-full blur-3xl pointer-events-none"></div>

        <div className="relative z-10 flex flex-col md:flex-row items-center justify-between gap-8">

          <div className="text-center md:text-left">
            <h2 className="text-2xl font-bold text-white mb-2">Control Center</h2>
            <p className="text-slate-400 text-sm max-w-md">
              Manually trigger intelligence gathering or sync specific data sources.
              The system sleeps when idle to conserve resources.
            </p>
          </div>

          <div className="flex flex-col sm:flex-row items-center gap-4">
            {/* Primary Button */}
            <button
              onClick={() => onSync('daily')}
              disabled={disabled || loadingState['daily']}
              className={`
                group relative px-8 py-4 rounded-xl font-bold text-white shadow-lg transition-all duration-300
                ${disabled
                  ? 'bg-slate-800 cursor-not-allowed text-slate-500'
                  : 'bg-gradient-to-r from-cyan-600 to-sky-600 hover:from-cyan-500 hover:to-sky-500 hover:shadow-cyan-500/25 hover:-translate-y-0.5'
                }
              `}
            >
              <span className="flex items-center gap-3">
                {loadingState['daily'] ? (
                  <i className="fas fa-circle-notch fa-spin"></i>
                ) : (
                  <i className="fas fa-rocket group-hover:animate-bounce"></i>
                )}
                TRIGGER DAILY PULSE
              </span>
              {!disabled && (
                <div className="absolute inset-0 rounded-xl ring-2 ring-white/20 group-hover:ring-white/40 transition-all"></div>
              )}
            </button>

            {/* Secondary Group */}
            <div className="flex gap-2">
              {[
                { id: 'github', icon: 'fa-github', label: 'GitHub' },
                { id: 'arxiv', icon: 'fa-scroll', label: 'ArXiv' },
                { id: 'medium', icon: 'fa-medium', label: 'Medium' },
                { id: 'hackernews', icon: 'fa-hacker-news', label: 'HackerNews' }
              ].map((btn) => (
                <button
                  key={btn.id}
                  onClick={() => onSync(btn.id as SyncType)}
                  disabled={disabled || loadingState[btn.id]}
                  title={`Sync ${btn.label}`}
                  className={`
                    w-12 h-12 rounded-lg border flex items-center justify-center transition-all duration-200
                    ${disabled
                      ? 'border-slate-800 text-slate-700 bg-slate-900'
                      : 'border-slate-600 text-slate-400 hover:text-cyan-400 hover:border-cyan-400/50 hover:bg-cyan-950/30'
                    }
                  `}
                >
                  {loadingState[btn.id] ? (
                    <i className="fas fa-circle-notch fa-spin text-xs"></i>
                  ) : (
                    <i className={`fab ${btn.icon} text-lg`}></i>
                  )}
                </button>
              ))}
            </div>
          </div>

        </div>
      </div>
    </section>
  );
};