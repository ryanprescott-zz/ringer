import React, { useState } from 'react';
import { CrawlInfo } from '../types';

interface CloneExistingModalProps {
  isOpen: boolean;
  crawls: CrawlInfo[];
  onClose: () => void;
  onClone: (crawl: CrawlInfo) => void;
}

export const CloneExistingModal: React.FC<CloneExistingModalProps> = ({
  isOpen,
  crawls,
  onClose,
  onClone,
}) => {
  const [selectedCrawlId, setSelectedCrawlId] = useState<string>('');

  const handleClone = () => {
    const selectedCrawl = crawls.find(
      (crawl) => crawl.crawl_status.crawl_id === selectedCrawlId
    );
    
    if (selectedCrawl) {
      onClone(selectedCrawl);
    }
  };

  const handleClose = () => {
    setSelectedCrawlId('');
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()}>
        <div className="modal-header">
          <h3 className="modal-title">Clone Existing</h3>
          <button
            onClick={handleClose}
            style={{
              background: 'none',
              border: 'none',
              color: 'var(--text-tertiary)',
              fontSize: '1.25rem',
              cursor: 'pointer',
              padding: '0.25rem'
            }}
          >
            ✕
          </button>
        </div>

        <div className="modal-body">
          <label style={{ 
            display: 'block', 
            fontSize: '0.875rem', 
            fontWeight: 500, 
            color: 'var(--text-primary)', 
            marginBottom: '0.5rem' 
          }}>
            Select Crawl to Clone
          </label>
          <select
            value={selectedCrawlId}
            onChange={(e) => setSelectedCrawlId(e.target.value)}
            className="input-field"
            style={{ width: '100%' }}
          >
            <option value="">Choose a crawl...</option>
            {crawls.map((crawl) => (
              <option 
                key={crawl.crawl_status.crawl_id} 
                value={crawl.crawl_status.crawl_id}
              >
                {crawl.crawl_spec.name}
              </option>
            ))}
          </select>
        </div>

        <div className="modal-footer">
          <button onClick={handleClose} className="btn-secondary">
            Cancel
          </button>
          <button 
            onClick={handleClone} 
            disabled={!selectedCrawlId}
            className="btn-primary"
            style={{ opacity: selectedCrawlId ? 1 : 0.5 }}
          >
            Clone
          </button>
        </div>
      </div>
    </div>
  );
};