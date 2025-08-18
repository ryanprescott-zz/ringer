import React, { useEffect } from 'react';

export interface ToastProps {
  id: string;
  type: 'success' | 'error' | 'info' | 'warning';
  title: string;
  message?: string;
  duration?: number;
  onClose: (id: string) => void;
}

export const Toast: React.FC<ToastProps> = ({
  id,
  type,
  title,
  message,
  duration = 5000,
  onClose,
}) => {
  useEffect(() => {
    const timer = setTimeout(() => {
      onClose(id);
    }, duration);

    return () => clearTimeout(timer);
  }, [id, duration, onClose]);

  const getTypeStyles = () => {
    switch (type) {
      case 'success':
        return 'bg-green-100 border-green-400 text-green-700';
      case 'error':
        return 'bg-red-100 border-red-400 text-red-700';
      case 'warning':
        return 'bg-yellow-100 border-yellow-400 text-yellow-700';
      case 'info':
      default:
        return 'bg-blue-100 border-blue-400 text-blue-700';
    }
  };

  const getIcon = () => {
    switch (type) {
      case 'success':
        return '✓';
      case 'error':
        return '✕';
      case 'warning':
        return '⚠';
      case 'info':
      default:
        return 'ℹ';
    }
  };

  return (
    <div className={`border px-4 py-3 rounded mb-2 shadow-lg ${getTypeStyles()}`}>
      <div className="flex items-start">
        <span className="text-lg mr-3">{getIcon()}</span>
        <div className="flex-1">
          <div className="font-medium">{title}</div>
          {message && <div className="text-sm mt-1">{message}</div>}
        </div>
        <button
          onClick={() => onClose(id)}
          className="ml-3 text-lg hover:opacity-70"
        >
          ×
        </button>
      </div>
    </div>
  );
};
