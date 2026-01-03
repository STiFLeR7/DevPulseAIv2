import React, { useEffect, useRef } from 'react';
import { LogEntry } from '../types';

interface LogConsoleProps {
  logs: LogEntry[];
}

export const LogConsole: React.FC<LogConsoleProps> = ({ logs }) => {
  const scrollRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs]);

  return (
    <div className="mt-8 border-t border-slate-800 pt-8 animate-fade-in">
      <div className="bg-slate-950 rounded-t-lg border border-slate-800 border-b-0 p-2 flex items-center gap-2">
        <div className="flex gap-1.5 ml-2">
          <div className="w-2.5 h-2.5 rounded-full bg-slate-700"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-slate-700"></div>
          <div className="w-2.5 h-2.5 rounded-full bg-slate-700"></div>
        </div>
        <div className="flex-1 text-center text-xs text-slate-500 font-mono">system_logs.log</div>
      </div>
      
      <div 
        ref={scrollRef}
        className="terminal-scroll h-48 overflow-y-auto bg-black border border-slate-800 rounded-b-lg p-4 font-mono text-xs md:text-sm leading-relaxed"
      >
        {logs.length === 0 && (
          <span className="text-slate-600">Waiting for system events...</span>
        )}
        
        {logs.map((log) => (
          <div key={log.id} className="mb-1 flex">
            <span className="text-slate-600 mr-3 select-none">[{log.timestamp}]</span>
            <span className={`
              ${log.type === 'info' ? 'text-slate-300' : ''}
              ${log.type === 'success' ? 'text-emerald-400' : ''}
              ${log.type === 'warning' ? 'text-orange-400' : ''}
              ${log.type === 'error' ? 'text-red-400' : ''}
            `}>
              {log.type === 'success' && '✓ '}
              {log.type === 'error' && '✗ '}
              {log.type === 'warning' && '⚠ '}
              {log.type === 'info' && '> '}
              {log.message}
            </span>
          </div>
        ))}
        <div className="animate-pulse text-cyan-500 mt-1">_</div>
      </div>
    </div>
  );
};