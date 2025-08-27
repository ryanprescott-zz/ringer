import React, { useState, useEffect } from 'react';
import { CrawlInfo, CrawlRecordSummary, CrawlRecord } from '../types';
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
  const { showError } = useToast();

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
    
    setSelectedRecordId(summary.id);
    
    try {
      const response = await crawlApi.getCrawlRecords(selectedCrawl.crawl_status.crawl_id, [summary.id]);
      if (response.records.length > 0) {
        setSelectedRecord(response.records[0]);
      }
    } catch (error) {
      showError('Fetch Error', 'Failed to fetch record details');
    }
  };

  const getFieldOptions = (): string[] => {
    if (!selectedRecord) return [];
    return Object.keys(selectedRecord).filter(key => 
      typeof selectedRecord[key as keyof CrawlRecord] === 'string' ||
      Array.isArray(selectedRecord[key as keyof CrawlRecord])
    );
  };

  const getFieldValue = (): string => {
    if (!selectedRecord || !selectedField) return '';
    const value = selectedRecord[selectedField as keyof CrawlRecord];
    if (Array.isArray(value)) {
      return value.join('\n');
    }
    return String(value || '');
  };

  // Pagination calculations
  const totalPages = Math.ceil(recordSummaries.length / rowsPerPage);
  const startIndex = (currentPage - 1) * rowsPerPage;
  const endIndex = startIndex + rowsPerPage;
  const currentRecords = recordSummaries.slice(startIndex, endIndex);

  const handlePageChange = (page: number) => {
    setCurrentPage(Math.max(1, Math.min(page, totalPages)));
  };

  return (
    <div className="space-y-6">
      {/* Controls Section */}
      <div className="flex gap-4 items-end mb-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Score Type
          </label>
          <select
            value={scoreType}
            onChange={(e) => setScoreType(e.target.value)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="composite">Composite</option>
            <option value="keyword">Keyword</option>
            <option value="dh llm">DH LLM</option>
          </select>
        </div>

        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Count
          </label>
          <input
            type="number"
            value={count}
            onChange={(e) => setCount(parseInt(e.target.value) || 400)}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
          />
        </div>

        <div>
          <button
            onClick={handleGetRecords}
            disabled={loading || !selectedCrawl}
            className="px-4 py-2 bg-ringer-blue text-white rounded hover:bg-ringer-dark-blue disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {loading ? 'Loading...' : 'Get Records'}
          </button>
        </div>

        <div className="ml-auto">
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Field
          </label>
          <select
            value={selectedField}
            onChange={(e) => setSelectedField(e.target.value)}
            disabled={!selectedRecord}
            className="px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-gray-100"
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
      <div className="grid grid-cols-2 gap-6">
        {/* Left Column - Table */}
        <div className="space-y-4">
          {/* Records Table */}
          <div className="bg-white border border-gray-300 overflow-hidden">
            <div className="overflow-auto" style={{ height: '400px' }}>
              <table className="min-w-full">
                <thead className="bg-table-header sticky top-0">
                  <tr>
                    <th className="px-4 py-2 text-left text-sm font-medium text-black cursor-pointer hover:bg-gray-400">
                      ID ↕
                    </th>
                    <th className="px-4 py-2 text-left text-sm font-medium text-black cursor-pointer hover:bg-gray-400">
                      URL ↕
                    </th>
                    <th className="px-4 py-2 text-left text-sm font-medium text-black cursor-pointer hover:bg-gray-400">
                      Composite Score ↕
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {currentRecords.map((record) => (
                    <tr
                      key={record.id}
                      onClick={() => handleSelectRecord(record)}
                      className={`cursor-pointer hover:bg-gray-50 border-b border-gray-300 ${
                        selectedRecordId === record.id ? 'bg-table-selected' : ''
                      }`}
                    >
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-black">
                        {record.id}
                      </td>
                      <td className="px-4 py-2 text-sm text-blue-600 underline">
                        {record.url}
                      </td>
                      <td className="px-4 py-2 whitespace-nowrap text-sm text-black">
                        {record.score.toFixed(3)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          {/* Pagination Controls */}
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-2">
              <span className="text-sm text-gray-700">Show</span>
              <select
                value={rowsPerPage}
                onChange={(e) => {
                  setRowsPerPage(parseInt(e.target.value));
                  setCurrentPage(1);
                }}
                className="px-2 py-1 border border-gray-300 rounded text-sm"
              >
                <option value={10}>10</option>
                <option value={20}>20</option>
                <option value={50}>50</option>
                <option value={100}>100</option>
              </select>
              <span className="text-sm text-gray-700">
                Showing {startIndex + 1} - {Math.min(endIndex, recordSummaries.length)} of {recordSummaries.length}
              </span>
            </div>

            <div className="flex items-center space-x-1">
              <button
                onClick={() => handlePageChange(currentPage - 1)}
                disabled={currentPage === 1}
                className="px-2 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
              >
                &lt;
              </button>
              
              {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                const page = i + 1;
                return (
                  <button
                    key={page}
                    onClick={() => handlePageChange(page)}
                    className={`px-2 py-1 text-sm border border-gray-300 rounded ${
                      currentPage === page ? 'bg-blue-600 text-white' : 'hover:bg-gray-50'
                    }`}
                  >
                    {page}
                  </button>
                );
              })}
              
              <button
                onClick={() => handlePageChange(currentPage + 1)}
                disabled={currentPage === totalPages}
                className="px-2 py-1 text-sm border border-gray-300 rounded disabled:opacity-50"
              >
                &gt;
              </button>
            </div>
          </div>
        </div>

        {/* Right Column - Field Content */}
        <div>
          <textarea
            value={getFieldValue()}
            readOnly
            className="w-full px-3 py-2 border border-gray-300 rounded-md bg-gray-50 text-sm font-mono overflow-auto"
            style={{ height: '400px' }}
            placeholder={selectedRecord ? "Select a field to view its content" : "Select a record to view details"}
          />
        </div>
      </div>
    </div>
  );
};
