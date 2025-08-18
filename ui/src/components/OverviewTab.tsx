import React, { useState } from 'react';
import { CrawlSpec, CrawlInfo } from '../types';
import { crawlApi } from '../services/api';
import { useToast } from '../hooks/useToast';

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
  const { showSuccess, showError } = useToast();

  const handleNameChange = (name: string) => {
    if (crawlSpec) {
      onCrawlSpecChange({ ...crawlSpec, name });
    }
  };

  const handleWorkerCountChange = (workerCount: number) => {
    if (crawlSpec) {
      onCrawlSpecChange({ ...crawlSpec, worker_count: workerCount });
    }
  };

  const handleSubmitCrawl = async () => {
    if (!crawlSpec || !crawlSpec.name.trim()) {
      showError('Validation Error', 'Crawl name is required');
      return;
    }

    if (crawlSpec.seeds.length === 0) {
      showError('Validation Error', 'At least one seed URL is required');
      return;
    }

    if (crawlSpec.worker_count < 1 || crawlSpec.worker_count > 16) {
      showError('Validation Error', 'Worker count must be between 1 and 16');
      return;
    }

    setLoading(true);
    try {
      await crawlApi.createCrawl({ crawl_spec: crawlSpec });
      showSuccess('Crawl Created', `Successfully created crawl "${crawlSpec.name}"`);
      onCrawlCreated();
    } catch (err) {
      showError('Creation Failed', 'Failed to create crawl');
    } finally {
      setLoading(false);
    }
  };

  const handleExportParams = async () => {
    if (selectedCrawl) {
      try {
        await crawlApi.exportCrawlSpec(selectedCrawl.crawl_status.crawl_id);
        showSuccess('Export Started', 'Crawl specification download started');
      } catch (err) {
        showError('Export Failed', 'Failed to export crawl specification');
      }
    }
  };

  return (
    <div className="space-y-6">
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
              rows={6}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-prospector-blue disabled:bg-gray-100"
              placeholder="Enter crawl description..."
            />
          </div>

          <div className="flex items-end space-x-3">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Worker Count
              </label>
              <input
                type="number"
                value={crawlSpec?.worker_count || 1}
                onChange={(e) => handleWorkerCountChange(parseInt(e.target.value) || 1)}
                disabled={!isNewCrawl}
                min="1"
                max="16"
                className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-prospector-blue disabled:bg-gray-100"
              />
            </div>
            
            {isNewCrawl && (
              <button
                onClick={handleSubmitCrawl}
                disabled={loading}
                className="px-4 py-2 bg-prospector-blue text-white rounded hover:bg-prospector-dark-blue disabled:opacity-50"
              >
                {loading ? 'Creating...' : 'Create Crawl'}
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
    </div>
  );
};
