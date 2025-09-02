import React, { useState } from 'react';
import { CrawlSpec, CrawlInfo } from '../types';
import { crawlApi } from '../services/api';
import { useToast } from '../hooks/useToast';

interface OverviewTabProps {
  crawlSpec: CrawlSpec | null;
  isNewCrawl: boolean;
  selectedCrawl: CrawlInfo | null;
  existingCrawls: CrawlInfo[];
  onCrawlSpecChange: (spec: CrawlSpec) => void;
  onCrawlCreated: () => void;
}

export const OverviewTab: React.FC<OverviewTabProps> = ({
  crawlSpec,
  isNewCrawl,
  selectedCrawl,
  existingCrawls,
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

    // Check for duplicate names
    const isDuplicateName = existingCrawls.some(
      (crawl) => crawl.crawl_spec.name.toLowerCase() === crawlSpec.name.toLowerCase()
    );
    
    if (isDuplicateName) {
      showError('Validation Error', 'A crawl with this name already exists. Please choose a different name.');
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
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
        <div>
          <label style={{ 
            display: 'block', 
            fontSize: '0.875rem', 
            fontWeight: '600', 
            color: 'var(--text-primary)', 
            marginBottom: '0.5rem' 
          }}>
            Name
          </label>
          <input
            type="text"
            value={crawlSpec?.name || ''}
            onChange={(e) => handleNameChange(e.target.value)}
            disabled={!isNewCrawl}
            className="input-field"
            style={{ 
              width: '100%',
              padding: '0.75rem 1rem',
              borderRadius: '0.5rem'
            }}
            placeholder="Enter crawl name..."
          />
        </div>

        <div>
          <label style={{ 
            display: 'block', 
            fontSize: '0.875rem', 
            fontWeight: '600', 
            color: 'var(--text-primary)', 
            marginBottom: '0.5rem' 
          }}>
            Description
          </label>
          <textarea
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            disabled={!isNewCrawl}
            rows={6}
            className="input-field"
            style={{ 
              width: '100%',
              padding: '0.75rem 1rem',
              borderRadius: '0.5rem',
              resize: 'vertical'
            }}
            placeholder="Enter crawl description..."
          />
        </div>

        <div style={{ display: 'flex', alignItems: 'flex-end', gap: '1rem' }}>
          <div>
            <label style={{ 
              display: 'block', 
              fontSize: '0.875rem', 
              fontWeight: '600', 
              color: 'var(--text-primary)', 
              marginBottom: '0.5rem' 
            }}>
              Worker Count
            </label>
            <input
              type="number"
              value={crawlSpec?.worker_count || 1}
              onChange={(e) => handleWorkerCountChange(parseInt(e.target.value) || 1)}
              disabled={!isNewCrawl}
              min="1"
              max="16"
              className="input-field"
              style={{ 
                width: '8rem',
                padding: '0.75rem 1rem',
                borderRadius: '0.5rem'
              }}
            />
          </div>
          
          {isNewCrawl && (
            <button
              onClick={handleSubmitCrawl}
              disabled={loading}
              className="btn-primary"
              style={{ marginLeft: 'auto' }}
            >
              {loading ? 'Creating...' : 'Create Crawl'}
            </button>
          )}
        </div>
      </div>
      
      {selectedCrawl && (
        <button
          onClick={handleExportParams}
          className="btn-primary"
          style={{ marginLeft: '2rem' }}
        >
          Export Params
        </button>
      )}
    </div>
  );
};
