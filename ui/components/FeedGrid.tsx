import React from 'react';
import { FeedItem } from '../types';

interface FeedGridProps {
  items: FeedItem[];
  loading: boolean;
}

export const FeedGrid: React.FC<FeedGridProps> = ({ items, loading }) => {
  if (items.length === 0 && !loading) {
    return (
      <div className="text-center py-20 border border-dashed border-slate-800 rounded-xl">
        <i className="fas fa-satellite-dish text-slate-700 text-4xl mb-4"></i>
        <p className="text-slate-500">Waiting for signal acquisition...</p>
      </div>
    );
  }

  return (
    <section className="py-4">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-semibold text-slate-200 flex items-center gap-2">
          <i className="fas fa-bolt text-cyan-500"></i>
          Live Intelligence Feed
        </h3>
        <span className="text-xs font-mono text-slate-500 bg-slate-900 px-2 py-1 rounded border border-slate-800">
          {items.length} SIGNALS
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {items.map((item, index) => (
          <div
            key={item.id}
            className="glass-panel glass-panel-hover p-5 rounded-xl transition-all duration-300 group animate-slide-up"
            style={{ animationDelay: `${index * 50}ms` }}
          >
            <div className="flex justify-between items-start mb-3">
              <span className={`
                text-[10px] font-bold uppercase tracking-wider px-2 py-0.5 rounded border
                ${item.type === 'repo' ? 'bg-sky-500/10 text-sky-400 border-sky-500/20' : ''}
                ${item.type === 'paper' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : ''}
                ${item.type === 'article' ? 'bg-amber-500/10 text-amber-400 border-amber-500/20' : ''}
              `}>
                {item.type}
              </span>
              <span className="text-xs text-slate-500 font-mono">{item.timestamp}</span>
            </div>

            <h4 className="text-slate-200 font-medium leading-snug mb-3 group-hover:text-cyan-300 transition-colors line-clamp-2">
              {item.title}
            </h4>

            <div className="flex items-center justify-between mt-auto pt-3 border-t border-slate-700/30">
              <span className="text-xs text-slate-400 flex items-center gap-1">
                <i className={`
                  ${item.source === 'GitHub' ? 'fab fa-github' : ''}
                  ${item.source === 'ArXiv' ? 'fas fa-scroll' : ''}
                  ${item.source === 'Medium' ? 'fab fa-medium' : ''}
                  ${item.source === 'Dev.to' ? 'fab fa-dev' : ''}
                  ${item.source === 'hackernews' ? 'fab fa-hacker-news' : ''}
                `}></i>
                {item.source}
              </span>
              <a href={item.url} className="text-xs text-cyan-500 hover:text-cyan-400 flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                OPEN <i className="fas fa-external-link-alt text-[10px]"></i>
              </a>
            </div>
          </div>
        ))}

        {/* Loading Skeletons */}
        {loading && Array.from({ length: 3 }).map((_, i) => (
          <div key={`skel-${i}`} className="glass-panel p-5 rounded-xl animate-pulse">
            <div className="flex justify-between mb-3">
              <div className="h-4 w-12 bg-slate-800 rounded"></div>
              <div className="h-4 w-16 bg-slate-800 rounded"></div>
            </div>
            <div className="h-12 bg-slate-800 rounded mb-3"></div>
            <div className="h-4 w-full bg-slate-800 rounded mt-4"></div>
          </div>
        ))}
      </div>
    </section>
  );
};