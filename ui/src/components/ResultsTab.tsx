import React, { useState, useEffect } from 'react';
import { CrawlInfo, CrawlRecordSummary, CrawlRecord, SortConfig } from '../types';
import { crawlApi } from '../services/api';
import { useToast } from '../hooks/useToast';

interface ResultsTabProps {
  selectedCrawl?: CrawlInfo | null;
}

export const ResultsTab: React.FC<ResultsTabProps> = ({ selectedCrawl }) => {
  const [scoreType, setScoreType] = useState<string>('composite');
  const [count, setCount] = useState<number>(400);
  const [recordSummaries, setRecordSummaries] = useState<CrawlRecordSummary[]>([]);
  const [selectedRecord, setSelectedRecord] = useState<CrawlRecord | null>(null);
  const [selectedRecordId, setSelectedRecordId] = useState<string>('');
  const [selectedField, setSelectedField] = useState<string>('extracted_content');
  const [loading, setLoading] = useState<boolean>(false);
  const [currentPage, setCurrentPage] = useState<number>(1);
  const [rowsPerPage, setRowsPerPage] = useState<number>(10);
  const [sortConfig, setSortConfig] = useState<SortConfig>({ key: 'score', direction: 'desc' });
  const { showError } = useToast();

  // Update text area when selected field changes
  useEffect(() => {
    // Force re-render when selectedField changes
    // This ensures getFieldValue() is called with the new field
  }, [selectedField, selectedRecord]);

  const handleGetRecords = async () => {
    if (!selectedCrawl) return;
    
    setLoading(true);
    try {
      const response = await crawlApi.getCrawlRecordSummaries(selectedCrawl.crawl_status.crawl_id, count, scoreType);
      setRecordSummaries(response.records);
      setCurrentPage(1);
      setSelectedRecord(null);
      setSelectedRecordId('');
    } catch (error) {
      showError('Fetch Error', 'Failed to fetch record summaries');
    } finally {
      setLoading(false);
    }
  };

  const handleSelectRecord = async (summary: CrawlRecordSummary) => {
    if (!selectedCrawl) return;
    
    // Set selected record ID immediately for visual feedback
    setSelectedRecordId(summary.id);
    
    try {
      const response = await crawlApi.getCrawlRecords(selectedCrawl.crawl_status.crawl_id, [summary.id]);
      if (response.records.length > 0) {
        const record = response.records[0];
        setSelectedRecord(record);
        // Set default field if not already set or if field doesn't exist in record
        if (!selectedField || !(selectedField in record)) {
          setSelectedField('extracted_content');
        }
      }
    } catch (error) {
      showError('Fetch Error', 'Failed to fetch record details');
      // Reset selection on error
      setSelectedRecordId('');
    }
  };

  const handleSort = (key: string) => {
    setSortConfig(prev => ({
      key,
      direction: prev.key === key && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  const sortRecords = (records: CrawlRecordSummary[]): CrawlRecordSummary[] => {
    return [...records].sort((a, b) => {
      let aValue: any = a[sortConfig.key as keyof CrawlRecordSummary];
      let bValue: any = b[sortConfig.key as keyof CrawlRecordSummary];

      // Handle different data types
      if (typeof aValue === 'string' && typeof bValue === 'string') {
        aValue = aValue.toLowerCase();
        bValue = bValue.toLowerCase();
      }

      if (aValue < bValue) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (aValue > bValue) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  };

  const getFieldOptions = (): string[] => {
    if (!selectedRecord) return ['extracted_content'];
    return Object.keys(selectedRecord);
  };

  const getFieldValue = (): string => {
    if (!selectedRecord || !selectedField) return '';
    const value = selectedRecord[selectedField as keyof CrawlRecord];
    if (Array.isArray(value)) {
      return value.join('\n');
    }
    if (typeof value === 'object' && value !== null) {
      return JSON.stringify(value, null, 2);
    }
    return String(value || '');
  };

  // Sort and paginate records
  const sortedRecords = sortRecords(recordSummaries);
  const totalPages = Math.ceil(sortedRecords.length / rowsPerPage);
  const startIndex = (currentPage - 1) * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const currentRecords = sortedRecords.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
      {/* Controls Section */}
      <div style={{ display: 'flex', gap: '1rem', alignItems: 'flex-end', marginBottom: '1rem' }}>
        <div>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '0.25rem'
          }}>
            Score Type
          </label>
          <select
            value={scoreType}
            onChange={(e) => setScoreType(e.target.value)}
            className="input-field"
            style={{ padding: '0.75rem 1rem' }}
          >
            <option value="composite">Composite</option>
            <option value="keyword">Keyword</option>
            <option value="dh llm">DH LLM</option>
          </select>
        </div>

        <div>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '0.25rem'
          }}>
            Count
          </label>
          <input
            type="number"
            value={count}
            onChange={(e) => setCount(parseInt(e.target.value) || 400)}
            className="input-field"
            style={{ padding: '0.75rem 1rem' }}
          />
        </div>

        <div>
          <button
            onClick={handleGetRecords}
            disabled={loading || !selectedCrawl}
            className="btn-primary"
          >
            {loading ? 'Loading...' : 'Get Records'}
          </button>
        </div>

        <div style={{ marginLeft: 'auto' }}>
          <label style={{
            display: 'block',
            fontSize: '0.875rem',
            fontWeight: '600',
            color: 'var(--text-primary)',
            marginBottom: '0.25rem'
          }}>
            Field
          </label>
          <select
            value={selectedField}
            onChange={(e) => setSelectedField(e.target.value)}
            disabled={!selectedRecord}
            className="input-field"
            style={{ padding: '0.75rem 1rem' }}
          >
            {getFieldOptions().map((field) => (
              <option key={field} value={field}>
                {field}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Results Section */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* Left Column - Table */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {/* Records Table */}
          <div className="table-container" style={{ overflow: 'hidden' }}>
            <div style={{ height: '400px', overflow: 'auto' }}>
              <table className="table" style={{ 
                width: '100%',
                tableLayout: 'fixed',
                minWidth: '600px'
              }}>
                <thead className="table-header" style={{ position: 'sticky', top: 0 }}>
                  <tr>
                    <th 
                      onClick={() => handleSort('id')}
                      style={{ 
                        cursor: 'pointer', 
                        padding: '0.75rem 1rem',
                        width: '100px'
                      }}
                    >
                      ID
                    </th>
                    <th 
                      onClick={() => handleSort('url')}
                      style={{ 
                        cursor: 'pointer', 
                        padding: '0.75rem 1rem',
                        width: '350px'
                      }}
                    >
                      URL
                    </th>
                    <th 
                      onClick={() => handleSort('score')}
                      style={{ 
                        cursor: 'pointer', 
                        padding: '0.75rem 1rem',
                        width: '150px'
                      }}
                    >
                      Composite Score
                    </th>
                  </tr>
                </thead>
                <tbody style={{ background: 'var(--bg-tertiary)' }}>
                  {currentRecords.length > 0 ? (
                    currentRecords.map((record) => (
                      <tr
                        key={record.id}
                        onClick={() => handleSelectRecord(record)}
                        className={`table-row ${
                          selectedRecordId === record.id ? 'selected' : ''
                        }`}
                      >
                        <td style={{ 
                          padding: '0.75rem 1rem', 
                          fontSize: '0.875rem',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }}>
                          {record.id}
                        </td>
                        <td style={{ 
                          padding: '0.75rem 1rem', 
                          fontSize: '0.875rem', 
                          color: '#3b82f6', 
                          textDecoration: 'underline',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap'
                        }} title={record.url}>
                          {record.url}
                        </td>
                        <td style={{ 
                          padding: '0.75rem 1rem', 
                          fontSize: '0.875rem',
                          overflow: 'hidden',
                          textOverflow: 'ellipsis',
                          whiteSpace: 'nowrap',
                          textAlign: 'right'
                        }}>
                          {record.score.toFixed(3)}
                        </td>
                      </tr>
                    ))
                  ) : (
                    <tr>
                      <td colSpan={3} style={{ 
                        padding: '3rem 1rem',
                        textAlign: 'center',
                        color: 'var(--text-secondary)',
                        fontSize: '0.875rem',
                        fontStyle: 'italic'
                      }}>
                        {recordSummaries.length === 0 ? 'Click "Get Records" to load results' : 'No records found'}
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination Controls */}
          {recordSummaries.length > 0 && (
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>Show</span>
                <select
                  value={rowsPerPage}
                  onChange={(e) => {
                    setRowsPerPage(parseInt(e.target.value));
                    setCurrentPage(1);
                  }}
                  className="input-field"
                  style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem' }}
                >
                  <option value={10}>10</option>
                  <option value={20}>20</option>
                  <option value={50}>50</option>
                  <option value={100}>100</option>
                </select>
                <span style={{ fontSize: '0.875rem', color: 'var(--text-primary)' }}>
                  Showing {startIndex + 1} - {Math.min(endIndex, sortedRecords.length)} of {sortedRecords.length}
                </span>
              </div>

              <div style={{ display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                <button
                  onClick={() => handlePageChange(currentPage - 1)}
                  disabled={currentPage === 1}
                  className="btn-secondary btn-sm"
                  style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem' }}
                >
                  &lt;
                </button>
                
                {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                  const page = i + 1;
                  return (
                    <button
                      key={page}
                      onClick={() => handlePageChange(page)}
                      className={currentPage === page ? 'btn-primary btn-sm' : 'btn-secondary btn-sm'}
                      style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem' }}
                    >
                      {page}
                    </button>
                  );
                })}
                
                <button
                  onClick={() => handlePageChange(currentPage + 1)}
                  disabled={currentPage === totalPages || totalPages === 0}
                  className="btn-secondary btn-sm"
                  style={{ padding: '0.25rem 0.5rem', fontSize: '0.875rem' }}
                >
                  &gt;
                </button>
              </div>
            </div>
          )}
        </div>

        {/* Right Column - Field Content */}
        <div>
          <textarea
            value={getFieldValue()}
            readOnly
            className="input-field"
            style={{ 
              width: '100%', 
              height: '400px',
              padding: '0.75rem 1rem',
              fontFamily: 'monospace',
              fontSize: '0.875rem',
              background: 'var(--bg-secondary)',
              resize: 'none'
            }}
            placeholder={selectedRecord ? "Select a field to view its content" : "Select a record to view details"}
          />
        </div>
      </div>
    </div>
  );
};
