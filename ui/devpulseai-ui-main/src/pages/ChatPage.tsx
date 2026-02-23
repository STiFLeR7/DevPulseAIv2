import React, { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'motion/react';
import { Send, ThumbsUp, ThumbsDown, Brain, Zap, Search, FileText, Globe, Shield, Package } from 'lucide-react';
import { Badge } from '../components/shared/Badge';
import { GlassCard } from '../components/shared/GlassCard';
import { PulsingDot } from '../components/shared/PulsingDot';
import { useWebSocket } from '../hooks/useWebSocket';
import { postFeedback, getRecommendations, type Recommendation } from '../lib/api';
import { useApi } from '../hooks/useApi';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  intent?: string;
}

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([
    { id: '1', role: 'assistant', content: 'Hello! I am DevPulseAI. How can I help you analyze signals today?', timestamp: new Date() }
  ]);
  const [input, setInput] = useState('');
  const scrollRef = useRef<HTMLDivElement>(null);

  const { send, lastMessage, isConnected, isTyping, conversationId } = useWebSocket();
  const { data: recommendations } = useApi<Recommendation[]>(() => getRecommendations(conversationId ?? undefined), [conversationId]);

  // Handle incoming WebSocket messages
  useEffect(() => {
    if (!lastMessage) return;
    if (lastMessage.type === 'response' && lastMessage.content) {
      const aiMsg: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: lastMessage.content,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, aiMsg]);
    } else if (lastMessage.type === 'error' && lastMessage.content) {
      const errMsg: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `⚠️ ${lastMessage.content}`,
        timestamp: new Date(),
      };
      setMessages(prev => [...prev, errMsg]);
    }
  }, [lastMessage]);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [messages, isTyping]);

  const handleSend = () => {
    if (!input.trim()) return;

    const userMsg: Message = {
      id: Date.now().toString(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMsg]);
    send(input, conversationId ?? undefined);
    setInput('');
  };

  const handleFeedback = async (vote: 'positive' | 'negative', msgContent: string) => {
    if (!conversationId) return;
    try {
      await postFeedback(conversationId, vote, msgContent.slice(0, 120));
    } catch (err) {
      console.error('Feedback error:', err);
    }
  };

  const quickActions = [
    { label: 'Analyze Repo', icon: Search },
    { label: 'Find Papers', icon: FileText },
    { label: 'Community Vibe', icon: Globe },
    { label: 'Risk Scan', icon: Shield },
    { label: 'Dependency Impact', icon: Package },
  ];

  return (
    <div className="flex h-[calc(100vh-3.5rem)] overflow-hidden">
      {/* Left Pane - Chat Area */}
      <div className="flex-1 flex flex-col min-w-0 border-r border-border-subtle">
        {/* Top Bar */}
        <div className="h-14 border-b border-border-subtle flex items-center justify-between px-6 bg-bg-secondary/50">
          <div className="flex items-center gap-3">
            <span className="text-xs font-bold text-text-muted uppercase tracking-widest">
              {conversationId ? `Session: ${conversationId.slice(0, 8)}` : 'New Session'}
            </span>
            <Badge variant={isConnected ? 'primary' : 'danger'}>
              {isConnected ? 'Connected' : 'Disconnected'}
            </Badge>
          </div>
          {isTyping && (
            <div className="flex items-center gap-2">
              <PulsingDot />
              <span className="text-[10px] font-bold text-accent-primary uppercase tracking-widest">Agent Processing...</span>
            </div>
          )}
        </div>

        {/* Message List */}
        <div ref={scrollRef} className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-hide">
          {messages.map((msg) => (
            <div key={msg.id} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] ${msg.role === 'user' ? 'order-2' : ''}`}>
                <div className={msg.role === 'user'
                  ? "bg-accent-secondary/20 border border-accent-secondary/30 rounded-2xl rounded-tr-none p-4 text-text-primary"
                  : "bg-bg-card border border-border-subtle rounded-2xl rounded-tl-none p-4 text-text-primary shadow-lg border-l-2 border-l-accent-primary"
                }>
                  <p className="leading-relaxed whitespace-pre-wrap">{msg.content}</p>

                  {msg.role === 'assistant' && (
                    <div className="mt-4 pt-4 border-t border-border-subtle flex items-center justify-between">
                      <div className="flex gap-2">
                        <button
                          onClick={() => handleFeedback('positive', msg.content)}
                          className="p-1.5 hover:bg-bg-hover rounded transition-colors text-text-muted hover:text-accent-primary"
                        >
                          <ThumbsUp className="w-4 h-4" />
                        </button>
                        <button
                          onClick={() => handleFeedback('negative', msg.content)}
                          className="p-1.5 hover:bg-bg-hover rounded transition-colors text-text-muted hover:text-accent-danger"
                        >
                          <ThumbsDown className="w-4 h-4" />
                        </button>
                      </div>
                      <span className="text-[10px] text-text-muted font-bold uppercase">{msg.timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                    </div>
                  )}
                </div>
              </div>
            </div>
          ))}
          {isTyping && (
            <div className="flex justify-start">
              <div className="bg-bg-card border border-border-subtle rounded-2xl rounded-tl-none p-4 shadow-lg">
                <div className="flex gap-1">
                  <span className="w-1.5 h-1.5 bg-accent-primary rounded-full animate-bounce"></span>
                  <span className="w-1.5 h-1.5 bg-accent-primary rounded-full animate-bounce [animation-delay:0.2s]"></span>
                  <span className="w-1.5 h-1.5 bg-accent-primary rounded-full animate-bounce [animation-delay:0.4s]"></span>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Input Area */}
        <div className="p-6 bg-bg-secondary/30 border-t border-border-subtle">
          <div className="max-w-4xl mx-auto">
            <div className="flex flex-wrap gap-2 mb-4">
              {quickActions.map((action) => (
                <button
                  key={action.label}
                  onClick={() => setInput(action.label + ': ')}
                  className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-bg-card border border-border-subtle text-[10px] font-bold text-text-secondary uppercase tracking-wider hover:border-accent-primary hover:text-accent-primary transition-all"
                >
                  <action.icon className="w-3 h-3" />
                  {action.label}
                </button>
              ))}
            </div>
            <div className="relative">
              <textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && (e.preventDefault(), handleSend())}
                placeholder={isConnected ? "Ask about repos, papers, risks, dependencies..." : "Connecting to server..."}
                disabled={!isConnected}
                className="w-full bg-bg-card border border-border-subtle rounded-xl p-4 pr-14 text-text-primary focus:outline-none focus:border-accent-primary transition-all resize-none h-24 disabled:opacity-50"
              />
              <button
                onClick={handleSend}
                disabled={!isConnected || !input.trim()}
                className="absolute right-4 bottom-4 p-2 bg-accent-primary text-bg-primary rounded-lg hover:opacity-90 transition-all active:scale-95 disabled:opacity-30"
              >
                <Send className="w-5 h-5" />
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Right Pane - Context Panel */}
      <div className="w-80 hidden lg:flex flex-col bg-bg-secondary/30 p-6 space-y-6">
        <div>
          <h3 className="text-[10px] font-bold text-text-muted uppercase tracking-[0.2em] mb-4">Context Metadata</h3>
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-xs text-text-secondary">Connection</span>
              <Badge variant={isConnected ? 'primary' : 'danger'}>
                {isConnected ? 'WebSocket' : 'Offline'}
              </Badge>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-text-secondary">Conversation</span>
              <span className="text-xs font-mono text-accent-tertiary">{conversationId?.slice(0, 8) ?? '—'}</span>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-xs text-text-secondary">Messages</span>
              <span className="text-xs font-mono text-accent-warning">{messages.length}</span>
            </div>
          </div>
        </div>

        <div>
          <h3 className="text-[10px] font-bold text-text-muted uppercase tracking-[0.2em] mb-4">Active Agent</h3>
          <GlassCard className="p-4 border-l-2 border-l-accent-primary">
            <div className="flex items-center gap-3">
              <div className="p-2 bg-accent-primary/10 rounded-lg">
                <Brain className="w-5 h-5 text-accent-primary" />
              </div>
              <div>
                <p className="text-sm font-bold text-white">MultiSwarm</p>
                <p className="text-[10px] text-text-secondary">Auto-Routing</p>
              </div>
            </div>
          </GlassCard>
        </div>

        <div className="flex-1">
          <h3 className="text-[10px] font-bold text-text-muted uppercase tracking-[0.2em] mb-4">Recommendations</h3>
          <div className="space-y-3">
            {(recommendations ?? []).length === 0 && (
              <p className="text-xs text-text-muted">Send a message to see related signals</p>
            )}
            {(recommendations ?? []).map((rec, i) => (
              <GlassCard key={i} className="p-3 hover:translate-x-1">
                <p className="text-xs font-bold text-text-primary mb-2">{rec.title}</p>
                <div className="flex items-center justify-between">
                  <div className="h-1 flex-1 bg-bg-hover rounded-full overflow-hidden mr-3">
                    <div className="h-full bg-accent-primary" style={{ width: `${rec.relevance_score * 100}%` }}></div>
                  </div>
                  <span className="text-[10px] font-mono text-accent-primary">{(rec.relevance_score * 100).toFixed(0)}%</span>
                </div>
              </GlassCard>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
