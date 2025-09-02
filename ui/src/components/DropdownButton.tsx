import React, { useState, useRef, useEffect } from 'react';

interface DropdownItem {
  id: string;
  label: string;
  disabled?: boolean;
  onClick: () => void;
}

interface DropdownButtonProps {
  children: React.ReactNode;
  onMainClick: () => void;
  items: DropdownItem[];
}

export const DropdownButton: React.FC<DropdownButtonProps> = ({
  children,
  onMainClick,
  items,
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleItemClick = (item: DropdownItem) => {
    if (!item.disabled) {
      item.onClick();
      setIsOpen(false);
    }
  };

  return (
    <div style={{ position: 'relative', display: 'inline-block' }} ref={dropdownRef}>
      <div style={{ display: 'flex' }}>
        {/* Main button */}
        <button
          onClick={onMainClick}
          className="btn-primary"
          style={{ borderRadius: '0.5rem 0 0 0.5rem' }}
        >
          {children}
        </button>
        
        {/* Dropdown toggle */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className="btn-primary"
          style={{
            borderRadius: '0 0.5rem 0.5rem 0',
            borderLeft: '1px solid rgba(255, 255, 255, 0.2)',
            paddingLeft: '0.75rem',
            paddingRight: '0.75rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center'
          }}
        >
          <svg 
            className={`dropdown-icon ${isOpen ? 'open' : ''}`}
            viewBox="0 0 24 24"
          >
            <path d="M19 9l-7 7-7-7" />
          </svg>
        </button>
      </div>

      {/* Dropdown menu */}
      {isOpen && (
        <div style={{
          position: 'absolute',
          left: 0,
          top: 'calc(100% + 0.25rem)',
          minWidth: '12rem',
          background: 'var(--bg-tertiary)',
          backdropFilter: 'blur(20px)',
          border: '1px solid var(--border-primary)',
          borderRadius: '0.75rem',
          boxShadow: 'var(--shadow-primary)',
          zIndex: 10
        }}>
          <div style={{ padding: '0.5rem' }}>
            {items.map((item) => (
              <button
                key={item.id}
                onClick={() => handleItemClick(item)}
                disabled={item.disabled}
                className="btn-secondary"
                style={{
                  width: '100%',
                  textAlign: 'left',
                  fontSize: '0.875rem',
                  opacity: item.disabled ? 0.5 : 1,
                  cursor: item.disabled ? 'not-allowed' : 'pointer',
                  marginBottom: '0.25rem'
                }}
              >
                {item.label}
              </button>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};