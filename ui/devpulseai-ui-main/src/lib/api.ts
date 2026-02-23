import { clsx, type ClassValue } from 'clsx';
import { twMerge } from 'tailwind-merge';

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

// ── API Base URL ──────────────────────────────────
// In dev: Vite proxy forwards /api → localhost:8000
// In prod: same-origin or VITE_API_URL override
export const API_BASE = import.meta.env.VITE_API_URL ?? '';
export const WS_BASE = import.meta.env.VITE_WS_URL
  ?? (typeof window !== 'undefined'
    ? `${window.location.protocol === 'https:' ? 'wss' : 'ws'}://${window.location.host}`
    : 'ws://localhost:8000');

// ── Generic fetch wrapper ─────────────────────────

export async function fetchApi<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const detail = await response.text().catch(() => response.statusText);
    throw new Error(`API ${response.status}: ${detail}`);
  }

  return response.json();
}

// ── Typed API functions ───────────────────────────

// Health
export const ping = () => fetchApi<{ status: string; version: string }>('/ping');

// Chat (REST fallback — prefer WebSocket)
export interface ChatResponse {
  response: string;
  conversation_id: string;
  intent?: string;
}
export const postChat = (message: string, conversation_id?: string) =>
  fetchApi<ChatResponse>('/api/chat', {
    method: 'POST',
    body: JSON.stringify({ message, conversation_id }),
  });

// Feedback
export const postFeedback = (conversation_id: string, vote_type: 'positive' | 'negative', message_preview?: string) =>
  fetchApi<{ status: string; vote_type: string }>('/api/feedback', {
    method: 'POST',
    body: JSON.stringify({ conversation_id, vote_type, message_preview }),
  });

// Signals
export interface RawSignal {
  id: string;
  source: string;
  external_id: string;
  payload: {
    title: string;
    content: string;
    url?: string;
    metadata?: Record<string, unknown>;
  };
  content_hash?: string;
  created_at: string;
}
export const getSignals = (source?: string, limit = 20) => {
  const params = new URLSearchParams({ limit: String(limit) });
  if (source && source !== 'all') params.set('source', source);
  return fetchApi<RawSignal[]>(`/api/signals?${params}`);
};

// Intelligence
export interface IntelligenceItem {
  id: string;
  agent_name: string;
  summary: string;
  confidence: number;
  timestamp: string;
}
export const getIntelligence = (agent_name?: string, limit = 20) => {
  const params = new URLSearchParams({ limit: String(limit) });
  if (agent_name) params.set('agent_name', agent_name);
  return fetchApi<IntelligenceItem[]>(`/api/intelligence?${params}`);
};

// Conversations
export const getConversations = (conversation_id: string, limit = 50) =>
  fetchApi<unknown[]>(`/api/conversations/${conversation_id}?limit=${limit}`);

// Recommendations
export interface Recommendation {
  title: string;
  summary: string;
  relevance_score: number;
}
export const getRecommendations = (conversation_id?: string, limit = 5) => {
  const params = new URLSearchParams({ limit: String(limit) });
  if (conversation_id) params.set('conversation_id', conversation_id);
  return fetchApi<Recommendation[]>(`/api/recommendations?${params}`);
};

// Model Router Status
export interface ModelRouterStatus {
  tiers: Record<string, string>;
  total_calls: number;
  total_cost_estimate: number;
  usage_log: Array<{ model: string; input_tokens: number; output_tokens: number; cost: number }>;
}
export const getModelRouterStatus = () =>
  fetchApi<ModelRouterStatus>('/api/model-router/status');

// Alerts Status
export interface AlertsStatus {
  configured_channels: string[];
  total_alerts_sent: number;
  recent_alerts: Array<{ type: string; message: string; severity: string; timestamp: string }>;
}
export const getAlertsStatus = () =>
  fetchApi<AlertsStatus>('/api/alerts/status');

// Ingestion
export const postIngest = (source: string, run_agents = true) =>
  fetchApi<{ status: string; message: string }>('/ingest', {
    method: 'POST',
    body: JSON.stringify({ source, run_agents }),
  });

export const postDailyPulse = () =>
  fetchApi<{ status: string; message: string }>('/daily-pulse', { method: 'POST' });

// Codebase Context
export interface ContextResponse {
  status: string;
  project: string;
  deps_count: number;
  frameworks: string[];
  tech_tags: string[];
}
export const postContext = (project_path: string, project_name?: string) =>
  fetchApi<ContextResponse>('/api/context', {
    method: 'POST',
    body: JSON.stringify({ project_path, project_name }),
  });
