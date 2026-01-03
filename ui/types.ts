export enum ServerStatus {
  CHECKING = 'CHECKING',
  ONLINE = 'ONLINE',
  WAKING_UP = 'WAKING_UP',
  ERROR = 'ERROR'
}

export interface LogEntry {
  id: string;
  timestamp: string;
  message: string;
  type: 'info' | 'success' | 'warning' | 'error';
}

export interface FeedItem {
  id: string;
  title: string;
  source: string;
  type: 'repo' | 'paper' | 'article';
  url: string;
  timestamp: string;
}

export type SyncType = 'daily' | 'github' | 'arxiv' | 'medium';