import React, { useState } from 'react';
import { CrawlSpec, CrawlInfo } from '../types';
import { crawlApi } from '../services/api';

interface OverviewTabProps {
  crawlSpec: CrawlSpec | null;
  isNewCrawl: boolean;
  selectedCrawl: CrawlInfo | null;
  onCrawlSpecChange: (spec: CrawlSpec) => void;
  onCrawlCreated: () => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({
  crawlSpec,
  isNewCrawl,
  selectedCrawl,
  onCrawlSpecChange,
  onCrawlCreated,
}) => {
  const [description, setDescription] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleNameChange = (name: string) => {
    if (crawlSpec) {
      onCrawlSpecChange({ ...crawlSpec, name });
    }
  };

  const handleSubmitCrawl = async () => {
    if (!crawlSpec || !crawlSpec.name.trim()) {
      setError('Crawl name is required');
      return;
    }

    if (crawlSpec.seeds.length === 0) {
      setError('At least one seed URL is required');
      return;
    }

    setLoading(true);
    setError(null);
    try {
      await crawlApi.createCrawl({ crawl_spec: crawlSpec });
      onCrawlCreated();
    } catch (err) {
      setError('Failed to create crawl');
    } finally {
      setLoading(false);
    }
  };

  const handleExportParams = async () => {
    if (selectedCrawl) {
      try {
        await crawlApi.exportCrawlSpec(selectedCrawl.crawl_status.crawl_id);
      } catch (err) {
        setError('Failed to export crawl spec');
      }
    }
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}

      <div className="flex justify-between items-start">
        <div className="flex-1 space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Name
            </label>
            <input
              type="text"
              value={crawlSpec?.name || ''}
              onChange={(e) => handleNameChange(e.target.value)}
              disabled={!isNewCrawl}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-prospector-blue disabled:bg-gray-100"
              placeholder="Enter crawl name..."
            />
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              disabled={!isNewCrawl}
              rows={8}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-prospector-blue disabled:bg-gray-100"
              placeholder="Enter crawl description..."
            />
          </div>
        </div>

        <div className="ml-6 space-y-3">
          {isNewCrawl && (
            <button
              onClick={handleSubmitCrawl}
              disabled={loading}
              className="px-4 py-2 bg-prospector-blue text-white rounded hover:bg-prospector-dark-blue disabled:opacity-50"
            >
              {loading ? 'Submitting...' : 'Submit Crawl'}
            </button>
          )}
          
          {selectedCrawl && (
            <button
              onClick={handleExportParams}
              className="px-4 py-2 bg-prospector-blue text-white rounded hover:bg-prospector-dark-blue"
            >
              Export Params
            </button>
          )}
        </div>
      </div>
    </div>
  );
};
