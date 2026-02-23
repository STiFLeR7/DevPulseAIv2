import React from 'react';
import { motion } from 'motion/react';
import { ArrowRight, Zap, Activity, MessageSquare, Shield, Database, Cpu } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import { Badge } from '../components/shared/Badge';

export default function LandingPage() {
  const navigate = useNavigate();

  const features = [
    { icon: Database, title: 'Knowledge Graph', desc: 'Context-aware intelligence mapping across all ingested signals.' },
    { icon: Cpu, title: 'Ephemeral Workers', desc: 'On-demand agents that scale to handle complex analytical tasks.' },
    { icon: Activity, title: 'Smart Routing', desc: 'Dynamic task allocation based on agent specialization and load.' },
  ];

  return (
    <div className="min-h-screen flex flex-col relative overflow-hidden">
      {/* Background Grid */}
      <div className="absolute inset-0 z-0 opacity-20" 
           style={{ backgroundImage: 'radial-gradient(circle, #63ffd1 1px, transparent 1px)', backgroundSize: '40px 40px' }}>
      </div>
      
      <main className="flex-1 flex flex-col items-center justify-center px-6 relative z-10 py-20">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.8 }}
          className="text-center max-w-4xl"
        >
          <div className="flex justify-center mb-6">
            <Badge variant="primary" className="px-4 py-1 text-xs">
              ● MULTISWARM ACTIVE — 7 Agents Online
            </Badge>
          </div>

          <h1 className="text-6xl md:text-8xl font-black mb-6 tracking-tighter">
            <span className="text-white">⚡ DevPulseAI</span>
            <span className="text-gradient block">v3</span>
          </h1>

          <p className="text-xl md:text-2xl text-text-secondary mb-12 max-w-2xl mx-auto leading-relaxed">
            Autonomous Technical Intelligence — <br />
            <span className="text-accent-primary">Ingest</span> • 
            <span className="text-accent-secondary"> Analyze</span> • 
            <span className="text-accent-tertiary"> Deliver</span>
          </p>

          <div className="flex flex-wrap justify-center gap-4 mb-20">
            <button 
              onClick={() => navigate('/dashboard')}
              className="btn-primary flex items-center gap-2 text-lg px-8 py-4"
            >
              Open Dashboard <ArrowRight className="w-5 h-5" />
            </button>
            <button className="btn-secondary text-lg px-8 py-4">
              View Documentation
            </button>
          </div>

          {/* Stats */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-12 max-w-3xl mx-auto mb-20">
            {[
              { label: 'Signals Ingested', value: '347+' },
              { label: 'Intelligence Processed', value: '1,028+' },
              { label: 'Active Conversations', value: '18+' },
            ].map((stat, i) => (
              <div key={i} className="flex flex-col items-center">
                <span className="text-4xl font-bold text-white mb-1">{stat.value}</span>
                <span className="text-sm uppercase tracking-widest text-text-muted font-bold">{stat.label}</span>
              </div>
            ))}
          </div>

          {/* Features */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-left">
            {features.map((f, i) => (
              <div key={i} className="glass-card p-8 group">
                <f.icon className="w-10 h-10 text-accent-primary mb-4 group-hover:scale-110 transition-transform" />
                <h3 className="text-xl font-bold mb-2 text-white">{f.title}</h3>
                <p className="text-text-secondary leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </motion.div>
      </main>
    </div>
  );
}
