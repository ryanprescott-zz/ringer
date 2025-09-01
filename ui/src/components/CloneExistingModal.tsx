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
    <div 
      className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
      onClick={handleClose}
    >
      <div 
        className="bg-white rounded-lg p-6 max-w-md w-full mx-4"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold">Clone Existing</h3>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        <div className="mb-6">
          <label className="block text-sm font-medium text-gray-700 mb-2">
            Select Crawl to Clone
          </label>
          <select
            value={selectedCrawlId}
            onChange={(e) => setSelectedCrawlId(e.target.value)}
            className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ringer-blue"
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

        <div className="flex justify-end space-x-3">
          <button
            onClick={handleClose}
            className="px-4 py-2 text-gray-700 border border-gray-300 rounded hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleClone}
            disabled={!selectedCrawlId}
            className="px-4 py-2 bg-ringer-blue text-white rounded hover:bg-ringer-dark-blue disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Clone
          </button>
        </div>
      </div>
    </div>
  );
};