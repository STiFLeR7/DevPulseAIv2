import React, { useState } from 'react';
import {
  Settings as SettingsIcon, Cpu, Bell, Database, Filter,
  Save, RefreshCw, Trash2, Plus, Check, AlertCircle, Loader2
} from 'lucide-react';
import { GlassCard } from '../components/shared/GlassCard';
import { Badge } from '../components/shared/Badge';
import { useApi } from '../hooks/useApi';
import {
  getModelRouterStatus, getAlertsStatus, postContext, postDailyPulse,
  type ModelRouterStatus, type AlertsStatus,
} from '../lib/api';

export default function SettingsPage() {
  const [isSaving, setIsSaving] = useState(false);
  const [projectPath, setProjectPath] = useState('');
  const [scanResult, setScanResult] = useState<string | null>(null);
  const [scanError, setScanError] = useState<string | null>(null);
  const [pulseStatus, setPulseStatus] = useState<string | null>(null);

  const { data: routerStatus, loading: routerLoading } = useApi<ModelRouterStatus>(() => getModelRouterStatus(), []);
  const { data: alertsStatus, loading: alertsLoading } = useApi<AlertsStatus>(() => getAlertsStatus(), []);

  const handleScanProject = async () => {
    if (!projectPath.trim()) return;
    setIsSaving(true);
    setScanResult(null);
    setScanError(null);
    try {
      const result = await postContext(projectPath);
      setScanResult(`✅ Scanned ${result.project}: ${result.deps_count} deps, frameworks: ${result.frameworks.join(', ')}`);
    } catch (err) {
      setScanError(err instanceof Error ? err.message : 'Scan failed');
    } finally {
      setIsSaving(false);
    }
  };

  const handleDailyPulse = async () => {
    setPulseStatus('running');
    try {
      await postDailyPulse();
      setPulseStatus('✅ Daily Pulse triggered — ingestion running in background');
    } catch (err) {
      setPulseStatus(`❌ ${err instanceof Error ? err.message : 'Failed'}`);
    }
  };

  // Derive tiers from real data
  const tiers = routerStatus
    ? Object.entries(routerStatus.tiers).map(([tier, model]) => ({
      tier: tier.charAt(0).toUpperCase() + tier.slice(1),
      model,
      active: true,
    }))
    : [];

  const channels = alertsStatus?.configured_channels ?? [];

  return (
    <div className="p-6 space-y-8 max-w-4xl mx-auto">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="p-2 bg-accent-primary/10 rounded-lg">
            <SettingsIcon className="w-6 h-6 text-accent-primary" />
          </div>
          <h1 className="text-2xl font-bold text-white">Configuration</h1>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6">
        {/* Model Routing */}
        <GlassCard className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <Cpu className="w-5 h-5 text-accent-tertiary" />
            <h2 className="text-lg font-bold text-white">Model Routing Tiers</h2>
            {routerLoading && <Loader2 className="w-4 h-4 text-text-muted animate-spin" />}
          </div>
          {routerStatus && (
            <div className="flex items-center gap-4 mb-4 text-xs text-text-secondary">
              <span>Total Calls: <strong className="text-white">{routerStatus.total_calls}</strong></span>
              <span>Total Cost: <strong className="text-accent-warning">${routerStatus.total_cost_estimate.toFixed(2)}</strong></span>
            </div>
          )}
          <div className="space-y-4">
            {tiers.map((item) => (
              <div key={item.tier} className="flex items-center justify-between p-4 rounded-xl bg-bg-secondary border border-border-subtle">
                <div>
                  <div className="flex items-center gap-2 mb-1">
                    <span className="text-sm font-bold text-white">{item.tier} Tier</span>
                    <Badge variant="primary">Active</Badge>
                  </div>
                  <p className="text-xs text-text-muted font-mono">{item.model}</p>
                </div>
              </div>
            ))}
            {tiers.length === 0 && !routerLoading && (
              <p className="text-xs text-text-muted">Model router not configured</p>
            )}
          </div>
        </GlassCard>

        {/* Alert Channels */}
        <GlassCard className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <Bell className="w-5 h-5 text-accent-danger" />
            <h2 className="text-lg font-bold text-white">Alert Channels</h2>
            {alertsLoading && <Loader2 className="w-4 h-4 text-text-muted animate-spin" />}
          </div>
          {alertsStatus && (
            <p className="text-xs text-text-secondary mb-4">
              Total Alerts Sent: <strong className="text-white">{alertsStatus.total_alerts_sent}</strong>
            </p>
          )}
          <div className="flex flex-wrap gap-3 mb-6">
            {channels.map(channel => (
              <div key={channel} className="flex items-center gap-2 px-4 py-2 rounded-lg bg-bg-secondary border border-border-subtle">
                <Check className="w-4 h-4 text-accent-primary" />
                <span className="text-sm text-text-primary capitalize">{channel}</span>
              </div>
            ))}
            {channels.length === 0 && !alertsLoading && (
              <p className="text-xs text-text-muted">No alert channels configured (set DISCORD_WEBHOOK_URL, SLACK_WEBHOOK_URL, or ALERT_EMAIL)</p>
            )}
          </div>

          {/* Recent alerts */}
          {(alertsStatus?.recent_alerts ?? []).length > 0 && (
            <div className="space-y-2 mt-4">
              <h3 className="text-[10px] font-bold text-text-muted uppercase tracking-widest mb-2">Recent Alerts</h3>
              {alertsStatus!.recent_alerts.slice(0, 10).map((alert, i) => (
                <div key={i} className="flex items-center gap-3 p-3 rounded-lg bg-bg-secondary border border-border-subtle">
                  <Badge variant={alert.severity === 'CRITICAL' ? 'danger' : alert.severity === 'HIGH' ? 'warning' : 'muted'}>
                    {alert.severity}
                  </Badge>
                  <span className="text-xs text-text-primary flex-1 truncate">{alert.message}</span>
                  <span className="text-[10px] text-text-muted">{alert.type}</span>
                </div>
              ))}
            </div>
          )}
        </GlassCard>

        {/* Project Context */}
        <GlassCard className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <Database className="w-5 h-5 text-accent-secondary" />
            <h2 className="text-lg font-bold text-white">Project Context</h2>
          </div>
          <div className="space-y-4">
            <div>
              <label className="block text-[10px] font-bold text-text-muted uppercase tracking-widest mb-2">Project Path</label>
              <div className="flex gap-2">
                <input
                  type="text"
                  placeholder="/path/to/your/project"
                  value={projectPath}
                  onChange={(e) => setProjectPath(e.target.value)}
                  className="flex-1 bg-bg-secondary border border-border-subtle rounded-lg px-4 py-2 text-sm text-text-primary focus:outline-none focus:border-accent-primary"
                />
                <button
                  onClick={handleScanProject}
                  disabled={isSaving || !projectPath.trim()}
                  className="btn-secondary px-4 flex items-center gap-2 disabled:opacity-50"
                >
                  {isSaving ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Database className="w-4 h-4" />}
                  Scan
                </button>
              </div>
            </div>
            {scanResult && (
              <div className="p-4 rounded-xl bg-accent-primary/5 border border-accent-primary/20">
                <p className="text-xs text-accent-primary">{scanResult}</p>
              </div>
            )}
            {scanError && (
              <div className="p-4 rounded-xl bg-accent-danger/5 border border-accent-danger/20">
                <p className="text-xs text-accent-danger">{scanError}</p>
              </div>
            )}
          </div>
        </GlassCard>

        {/* Ingestion */}
        <GlassCard className="p-6">
          <div className="flex items-center gap-3 mb-6">
            <Filter className="w-5 h-5 text-accent-primary" />
            <h2 className="text-lg font-bold text-white">Signal Ingestion</h2>
          </div>
          <div className="space-y-4">
            <button
              onClick={handleDailyPulse}
              className="btn-primary flex items-center gap-2"
            >
              <RefreshCw className="w-4 h-4" />
              Trigger Daily Pulse
            </button>
            <p className="text-xs text-text-muted">
              Runs ingestion across all sources (GitHub, HuggingFace, ArXiv, HackerNews) in the background.
            </p>
            {pulseStatus && (
              <p className="text-xs text-text-secondary">{pulseStatus}</p>
            )}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
