import React, { useState } from 'react';
import { CrawlInfo, SortConfig } from '../types';
import { sortCrawls } from '../utils/sorting';
import { ConfirmDialog } from './ConfirmDialog';
import { crawlApi } from '../services/api';

interface CrawlTableProps {
  crawls: CrawlInfo[];
  selectedCrawl: CrawlInfo | null;
  onSelectCrawl: (crawl: CrawlInfo | null) => void;
}

export const CrawlTable: React.FC<CrawlTableProps> = ({
  crawls,
  selectedCrawl,
  onSelectCrawl,
}) => {
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: 'name', direction: 'asc' });
  const [deleteDialog, setDeleteDialog] = useState<{ isOpen: boolean; crawl: CrawlInfo | null }>({
    isOpen: false,
    crawl: null,
  });
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);

  const sortedCrawls = sortCrawls(crawls, sortConfig);

  const handleSort = (key: string) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const handleStartCrawl = async (crawl: CrawlInfo) => {
    setActionLoading(crawl.crawl_status.crawl_id);
    setError(null);
    try {
      await crawlApi.startCrawl({ crawl_id: crawl.crawl_status.crawl_id });
    } catch (err) {
      setError('Failed to start crawl');
    } finally {
      setActionLoading(null);
    }
  };

  const handleStopCrawl = async (crawl: CrawlInfo) => {
    setActionLoading(crawl.crawl_status.crawl_id);
    setError(null);
    try {
      await crawlApi.stopCrawl({ crawl_id: crawl.crawl_status.crawl_id });
    } catch (err) {
      setError('Failed to stop crawl');
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteCrawl = async () => {
    if (!deleteDialog.crawl) return;
    
    setActionLoading(deleteDialog.crawl.crawl_status.crawl_id);
    setError(null);
    try {
      await crawlApi.deleteCrawl({ crawl_id: deleteDialog.crawl.crawl_status.crawl_id });
      setDeleteDialog({ isOpen: false, crawl: null });
      if (selectedCrawl?.crawl_status.crawl_id === deleteDialog.crawl.crawl_status.crawl_id) {
        onSelectCrawl(null);
      }
    } catch (err) {
      setError('Failed to delete crawl');
    } finally {
      setActionLoading(null);
    }
  };

  const formatDate = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const getResultsSummary = (status: CrawlInfo['crawl_status']) => {
    return `${status.crawled_count} Visited / ${status.processed_count} Processed / ${status.error_count} Failed`;
  };

  const getSortIcon = (key: string) => {
    if (sortConfig.key !== key) return '↕️';
    return sortConfig.direction === 'asc' ? '↑' : '↓';
  };

  return (
    <>
      {error && (
        <div className="mb-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          {error}
        </div>
      )}
      
      <div className="bg-white rounded-lg shadow overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-gray-200">
            <tr>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-300"
                onClick={() => handleSort('name')}
              >
                Name {getSortIcon('name')}
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-300"
                onClick={() => handleSort('status')}
              >
                Status {getSortIcon('status')}
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-300"
                onClick={() => handleSort('results')}
              >
                Results Summary {getSortIcon('results')}
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-300"
                onClick={() => handleSort('created')}
              >
                Created {getSortIcon('created')}
              </th>
              <th
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-300"
                onClick={() => handleSort('lastUpdate')}
              >
                Last Status Change {getSortIcon('lastUpdate')}
              </th>
              <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                Actions
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedCrawls.map((crawl) => {
              const isSelected = selectedCrawl?.crawl_status.crawl_id === crawl.crawl_status.crawl_id;
              const isLoading = actionLoading === crawl.crawl_status.crawl_id;
              const lastState = crawl.crawl_status.state_history[crawl.crawl_status.state_history.length - 1];
              
              return (
                <tr
                  key={crawl.crawl_status.crawl_id}
                  className={`cursor-pointer hover:bg-gray-50 ${isSelected ? 'bg-blue-100' : ''}`}
                  onClick={() => onSelectCrawl(crawl)}
                >
                  <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                    {crawl.crawl_spec.name}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <span className={`px-2 py-1 rounded text-xs font-medium ${
                      crawl.crawl_status.current_state === 'RUNNING' ? 'bg-green-100 text-green-800' :
                      crawl.crawl_status.current_state === 'STOPPED' ? 'bg-red-100 text-red-800' :
                      'bg-gray-100 text-gray-800'
                    }`}>
                      {crawl.crawl_status.current_state}
                    </span>
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {getResultsSummary(crawl.crawl_status)}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(crawl.crawl_status.state_history[0]?.timestamp || '')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    {formatDate(lastState?.timestamp || '')}
                  </td>
                  <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                    <div className="flex space-x-2">
                      {crawl.crawl_status.current_state !== 'RUNNING' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartCrawl(crawl);
                          }}
                          disabled={isLoading}
                          className="w-8 h-8 bg-green-600 text-white rounded-full flex items-center justify-center hover:bg-green-700 disabled:opacity-50"
                          title="Start crawl"
                        >
                          ▶
                        </button>
                      )}
                      {crawl.crawl_status.current_state === 'RUNNING' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStopCrawl(crawl);
                          }}
                          disabled={isLoading}
                          className="w-8 h-8 bg-red-600 text-white rounded-full flex items-center justify-center hover:bg-red-700 disabled:opacity-50"
                          title="Stop crawl"
                        >
                          ⏸
                        </button>
                      )}
                      <button
                        onClick={(e) => {
                          e.stopPropagation();
                          setDeleteDialog({ isOpen: true, crawl });
                        }}
                        disabled={isLoading}
                        className="w-8 h-8 bg-red-600 text-white rounded-full flex items-center justify-center hover:bg-red-700 disabled:opacity-50"
                        title="Delete crawl"
                      >
                        ⊖
                      </button>
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <ConfirmDialog
        isOpen={deleteDialog.isOpen}
        title="Confirm Delete"
        message={`Are you sure you want to delete the crawl "${deleteDialog.crawl?.crawl_spec.name}"? This action cannot be undone.`}
        onConfirm={handleDeleteCrawl}
        onCancel={() => setDeleteDialog({ isOpen: false, crawl: null })}
      />
    </>
  );
};
