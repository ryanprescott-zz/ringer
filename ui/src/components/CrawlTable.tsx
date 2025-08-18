import React, { useState } from 'react';
import { CrawlInfo, SortConfig } from '../types';
import { sortCrawls } from '../utils/sorting';
import { ConfirmDialog } from './ConfirmDialog';
import { crawlApi } from '../services/api';
import { useToast } from '../hooks/useToast';

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
  const { showSuccess, showError } = useToast();

  const sortedCrawls = sortCrawls(crawls, sortConfig);

  const handleSort = (key: string) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const handleStartCrawl = async (crawl: CrawlInfo) => {
    setActionLoading(crawl.crawl_status.crawl_id);
    try {
      await crawlApi.startCrawl({ crawl_id: crawl.crawl_status.crawl_id });
      showSuccess('Crawl Started', `Successfully started crawl "${crawl.crawl_spec.name}"`);
    } catch (err) {
      showError('Start Failed', `Failed to start crawl "${crawl.crawl_spec.name}"`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleStopCrawl = async (crawl: CrawlInfo) => {
    setActionLoading(crawl.crawl_status.crawl_id);
    try {
      await crawlApi.stopCrawl({ crawl_id: crawl.crawl_status.crawl_id });
      showSuccess('Crawl Stopped', `Successfully stopped crawl "${crawl.crawl_spec.name}"`);
    } catch (err) {
      showError('Stop Failed', `Failed to stop crawl "${crawl.crawl_spec.name}"`);
    } finally {
      setActionLoading(null);
    }
  };

  const handleDeleteCrawl = async () => {
    if (!deleteDialog.crawl) return;
    
    setActionLoading(deleteDialog.crawl.crawl_status.crawl_id);
    try {
      await crawlApi.deleteCrawl({ crawl_id: deleteDialog.crawl.crawl_status.crawl_id });
      showSuccess('Crawl Deleted', `Successfully deleted crawl "${deleteDialog.crawl.crawl_spec.name}"`);
      setDeleteDialog({ isOpen: false, crawl: null });
      if (selectedCrawl?.crawl_status.crawl_id === deleteDialog.crawl.crawl_status.crawl_id) {
        onSelectCrawl(null);
      }
    } catch (err) {
      showError('Delete Failed', `Failed to delete crawl "${deleteDialog.crawl.crawl_spec.name}"`);
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
      <div className="bg-white border border-gray-300 overflow-hidden">
        <table className="min-w-full">
          <thead className="bg-table-header">
            <tr>
              <th
                className="px-4 py-2 text-left text-sm font-medium text-black cursor-pointer hover:bg-gray-400"
                onClick={() => handleSort('name')}
              >
                Name {getSortIcon('name')}
              </th>
              <th
                className="px-4 py-2 text-left text-sm font-medium text-black cursor-pointer hover:bg-gray-400"
                onClick={() => handleSort('status')}
              >
                Status {getSortIcon('status')}
              </th>
              <th
                className="px-4 py-2 text-left text-sm font-medium text-black cursor-pointer hover:bg-gray-400"
                onClick={() => handleSort('results')}
              >
                Results Summary {getSortIcon('results')}
              </th>
              <th
                className="px-4 py-2 text-left text-sm font-medium text-black cursor-pointer hover:bg-gray-400"
                onClick={() => handleSort('created')}
              >
                Created {getSortIcon('created')}
              </th>
              <th
                className="px-4 py-2 text-left text-sm font-medium text-black cursor-pointer hover:bg-gray-400"
                onClick={() => handleSort('lastUpdate')}
              >
                Last Status Change {getSortIcon('lastUpdate')}
              </th>
              <th className="px-4 py-2 text-left text-sm font-medium text-black">
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
                  className={`cursor-pointer hover:bg-gray-50 border-b border-gray-300 ${isSelected ? 'bg-table-selected' : ''}`}
                  onClick={() => onSelectCrawl(crawl)}
                >
                  <td className="px-4 py-2 whitespace-nowrap text-sm font-medium text-black">
                    {crawl.crawl_spec.name}
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-black">
                    <span className={`font-medium ${
                      crawl.crawl_status.current_state === 'RUNNING' ? 'text-green-600' :
                      crawl.crawl_status.current_state === 'STOPPED' ? 'text-red-600' :
                      'text-black'
                    }`}>
                      {crawl.crawl_status.current_state}
                    </span>
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-black">
                    {getResultsSummary(crawl.crawl_status)}
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-black">
                    {formatDate(crawl.crawl_status.state_history[0]?.timestamp || '')}
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-black">
                    {formatDate(lastState?.timestamp || '')}
                  </td>
                  <td className="px-4 py-2 whitespace-nowrap text-sm text-black">
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
