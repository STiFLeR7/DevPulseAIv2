import React from 'react';
import {
  PieChart, Pie, Cell, Tooltip, ResponsiveContainer,
} from 'recharts';
import {
  Activity, Zap, Brain, AlertTriangle, TrendingUp,
  Github, FileText, Globe, Package, ArrowUpRight, ArrowDownRight
} from 'lucide-react';
import { GlassCard } from '../components/shared/GlassCard';
import { Badge } from '../components/shared/Badge';
import { PulsingDot } from '../components/shared/PulsingDot';
import { useApi } from '../hooks/useApi';
import {
  getSignals, getIntelligence, getModelRouterStatus, getAlertsStatus,
  type RawSignal, type IntelligenceItem, type ModelRouterStatus, type AlertsStatus
} from '../lib/api';

const SOURCE_COLORS: Record<string, string> = {
  github: '#00b4d8',
  arxiv: '#a78bfa',
  hackernews: '#ffbe32',
  huggingface: '#63ffd1',
  hn: '#ffbe32',
  hf: '#63ffd1',
  medium: '#e0e6ed',
};

const SOURCE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  github: Github,
  arxiv: FileText,
  hn: Globe,
  hackernews: Globe,
  hf: Package,
  huggingface: Package,
};

export default function DashboardPage() {
  const { data: signals, loading: sigLoading } = useApi<RawSignal[]>(() => getSignals(undefined, 20), []);
  const { data: intelligence, loading: intLoading } = useApi<IntelligenceItem[]>(() => getIntelligence(undefined, 8), []);
  const { data: routerStatus } = useApi<ModelRouterStatus>(() => getModelRouterStatus(), []);
  const { data: alertsStatus } = useApi<AlertsStatus>(() => getAlertsStatus(), []);

  // Derive source distribution for pie chart
  const sourceCounts: Record<string, number> = {};
  (signals ?? []).forEach(s => {
    const src = s.source ?? 'unknown';
    sourceCounts[src] = (sourceCounts[src] || 0) + 1;
  });
  const pieData = Object.entries(sourceCounts).map(([name, value]) => ({
    name: name.charAt(0).toUpperCase() + name.slice(1),
    value,
    color: SOURCE_COLORS[name] ?? '#8899aa',
  }));

  const metrics = [
    { label: 'Signals Ingested', value: signals ? signals.length.toLocaleString() : '—', icon: Activity, color: 'text-accent-primary' },
    { label: 'Intelligence Processed', value: intelligence ? intelligence.length.toLocaleString() : '—', icon: Brain, color: 'text-accent-tertiary' },
    { label: 'Active Agents', value: '7', status: 'Online', icon: Zap, color: 'text-accent-secondary' },
    { label: 'Model Cost (Today)', value: routerStatus ? `$${routerStatus.total_cost_estimate.toFixed(2)}` : '—', trend: routerStatus ? `${routerStatus.total_calls} calls` : '', icon: TrendingUp, color: 'text-accent-warning' },
    { label: 'Alerts Sent', value: alertsStatus ? String(alertsStatus.total_alerts_sent) : '—', icon: AlertTriangle, color: 'text-accent-danger' },
  ];

  return (
    <div className="p-6 space-y-6 max-w-[1600px] mx-auto">
      {/* Row 1: Metrics */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
        {metrics.map((metric, i) => (
          <GlassCard key={i} className="p-4">
            <div className="flex justify-between items-start mb-2">
              <div className={`p-2 rounded-lg bg-white/5 ${metric.color}`}>
                <metric.icon className="w-5 h-5" />
              </div>
              {metric.trend && (
                <span className="text-[10px] font-bold flex items-center gap-0.5 text-text-secondary">
                  {metric.trend}
                </span>
              )}
              {metric.status && (
                <div className="flex items-center gap-1.5">
                  <PulsingDot />
                  <span className="text-[10px] font-bold text-accent-primary uppercase">{metric.status}</span>
                </div>
              )}
            </div>
            <p className="text-2xl font-bold text-white mb-1">{metric.value}</p>
            <p className="text-[10px] font-bold text-text-muted uppercase tracking-wider">{metric.label}</p>
          </GlassCard>
        ))}
      </div>

      {/* Row 2: Signal Feed + Distribution */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <GlassCard className="lg:col-span-2 p-0 flex flex-col h-[400px]">
          <div className="p-6 border-b border-border-subtle flex justify-between items-center">
            <h3 className="text-sm font-bold text-white uppercase tracking-widest">Signal Feed</h3>
            <Badge variant={sigLoading ? 'muted' : 'primary'}>{sigLoading ? 'Loading...' : 'Live'}</Badge>
          </div>
          <div className="flex-1 overflow-y-auto p-4 space-y-3 scrollbar-hide">
            {(signals ?? []).slice(0, 20).map((signal) => {
              const title = signal.payload?.title ?? signal.external_id ?? 'Untitled';
              const src = signal.source ?? 'unknown';
              const Icon = SOURCE_ICONS[src] ?? Globe;
              const score = signal.payload?.metadata?.codebase_relevance;
              const displayScore = typeof score === 'number' ? score : null;

              return (
                <div key={signal.id} className="flex items-center gap-4 p-3 rounded-lg hover:bg-bg-hover transition-colors group">
                  <div className={`p-2 rounded bg-white/5`} style={{ color: SOURCE_COLORS[src] ?? '#8899aa' }}>
                    <Icon className="w-4 h-4" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-sm font-medium text-text-primary truncate">{title}</p>
                    <p className="text-[10px] text-text-muted">
                      {src} · {new Date(signal.created_at).toLocaleDateString()}
                      {displayScore != null && ` · Relevance: ${(displayScore * 100).toFixed(0)}%`}
                    </p>
                  </div>
                  {displayScore != null && (
                    <div className="h-1 w-16 bg-bg-hover rounded-full overflow-hidden">
                      <div className="h-full bg-accent-primary" style={{ width: `${displayScore * 100}%` }}></div>
                    </div>
                  )}
                </div>
              );
            })}
            {!sigLoading && (signals ?? []).length === 0 && (
              <p className="text-center text-text-muted py-8">No signals ingested yet. Run POST /ingest to start.</p>
            )}
          </div>
        </GlassCard>

        <GlassCard className="p-6 h-[400px] flex flex-col">
          <h3 className="text-sm font-bold text-white uppercase tracking-widest mb-6">Distribution</h3>
          <div className="flex-1">
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieData}
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={5}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{ backgroundColor: '#131b2e', border: '1px solid rgba(99, 255, 209, 0.25)', borderRadius: '8px' }}
                    itemStyle={{ color: '#e0e6ed', fontSize: '12px' }}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p className="text-center text-text-muted pt-12">No data yet</p>
            )}
          </div>
          <div className="grid grid-cols-2 gap-2 mt-4">
            {pieData.map((item) => (
              <div key={item.name} className="flex items-center gap-2">
                <div className="w-2 h-2 rounded-full" style={{ backgroundColor: item.color }}></div>
                <span className="text-[10px] text-text-secondary font-medium">{item.name} ({item.value})</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>

      {/* Row 3: Agent Gauges */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
        {[
          { name: 'RepoResearcher', color: '#00b4d8', value: 85 },
          { name: 'PaperAnalyst', color: '#a78bfa', value: 92 },
          { name: 'CommunityVibe', color: '#63ffd1', value: 78 },
          { name: 'RiskAnalyst', color: '#ff6b6b', value: 64 },
        ].map((agent, i) => (
          <GlassCard key={i} className="p-6 text-center">
            <h4 className="text-[10px] font-bold text-text-muted uppercase tracking-widest mb-4">{agent.name}</h4>
            <div className="relative h-24 w-full flex items-center justify-center">
              <svg className="w-full h-full transform -rotate-90">
                <circle cx="50%" cy="50%" r="36" fill="none" stroke="rgba(255,255,255,0.05)" strokeWidth="8" strokeDasharray="226.2" strokeDashoffset="113.1" />
                <circle cx="50%" cy="50%" r="36" fill="none" stroke={agent.color} strokeWidth="8" strokeDasharray="226.2" strokeDashoffset={226.2 - (agent.value / 100) * 113.1} className="transition-all duration-1000" />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center pt-4">
                <span className="text-2xl font-bold text-white">{agent.value}%</span>
                <span className="text-[8px] font-bold text-text-muted uppercase">Confidence</span>
              </div>
            </div>
          </GlassCard>
        ))}
      </div>

      {/* Row 4: Recent Intelligence */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {intLoading && <p className="text-text-muted col-span-4 text-center py-8">Loading intelligence...</p>}
        {(intelligence ?? []).map((item, i) => (
          <GlassCard key={item.id ?? i} className="p-4 hover:border-accent-primary/40 group">
            <div className="flex justify-between items-start mb-3">
              <Badge variant={item.agent_name.includes('Paper') ? 'tertiary' : 'primary'}>
                {item.agent_name}
              </Badge>
              <span className="text-[10px] text-text-muted font-mono">
                {new Date(item.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            </div>
            <p className="text-xs text-text-primary line-clamp-2 mb-3 group-hover:text-accent-primary transition-colors">
              {item.summary}
            </p>
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1.5">
                <PulsingDot color={item.confidence > 0.85 ? '#63ffd1' : '#ffbe32'} />
                <span className="text-[10px] font-bold text-text-secondary uppercase">Processed</span>
              </div>
              <span className="text-[10px] font-bold text-accent-primary">{item.confidence.toFixed(2)}</span>
            </div>
          </GlassCard>
        ))}
        {!intLoading && (intelligence ?? []).length === 0 && (
          <p className="text-text-muted col-span-4 text-center py-8">No intelligence processed yet</p>
        )}
      </div>
    </div>
  );
}
