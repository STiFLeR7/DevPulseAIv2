import React, { useEffect } from 'react';
import { LogEntry } from '../types';

interface ToastContainerProps {
  toasts: LogEntry[];
  removeToast: (id: string) => void;
}

export const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, removeToast }) => {
  return (
    <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-3 pointer-events-none">
      {toasts.map((toast) => (
        <ToastItem key={toast.id} toast={toast} onRemove={() => removeToast(toast.id)} />
      ))}
    </div>
  );
};

interface ToastItemProps {
  toast: LogEntry;
  onRemove: () => void;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, onRemove }) => {
  // Auto-dismiss after 4 seconds
  useEffect(() => {
    const timer = setTimeout(() => {
      onRemove();
    }, 4000);
    return () => clearTimeout(timer);
  }, [onRemove]);

  const getStyle = () => {
    switch (toast.type) {
      case 'success':
        return 'bg-emerald-950/90 border-emerald-500/40 text-emerald-400 shadow-[0_0_15px_rgba(16,185,129,0.1)]';
      case 'error':
        return 'bg-red-950/90 border-red-500/40 text-red-400 shadow-[0_0_15px_rgba(239,68,68,0.1)]';
      case 'warning':
        return 'bg-orange-950/90 border-orange-500/40 text-orange-400 shadow-[0_0_15px_rgba(249,115,22,0.1)]';
      case 'info':
      default:
        return 'bg-slate-900/90 border-cyan-500/40 text-cyan-400 shadow-[0_0_15px_rgba(6,182,212,0.1)]';
    }
  };

  const getIcon = () => {
    switch (toast.type) {
      case 'success': return 'fa-check-circle';
      case 'error': return 'fa-circle-xmark';
      case 'warning': return 'fa-triangle-exclamation';
      case 'info': default: return 'fa-circle-info';
    }
  };

  return (
    <div className={`
      pointer-events-auto
      flex items-start gap-3 px-4 py-3 rounded-lg border backdrop-blur-md
      transform transition-all duration-300 animate-slide-up
      min-w-[300px] max-w-sm
      ${getStyle()}
    `}>
      <i className={`fas ${getIcon()} text-lg mt-0.5`}></i>
      <div className="flex-1">
        <h4 className="text-sm font-semibold capitalize mb-0.5">{toast.type}</h4>
        <p className="text-xs opacity-90 leading-relaxed font-sans">{toast.message}</p>
        <p className="text-[10px] opacity-60 font-mono mt-1">{toast.timestamp}</p>
      </div>
      <button 
        onClick={onRemove} 
        className="text-current opacity-50 hover:opacity-100 transition-opacity p-1 hover:bg-white/5 rounded"
      >
        <i className="fas fa-times text-xs"></i>
      </button>
    </div>
  );
};