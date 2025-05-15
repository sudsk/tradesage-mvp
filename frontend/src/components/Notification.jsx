import React, { useState, useEffect } from 'react';

const Notification = ({ message, type = 'success', duration = 5000, onClose }) => {
  const [visible, setVisible] = useState(true);
  const [isLeaving, setIsLeaving] = useState(false);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsLeaving(true);
      setTimeout(() => {
        setVisible(false);
        onClose && onClose();
      }, 300);
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  if (!visible) return null;

  const getTypeStyles = () => {
    switch (type) {
      case 'success':
        return {
          background: 'bg-gradient-to-r from-green-50 to-emerald-50',
          border: 'border-green-200',
          text: 'text-green-800',
          icon: '✅',
          iconBg: 'bg-green-100',
          iconColor: 'text-green-600'
        };
      case 'error':
        return {
          background: 'bg-gradient-to-r from-red-50 to-pink-50',
          border: 'border-red-200',
          text: 'text-red-800',
          icon: '❌',
          iconBg: 'bg-red-100',
          iconColor: 'text-red-600'
        };
      case 'warning':
        return {
          background: 'bg-gradient-to-r from-yellow-50 to-orange-50',
          border: 'border-yellow-200',
          text: 'text-yellow-800',
          icon: '⚠️',
          iconBg: 'bg-yellow-100',
          iconColor: 'text-yellow-600'
        };
      case 'info':
        return {
          background: 'bg-gradient-to-r from-blue-50 to-indigo-50',
          border: 'border-blue-200',
          text: 'text-blue-800',
          icon: 'ℹ️',
          iconBg: 'bg-blue-100',
          iconColor: 'text-blue-600'
        };
      default:
        return {
          background: 'bg-gradient-to-r from-gray-50 to-slate-50',
          border: 'border-gray-200',
          text: 'text-gray-800',
          icon: '📝',
          iconBg: 'bg-gray-100',
          iconColor: 'text-gray-600'
        };
    }
  };

  const styles = getTypeStyles();

  const getProgressColor = () => {
    switch (type) {
      case 'success': return 'from-green-500 to-emerald-600';
      case 'error': return 'from-red-500 to-pink-600';
      case 'warning': return 'from-yellow-500 to-orange-600';
      case 'info': return 'from-blue-500 to-indigo-600';
      default: return 'from-gray-500 to-slate-600';
    }
  };

  return (
    <div className="fixed top-4 right-4 z-50 space-y-2">
      <div
        className={`
          flex items-start p-4 rounded-xl border shadow-lg max-w-md backdrop-blur-sm
          ${styles.background} ${styles.border}
          ${isLeaving ? 'transform translate-x-full opacity-0' : 'transform translate-x-0 opacity-100'}
          transition-all duration-300 ease-in-out
        `}
      >
        {/* Icon */}
        <div className={`flex-shrink-0 w-10 h-10 rounded-lg ${styles.iconBg} flex items-center justify-center mr-3`}>
          <span className="text-lg">{styles.icon}</span>
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <p className={`text-sm font-semibold ${styles.text} leading-relaxed`}>
            {message}
          </p>
          
          {/* Progress bar */}
          <div className="w-full bg-gray-200 rounded-full h-1 mt-3 overflow-hidden">
            <div
              className={`h-1 bg-gradient-to-r ${getProgressColor()} rounded-full transition-all duration-[${duration}ms] ease-linear`}
              style={{
                animation: `shrink ${duration}ms linear forwards`
              }}
            />
          </div>
        </div>

        {/* Close button */}
        <button
          className={`flex-shrink-0 ml-3 p-1 rounded-lg hover:bg-gray-100 transition-colors ${styles.iconColor}`}
          onClick={() => {
            setIsLeaving(true);
            setTimeout(() => {
              setVisible(false);
              onClose && onClose();
            }, 300);
          }}
          aria-label="Close notification"
        >
          <svg className="w-5 h-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd" />
          </svg>
        </button>
      </div>

      <style jsx>{`
        @keyframes shrink {
          from { width: 100%; }
          to { width: 0%; }
        }
      `}</style>
    </div>
  );
};

export default Notification;
