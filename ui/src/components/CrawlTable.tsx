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
    const isActive = sortConfig.key === key;
    const isAsc = sortConfig.direction === 'asc';
    
    return (
      <span className={`sort-arrows ${isActive ? 'active' : ''}`}>
        <span className={`sort-arrow ${isActive && isAsc ? 'active' : ''}`}>▲</span>
        <span className={`sort-arrow ${isActive && !isAsc ? 'active' : ''}`}>▼</span>
      </span>
    );
  };

  return (
    <>
      <div className="table-container">
        <table className="table">
          <thead className="table-header">
            <tr>
              <th
                onClick={() => handleSort('name')}
              >
                Name {getSortIcon('name')}
              </th>
              <th
                onClick={() => handleSort('status')}
              >
                Status {getSortIcon('status')}
              </th>
              <th
                onClick={() => handleSort('results')}
              >
                Results Summary {getSortIcon('results')}
              </th>
              <th
                onClick={() => handleSort('created')}
              >
                Created {getSortIcon('created')}
              </th>
              <th
                onClick={() => handleSort('lastUpdate')}
              >
                Last Status Change {getSortIcon('lastUpdate')}
              </th>
              <th>
                Actions
              </th>
            </tr>
          </thead>
          <tbody>
            {sortedCrawls.map((crawl) => {
              const isSelected = selectedCrawl?.crawl_status.crawl_id === crawl.crawl_status.crawl_id;
              const isLoading = actionLoading === crawl.crawl_status.crawl_id;
              const lastState = crawl.crawl_status.state_history[crawl.crawl_status.state_history.length - 1];
              
              return (
                <tr
                  key={crawl.crawl_status.crawl_id}
                  className={`table-row ${isSelected ? 'selected' : ''}`}
                  onClick={() => onSelectCrawl(crawl)}
                >
                  <td style={{ fontWeight: 600 }}>
                    {crawl.crawl_spec.name}
                  </td>
                  <td>
                    <span style={{
                      fontWeight: 500,
                      color: crawl.crawl_status.current_state === 'RUNNING' ? '#059669' :
                             crawl.crawl_status.current_state === 'STOPPED' ? '#dc2626' :
                             'inherit'
                    }}>
                      {crawl.crawl_status.current_state}
                    </span>
                  </td>
                  <td>
                    {getResultsSummary(crawl.crawl_status)}
                  </td>
                  <td>
                    {formatDate(crawl.crawl_status.state_history[0]?.timestamp || '')}
                  </td>
                  <td>
                    {formatDate(lastState?.timestamp || '')}
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.5rem' }}>
                      {crawl.crawl_status.current_state !== 'RUNNING' && (
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartCrawl(crawl);
                          }}
                          disabled={isLoading}
                          className="btn-success btn-circle btn-sm"
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
                          className="btn-danger btn-circle btn-sm"
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
                        className="btn-danger btn-circle btn-sm"
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
