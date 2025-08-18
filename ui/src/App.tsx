import React, { useState } from 'react';
import { CrawlInfo, CrawlSpec, AnalyzerSpec } from './types';
import { useCrawlData } from './hooks/useCrawlData';
import { CrawlTable } from './components/CrawlTable';
import { TabNavigation } from './components/TabNavigation';
import { OverviewTab } from './components/OverviewTab';
import { SourcesTab } from './components/SourcesTab';
import { AnalyzersTab } from './components/AnalyzersTab';
import { ResultsTab } from './components/ResultsTab';

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'sources', label: 'Sources' },
  { id: 'analyzers', label: 'Analyzers' },
  { id: 'results', label: 'Results' },
];

function App() {
  const { crawls, loading, error } = useCrawlData();
  const [selectedCrawl, setSelectedCrawl] = useState<CrawlInfo | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isNewCrawl, setIsNewCrawl] = useState(false);
  const [newCrawlSpec, setNewCrawlSpec] = useState<CrawlSpec>({
    name: '',
    seeds: [],
    analyzer_specs: [],
    worker_count: 1,
    domain_blacklist: [],
  });

  const handleNewCrawl = () => {
    setIsNewCrawl(true);
    setSelectedCrawl(null);
    setActiveTab('overview');
    setNewCrawlSpec({
      name: '',
      seeds: [],
      analyzer_specs: [],
      worker_count: 1,
      domain_blacklist: [],
    });
  };

  const handleSelectCrawl = (crawl: CrawlInfo | null) => {
    setIsNewCrawl(false);
    setSelectedCrawl(crawl);
    setActiveTab('overview');
  };

  const handleCrawlCreated = () => {
    setIsNewCrawl(false);
    setSelectedCrawl(null);
  };

  const currentCrawlSpec = isNewCrawl ? newCrawlSpec : selectedCrawl?.crawl_spec || null;

  if (loading && crawls.length === 0) {
    return (
      <div className="min-h-screen bg-gray-100 flex items-center justify-center">
        <div className="text-lg">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <div className="bg-prospector-blue text-white px-6 py-4">
        <div className="flex justify-between items-center">
          <h1 className="text-2xl font-bold">Prospector</h1>
          <div className="text-right">
            <div className="text-lg font-semibold">Ringer</div>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-6 py-6">
        {/* New Crawl Button */}
        <div className="mb-6">
          <button
            onClick={handleNewCrawl}
            className="px-4 py-2 bg-prospector-blue text-white rounded hover:bg-prospector-dark-blue"
          >
            New Crawl
          </button>
        </div>

        {/* Error Display */}
        {error && (
          <div className="mb-6 p-4 bg-red-100 border border-red-400 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* Crawl Table */}
        <div className="mb-6">
          <CrawlTable
            crawls={crawls}
            selectedCrawl={selectedCrawl}
            onSelectCrawl={handleSelectCrawl}
          />
        </div>

        {/* Tab Content */}
        {(selectedCrawl || isNewCrawl) && (
          <div className="bg-white rounded-lg shadow p-6">
            <TabNavigation
              tabs={tabs}
              activeTab={activeTab}
              onTabChange={setActiveTab}
            />

            <div className="mt-6">
              {activeTab === 'overview' && (
                <OverviewTab
                  crawlSpec={currentCrawlSpec}
                  isNewCrawl={isNewCrawl}
                  selectedCrawl={selectedCrawl}
                  onCrawlSpecChange={setNewCrawlSpec}
                  onCrawlCreated={handleCrawlCreated}
                />
              )}
              {activeTab === 'sources' && (
                <SourcesTab
                  crawlSpec={currentCrawlSpec}
                  isNewCrawl={isNewCrawl}
                  onCrawlSpecChange={setNewCrawlSpec}
                />
              )}
              {activeTab === 'analyzers' && (
                <AnalyzersTab
                  crawlSpec={currentCrawlSpec}
                  isNewCrawl={isNewCrawl}
                  onCrawlSpecChange={setNewCrawlSpec}
                />
              )}
              {activeTab === 'results' && (
                <ResultsTab />
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;
