import React, { useState } from 'react';
import { Search, Filter, Github, FileText, Globe, Package, ExternalLink, Clock, TrendingUp } from 'lucide-react';
import { GlassCard } from '../components/shared/GlassCard';
import { Badge } from '../components/shared/Badge';
import { useApi } from '../hooks/useApi';
import { getSignals, type RawSignal } from '../lib/api';

const SOURCES = [
  { id: 'all', label: 'All Sources', icon: Filter },
  { id: 'github', label: 'GitHub', icon: Github },
  { id: 'arxiv', label: 'ArXiv', icon: FileText },
  { id: 'hackernews', label: 'HackerNews', icon: Globe },
  { id: 'huggingface', label: 'HuggingFace', icon: Package },
];

const SOURCE_COLORS: Record<string, string> = {
  github: 'text-accent-secondary',
  arxiv: 'text-accent-tertiary',
  hackernews: 'text-accent-warning',
  hn: 'text-accent-warning',
  huggingface: 'text-accent-primary',
  hf: 'text-accent-primary',
};

const SOURCE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  github: Github,
  arxiv: FileText,
  hackernews: Globe,
  hn: Globe,
  huggingface: Package,
  hf: Package,
};

export default function SignalsPage() {
  const [activeSource, setActiveSource] = useState('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [limit, setLimit] = useState(20);

  const { data: signals, loading, refetch } = useApi<RawSignal[]>(
    () => getSignals(activeSource === 'all' ? undefined : activeSource, limit),
    [activeSource, limit]
  );

  const filteredSignals = (signals ?? []).filter(s => {
    if (!searchQuery) return true;
    const q = searchQuery.toLowerCase();
    const title = (s.payload?.title ?? '').toLowerCase();
    const content = (s.payload?.content ?? '').toLowerCase();
    return title.includes(q) || content.includes(q);
  });

  const getTimeAgo = (dateStr: string) => {
    const diff = Date.now() - new Date(dateStr).getTime();
    const hours = Math.floor(diff / (1000 * 60 * 60));
    if (hours < 1) return 'Just now';
    if (hours < 24) return `${hours}h ago`;
    const days = Math.floor(hours / 24);
    return `${days}d ago`;
  };

  return (
    <div className="p-6 space-y-6 max-w-6xl mx-auto">
      {/* Top Bar */}
      <div className="flex flex-col md:flex-row gap-4 items-center justify-between">
        <div className="flex flex-wrap gap-2">
          {SOURCES.map((source) => (
            <button
              key={source.id}
              onClick={() => setActiveSource(source.id)}
              className={`
                flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-bold uppercase tracking-wider transition-all border
                ${activeSource === source.id
                  ? 'bg-accent-primary text-bg-primary border-accent-primary'
                  : 'bg-bg-card text-text-secondary border-border-subtle hover:border-accent-primary/50'}
              `}
            >
              <source.icon className="w-4 h-4" />
              {source.label}
            </button>
          ))}
        </div>

        <div className="relative w-full md:w-80">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-text-muted" />
          <input
            type="text"
            placeholder="Filter signals by text..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-bg-card border border-border-subtle rounded-lg py-2 pl-10 pr-4 text-sm text-text-primary focus:outline-none focus:border-accent-primary transition-all"
          />
        </div>
      </div>

      {/* Loading */}
      {loading && <p className="text-center text-text-muted py-8">Loading signals...</p>}

      {/* Signal Grid */}
      <div className="grid grid-cols-1 gap-4">
        {filteredSignals.map((signal) => {
          const title = signal.payload?.title ?? signal.external_id ?? 'Untitled';
          const src = signal.source ?? 'unknown';
          const Icon = SOURCE_ICONS[src] ?? Globe;
          const colorClass = SOURCE_COLORS[src] ?? 'text-text-secondary';
          const relevance = signal.payload?.metadata?.codebase_relevance;
          const score = typeof relevance === 'number' ? relevance : null;
          const url = signal.payload?.url;
          const tags: string[] = Array.isArray(signal.payload?.metadata?.tags) ? (signal.payload.metadata.tags as string[]) : [];

          return (
            <GlassCard key={signal.id} className="p-5 hover:border-accent-primary/30 group">
              <div className="flex flex-col md:flex-row gap-6">
                {/* Source & Score */}
                <div className="flex md:flex-col items-center justify-between md:justify-center gap-4 md:w-24 border-b md:border-b-0 md:border-r border-border-subtle pb-4 md:pb-0 md:pr-6">
                  <div className={`p-3 rounded-xl bg-white/5 ${colorClass}`}>
                    <Icon className="w-6 h-6" />
                  </div>
                  {score != null && (
                    <div className="text-center">
                      <p className="text-lg font-black text-white">{(score * 100).toFixed(0)}</p>
                      <p className="text-[8px] font-bold text-text-muted uppercase tracking-widest">Relevance</p>
                    </div>
                  )}
                </div>

                {/* Content */}
                <div className="flex-1 space-y-3">
                  <div className="flex items-start justify-between gap-4">
                    <h3 className="text-lg font-bold text-white group-hover:text-accent-primary transition-colors leading-tight">
                      {title}
                    </h3>
                    {url && (
                      <a href={url} target="_blank" rel="noopener noreferrer" className="p-2 hover:bg-bg-hover rounded-lg transition-colors text-text-muted hover:text-white">
                        <ExternalLink className="w-4 h-4" />
                      </a>
                    )}
                  </div>

                  {tags.length > 0 && (
                    <div className="flex flex-wrap gap-2">
                      {tags.map(tag => (
                        <Badge key={tag} variant="muted" className="bg-bg-secondary border-none">{tag}</Badge>
                      ))}
                    </div>
                  )}

                  <div className="flex items-center gap-6 pt-2">
                    <div className="flex items-center gap-1.5 text-text-muted">
                      <Clock className="w-3 h-3" />
                      <span className="text-[10px] font-bold uppercase tracking-wider">{getTimeAgo(signal.created_at)}</span>
                    </div>
                    {score != null && score > 0.7 && (
                      <div className="flex items-center gap-1.5 text-accent-primary">
                        <TrendingUp className="w-3 h-3" />
                        <span className="text-[10px] font-bold uppercase tracking-wider">High Relevance</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>
            </GlassCard>
          );
        })}
      </div>

      {!loading && filteredSignals.length === 0 && (
        <p className="text-center text-text-muted py-8">No signals found. Try a different source or run ingestion.</p>
      )}

      <div className="flex justify-center py-8">
        <button
          onClick={() => setLimit(prev => prev + 20)}
          className="btn-secondary"
        >
          Load More Signals
        </button>
      </div>
    </div>
  );
}
