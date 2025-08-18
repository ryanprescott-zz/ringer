import React, { useState } from 'react';
import { SearchEngineSeed } from '../types';
import { crawlApi } from '../services/api';

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
  const [error, setError] = useState<string | null>(null);

  const handleRunQuery = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setError(null);
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
    } catch (err) {
      setError('Failed to collect seed URLs');
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
    onAddUrls(Array.from(selectedUrls));
    handleClose();
  };

  const handleClose = () => {
    setQuery('');
    setResults([]);
    setSelectedUrls(new Set());
    setError(null);
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg p-6 max-w-4xl w-full mx-4 max-h-[80vh] overflow-y-auto">
        <div className="flex justify-between items-center mb-6">
          <h3 className="text-lg font-semibold">Search Engine Seed Collection</h3>
          <button
            onClick={handleClose}
            className="text-gray-400 hover:text-gray-600"
          >
            ✕
          </button>
        </div>

        <div className="grid grid-cols-4 gap-4 mb-6">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Search Engine
            </label>
            <select
              value={searchEngine}
              onChange={(e) => setSearchEngine(e.target.value)}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-prospector-blue"
            >
              <option value="Google">Google</option>
              <option value="Bing">Bing</option>
              <option value="DuckDuckGo">DuckDuckGo</option>
            </select>
          </div>
          
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Count
            </label>
            <input
              type="number"
              value={count}
              onChange={(e) => setCount(parseInt(e.target.value) || 10)}
              min="1"
              max="100"
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-prospector-blue"
            />
          </div>
          
          <div className="col-span-2">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Query
            </label>
            <div className="flex">
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Enter search query..."
                className="flex-1 px-3 py-2 border border-gray-300 rounded-l-md focus:outline-none focus:ring-2 focus:ring-prospector-blue"
                onKeyPress={(e) => e.key === 'Enter' && handleRunQuery()}
              />
              <button
                onClick={handleRunQuery}
                disabled={loading || !query.trim()}
                className="px-4 py-2 bg-prospector-blue text-white rounded-r-md hover:bg-prospector-dark-blue disabled:opacity-50"
              >
                {loading ? 'Running...' : 'Run Query'}
              </button>
            </div>
          </div>
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {results.length > 0 && (
          <div>
            <h4 className="text-md font-medium mb-3">Results</h4>
            <div className="border border-gray-300 rounded-md max-h-60 overflow-y-auto">
              {results.map((url, index) => (
                <div
                  key={index}
                  className="flex items-center p-3 border-b border-gray-200 last:border-b-0"
                >
                  <input
                    type="checkbox"
                    checked={selectedUrls.has(url)}
                    onChange={() => handleUrlToggle(url)}
                    className="mr-3"
                  />
                  <span className="flex-1 text-sm">{url}</span>
                </div>
              ))}
            </div>
            
            <div className="flex justify-end mt-4">
              <button
                onClick={handleAddSelected}
                disabled={selectedUrls.size === 0}
                className="px-4 py-2 bg-prospector-blue text-white rounded hover:bg-prospector-dark-blue disabled:opacity-50"
              >
                Add Selected ({selectedUrls.size})
              </button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
