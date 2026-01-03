import { FeedItem, ServerStatus, SyncType } from "../types";

export const ApiService = {
  checkStatus: async (): Promise<ServerStatus> => {
    try {
      // Simple ping to check if server is awake
      const res = await fetch('/ping');
      if (res.ok) return ServerStatus.ONLINE;
      return ServerStatus.ERROR;
    } catch (e) {
      return ServerStatus.ERROR;
    }
  },

  triggerPulse: async (): Promise<{ message: string, items: FeedItem[] }> => {
    const res = await fetch('/daily-pulse', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source: 'manual_ui', run_agents: true })
    });

    if (!res.ok) throw new Error("Failed to trigger pulse");

    const data = await res.json();
    return {
      message: data.message || "Pipeline triggered",
      items: [] // The real API implementation might need to return items or we fetch them separately
    };
  },

  syncSource: async (source: SyncType): Promise<string> => {
    const res = await fetch('/ingest', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ source: source, run_agents: false })
    });

    if (!res.ok) throw new Error(`Failed to sync ${source}`);

    const data = await res.json();
    return data.message || `Synced ${source}`;
  }
};