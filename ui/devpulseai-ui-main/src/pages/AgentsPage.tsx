import React from 'react';
import { motion } from 'motion/react';
import { 
  Search, FileText, FolderOpen, Globe, Shield, Package, 
  Brain, Scale, BarChart3, ArrowRight, Activity, Cpu, Database, Network, Zap
} from 'lucide-react';
import { GlassCard } from '../components/shared/GlassCard';
import { Badge } from '../components/shared/Badge';
import { PulsingDot } from '../components/shared/PulsingDot';
import { AGENTS } from '../lib/constants';

const ICON_MAP: Record<string, any> = {
  Search, FileText, FolderOpen, Globe, Shield, Package, Brain, Scale, BarChart3
};

export default function AgentsPage() {
  return (
    <div className="p-6 space-y-12 max-w-7xl mx-auto">
      <div className="text-center space-y-4">
        <h1 className="text-4xl font-black tracking-tight text-white">Agent System Overview</h1>
        <p className="text-text-secondary max-w-2xl mx-auto">
          DevPulseAI v3 utilizes a Multi-Swarm architecture where specialized agents collaborate 
          to ingest, analyze, and deliver technical intelligence.
        </p>
      </div>

      {/* Agent Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {AGENTS.map((agent, i) => {
          const Icon = ICON_MAP[agent.icon];
          return (
            <motion.div
              key={agent.id}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: i * 0.1 }}
            >
              <GlassCard className="h-full flex flex-col group relative overflow-hidden">
                <div className="absolute top-0 right-0 p-4">
                  <PulsingDot color={agent.color} />
                </div>
                
                <div className="flex items-start gap-4 mb-6">
                  <div className="p-3 rounded-xl bg-white/5 group-hover:bg-accent-primary/10 transition-colors">
                    <Icon className="w-6 h-6" style={{ color: agent.color }} />
                  </div>
                  <div>
                    <h3 className="text-lg font-bold text-white mb-1">{agent.name}</h3>
                    <Badge variant={
                      agent.swarm === 'Research' ? 'secondary' :
                      agent.swarm === 'Analysis' ? 'tertiary' :
                      agent.swarm === 'Core' ? 'primary' :
                      agent.swarm === 'Intelligence' ? 'warning' : 'muted'
                    }>
                      {agent.swarm}
                    </Badge>
                  </div>
                </div>

                <p className="text-sm text-text-secondary leading-relaxed mb-6 flex-1">
                  {agent.description}
                </p>

                <div className="pt-4 border-t border-border-subtle flex items-center justify-between">
                  <div className="flex items-center gap-2">
                    <Activity className="w-3 h-3 text-text-muted" />
                    <span className="text-[10px] font-bold text-text-muted uppercase tracking-wider">Active Tasks: {Math.floor(Math.random() * 5)}</span>
                  </div>
                  <button className="text-[10px] font-bold text-accent-primary uppercase tracking-widest flex items-center gap-1 hover:gap-2 transition-all">
                    View Logs <ArrowRight className="w-3 h-3" />
                  </button>
                </div>
              </GlassCard>
            </motion.div>
          );
        })}
      </div>

      {/* Architecture Diagram */}
      <div className="space-y-8">
        <h2 className="text-2xl font-bold text-white text-center">System Architecture</h2>
        <GlassCard className="p-12">
          <div className="flex flex-col md:flex-row items-center justify-between gap-8 relative">
            {/* Connection Lines (Desktop) */}
            <div className="absolute top-1/2 left-0 w-full h-0.5 bg-gradient-to-r from-accent-secondary via-accent-primary to-accent-tertiary -translate-y-1/2 hidden md:block opacity-20"></div>
            
            {[
              { label: 'Signal Sources', icon: Globe, color: 'text-accent-secondary' },
              { label: 'MCP Layer', icon: Network, color: 'text-accent-tertiary' },
              { label: 'Ingestion Pipeline', icon: Database, color: 'text-accent-warning' },
              { label: 'Multi-Swarm', icon: Cpu, color: 'text-accent-primary' },
              { label: 'Delivery', icon: Zap, color: 'text-accent-secondary' },
            ].map((step, i) => (
              <div key={i} className="flex flex-col items-center gap-4 relative z-10">
                <div className={`p-6 rounded-2xl bg-bg-secondary border border-border-subtle shadow-2xl ${step.color} hover:scale-110 transition-transform cursor-default`}>
                  <step.icon className="w-8 h-8" />
                </div>
                <span className="text-xs font-bold text-white uppercase tracking-widest">{step.label}</span>
              </div>
            ))}
          </div>
        </GlassCard>
      </div>
    </div>
  );
}
