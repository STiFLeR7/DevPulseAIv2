import React, { useState, useEffect, useCallback } from 'react';
import { Header } from './components/Header';
import { ControlPanel } from './components/ControlPanel';
import { FeedGrid } from './components/FeedGrid';
import { LogConsole } from './components/LogConsole';
import { ToastContainer } from './components/ToastContainer'; // Imported ToastContainer
import { ApiService } from './services/mockApi';
import { ServerStatus, LogEntry, FeedItem, SyncType } from './types';
import { INITIAL_LOGS } from './constants';

const App: React.FC = () => {
  const [status, setStatus] = useState<ServerStatus>(ServerStatus.CHECKING);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [toasts, setToasts] = useState<LogEntry[]>([]); // New State for Toasts
  const [feedItems, setFeedItems] = useState<FeedItem[]>([]);
  const [loadingState, setLoadingState] = useState<Record<string, boolean>>({});

  // Helper to add logs and optionally show toasts
  const addLog = useCallback((message: string, type: LogEntry['type'] = 'info') => {
    const timestamp = new Date().toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    const newEntry: LogEntry = {
      id: Math.random().toString(36).substr(2, 9),
      timestamp,
      message,
      type
    };

    setLogs(prev => [...prev, newEntry]);

    // Show toast for non-info logs (Success, Warning, Error)
    if (type !== 'info') {
      setToasts(prev => [...prev, newEntry]);
    }
  }, []);

  const removeToast = useCallback((id: string) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  // Initial Check
  useEffect(() => {
    // Load initial logs
    INITIAL_LOGS.forEach(log => addLog(log, 'info'));

    const init = async () => {
      // If the first check takes long (simulated inside ApiService), we update UI to WAKING_UP
      const checkPromise = ApiService.checkStatus();
      
      // Race condition to show "Waking Up" if it takes > 2s
      const timeoutId = setTimeout(() => {
        setStatus(ServerStatus.WAKING_UP);
        addLog("Server returned from dormancy. Warming up containers...", "warning");
      }, 2000);

      try {
        const result = await checkPromise;
        clearTimeout(timeoutId);
        setStatus(result);
        addLog("Connection established. System Online.", "success");
      } catch (e) {
        clearTimeout(timeoutId);
        setStatus(ServerStatus.ERROR);
        addLog("Failed to connect to backend.", "error");
      }
    };

    init();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  // Handle Sync Actions
  const handleSync = async (type: SyncType) => {
    if (status === ServerStatus.CHECKING || status === ServerStatus.WAKING_UP) return;

    setLoadingState(prev => ({ ...prev, [type]: true }));
    
    try {
      if (type === 'daily') {
        addLog("Triggering Daily Pulse sequence...", "info");
        const response = await ApiService.triggerPulse();
        setFeedItems(response.items);
        addLog(`Pulse complete. Received ${response.items.length} new signals.`, "success");
      } else {
        addLog(`Initiating sync for ${type}...`, "info");
        const msg = await ApiService.syncSource(type);
        addLog(msg, "success");
      }
    } catch (error) {
      addLog(`Operation failed for ${type}`, "error");
    } finally {
      setLoadingState(prev => ({ ...prev, [type]: false }));
    }
  };

  return (
    <div className="min-h-screen bg-slate-950 text-slate-100 flex flex-col relative">
      <Header status={status} />
      
      {/* Toast Overlay */}
      <ToastContainer toasts={toasts} removeToast={removeToast} />
      
      <main className="flex-1 max-w-7xl w-full mx-auto px-6 py-8">
        <ControlPanel 
          onSync={handleSync} 
          loadingState={loadingState} 
          disabled={status !== ServerStatus.ONLINE}
        />

        <div className="mt-8">
          <FeedGrid 
            items={feedItems} 
            loading={loadingState['daily'] || false} 
          />
        </div>

        <LogConsole logs={logs} />
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-900 py-6 mt-12">
        <div className="max-w-7xl mx-auto px-6 text-center text-xs text-slate-600 font-mono">
          DevPulseAI v2.0 &bull; Running on Render Free Tier &bull; <span className="text-cyan-900">NO PURPLE ALLOWED</span>
        </div>
      </footer>
    </div>
  );
};

export default App;