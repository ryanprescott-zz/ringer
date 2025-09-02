import React, { useState } from 'react';
import { crawlApi } from '../services/api';
import { useToast } from '../hooks/useToast';

interface SearchEngineModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddUrls: (urls: string[]) => void;
}

export const SearchEngineModal: React.FC<SearchEngineModalProps> = ({
  isOpen,
  onClose,
  onAddUrls,
}) => {
  const [searchEngine, setSearchEngine] = useState('Google');
  const [query, setQuery] = useState('');
  const [count, setCount] = useState(10);
  const [results, setResults] = useState<string[]>([]);
  const [selectedUrls, setSelectedUrls] = useState<Set<string>>(new Set());
  const [loading, setLoading] = useState(false);
  const { showSuccess, showError } = useToast();

  const handleRunQuery = async () => {
    if (!query.trim()) return;

    setLoading(true);
    try {
      const response = await crawlApi.collectSeedUrls({
        search_engine_seeds: [{
          search_engine: searchEngine,
          query: query.trim(),
          result_count: count,
        }],
      });
      
      setResults(response.seed_urls);
      setSelectedUrls(new Set(response.seed_urls)); // Select all by default
      showSuccess('Search Complete', `Found ${response.seed_urls.length} URLs`);
    } catch (err) {
      showError('Search Failed', 'Failed to collect seed URLs from search engine');
    } finally {
      setLoading(false);
    }
  };

  const handleUrlToggle = (url: string) => {
    const newSelected = new Set(selectedUrls);
    if (newSelected.has(url)) {
      newSelected.delete(url);
    } else {
      newSelected.add(url);
    }
    setSelectedUrls(newSelected);
  };

  const handleAddSelected = () => {
    const urlsToAdd = Array.from(selectedUrls);
    onAddUrls(urlsToAdd);
    showSuccess('URLs Added', `Added ${urlsToAdd.length} URLs to source list`);
    handleClose();
  };

  const handleClose = () => {
    setQuery('');
    setResults([]);
    setSelectedUrls(new Set());
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="modal-overlay" onClick={handleClose}>
      <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '48rem', width: '95%' }}>
        <div className="modal-header">
          <h3 className="modal-title">Search Engine</h3>
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

        <div className="modal-body" style={{ padding: '1.5rem' }}>
          {/* Search Form */}
          <div style={{ 
            display: 'flex', 
            alignItems: 'flex-end', 
            gap: '1rem', 
            marginBottom: '1.5rem',
            flexWrap: 'wrap'
          }}>
            <div>
              <label style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: '600',
                color: 'var(--text-primary)',
                marginBottom: '0.5rem'
              }}>
                Search Engine
              </label>
              <select
                value={searchEngine}
                onChange={(e) => setSearchEngine(e.target.value)}
                className="input-field"
                style={{ minWidth: '120px' }}
              >
                <option value="Google">Google</option>
                <option value="Bing">Bing</option>
                <option value="DuckDuckGo">DuckDuckGo</option>
              </select>
            </div>
            
            <div>
              <label style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: '600',
                color: 'var(--text-primary)',
                marginBottom: '0.5rem'
              }}>
                Count
              </label>
              <input
                type="number"
                value={count}
                onChange={(e) => setCount(parseInt(e.target.value) || 10)}
                min="1"
                max="100"
                className="input-field"
                style={{ width: '80px' }}
              />
            </div>
            
            <div style={{ flex: 1, minWidth: '200px' }}>
              <label style={{
                display: 'block',
                fontSize: '0.875rem',
                fontWeight: '600',
                color: 'var(--text-primary)',
                marginBottom: '0.5rem'
              }}>
                Query
              </label>
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter search query..."
                className="input-field"
                style={{ width: '100%' }}
                onKeyPress={(e) => e.key === 'Enter' && handleRunQuery()}
              />
            </div>
            
            <button
              onClick={handleRunQuery}
              disabled={loading || !query.trim()}
              className="btn-primary"
            >
              {loading ? 'Running...' : 'Run Query'}
            </button>
          </div>

          {results.length > 0 && (
            <div>
              <h4 style={{
                fontSize: '1rem',
                fontWeight: '600',
                color: 'var(--text-primary)',
                marginBottom: '0.75rem',
                margin: '0 0 0.75rem 0'
              }}>
                Results
              </h4>
              <div className="table-container" style={{ 
                maxHeight: '300px', 
                overflow: 'auto',
                marginBottom: '1.5rem'
              }}>
                {results.map((url, index) => (
                  <div
                    key={index}
                    style={{
                      display: 'flex',
                      alignItems: 'center',
                      padding: '0.75rem',
                      borderBottom: index < results.length - 1 ? '1px solid var(--border-secondary)' : 'none'
                    }}
                  >
                    <input
                      type="checkbox"
                      checked={selectedUrls.has(url)}
                      onChange={() => handleUrlToggle(url)}
                      style={{ 
                        marginRight: '0.75rem',
                        transform: 'scale(1.2)'
                      }}
                    />
                    <span style={{ 
                      flex: 1, 
                      fontSize: '0.875rem',
                      color: 'var(--text-primary)',
                      wordBreak: 'break-all'
                    }}>
                      {url}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {results.length > 0 && (
          <div className="modal-footer">
            <button onClick={handleClose} className="btn-secondary">
              Cancel
            </button>
            <button
              onClick={handleAddSelected}
              disabled={selectedUrls.size === 0}
              className="btn-primary"
              style={{ opacity: selectedUrls.size > 0 ? 1 : 0.5 }}
            >
              Add Selected ({selectedUrls.size})
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
