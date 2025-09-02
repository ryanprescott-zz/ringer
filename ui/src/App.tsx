import React, { useState } from 'react';
import { CrawlInfo, CrawlSpec } from './types';
import { useCrawlData } from './hooks/useCrawlData';
import { useToast } from './hooks/useToast';
import { ThemeProvider } from './contexts/ThemeContext';
import { CrawlTable } from './components/CrawlTable';
import { TabNavigation } from './components/TabNavigation';
import { OverviewTab } from './components/OverviewTab';
import { SourcesTab } from './components/SourcesTab';
import { AnalyzersTab } from './components/AnalyzersTab';
import { ResultsTab } from './components/ResultsTab';
import { ToastContainer } from './components/ToastContainer';
import { DropdownButton } from './components/DropdownButton';
import { CloneExistingModal } from './components/CloneExistingModal';
import { SearchEngineModal } from './components/SearchEngineModal';
import SettingsMenu from './components/SettingsMenu';
import './App.css';

const tabs = [
  { id: 'overview', label: 'Overview' },
  { id: 'sources', label: 'Sources' },
  { id: 'analyzers', label: 'Analyzers' },
  { id: 'results', label: 'Results' },
];

function AppContent() {
  const { crawls, loading, error } = useCrawlData();
  const { toasts, removeToast, showError, showSuccess } = useToast();
  const [selectedCrawl, setSelectedCrawl] = useState<CrawlInfo | null>(null);
  const [activeTab, setActiveTab] = useState('overview');
  const [isNewCrawl, setIsNewCrawl] = useState(false);
  const [isCloneModalOpen, setIsCloneModalOpen] = useState(false);
  const [isSearchEngineModalOpen, setIsSearchEngineModalOpen] = useState(false);
  const [newCrawlSpec, setNewCrawlSpec] = useState<CrawlSpec>({
    name: '',
    seeds: [],
    analyzer_specs: [],
    worker_count: 1,
    domain_blacklist: [],
  });

  // Show error toast when there's a data loading error
  React.useEffect(() => {
    if (error) {
      showError('Connection Error', error);
    }
  }, [error, showError]);

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

  const handleCloneExisting = (crawlToClone: CrawlInfo) => {
    const clonedSpec: CrawlSpec = {
      ...crawlToClone.crawl_spec,
      name: `${crawlToClone.crawl_spec.name} (Copy)`,
    };
    
    setNewCrawlSpec(clonedSpec);
    setIsNewCrawl(true);
    setSelectedCrawl(null);
    setActiveTab('overview');
    setIsCloneModalOpen(false);
    
    showSuccess('Crawl Cloned', `Cloned "${crawlToClone.crawl_spec.name}" successfully`);
  };

  const handleAddSearchUrls = (urls: string[]) => {
    if (newCrawlSpec) {
      const uniqueUrls = urls.filter(url => !newCrawlSpec.seeds.includes(url));
      setNewCrawlSpec({
        ...newCrawlSpec,
        seeds: [...newCrawlSpec.seeds, ...uniqueUrls],
      });
    }
    setIsSearchEngineModalOpen(false);
  };

  const currentCrawlSpec = isNewCrawl ? newCrawlSpec : selectedCrawl?.crawl_spec || null;

  if (loading && crawls.length === 0) {
    return (
      <div className="app">
        <div className="tab-placeholder">Loading...</div>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Header */}
      <div className="app-header">
        <div className="header-content">
          <h1 className="header-title">RINGER</h1>
          <p className="header-subtitle">Web Crawling Platform</p>
        </div>
        <div className="header-actions">
          <SettingsMenu />
        </div>
      </div>

      <div className="app-content">
        <div className="content-container">
          {/* New Crawl Button */}
          <div style={{ marginBottom: '1.5rem' }}>
            <DropdownButton
              onMainClick={handleNewCrawl}
              items={[
                {
                  id: 'clone-existing',
                  label: 'Clone Existing',
                  disabled: crawls.length === 0,
                  onClick: () => setIsCloneModalOpen(true),
                },
              ]}
            >
              New Crawl
            </DropdownButton>
          </div>

          {/* Crawl Table */}
          <div style={{ marginBottom: '1.5rem' }}>
            <CrawlTable
              crawls={crawls}
              selectedCrawl={selectedCrawl}
              onSelectCrawl={handleSelectCrawl}
            />
          </div>

          {/* Tab Content */}
          {(selectedCrawl || isNewCrawl) && (
            <div className="content-container">
              <TabNavigation
                tabs={tabs}
                activeTab={activeTab}
                onTabChange={setActiveTab}
              />

              <div className="tab-content">
                <div style={{ padding: '2rem' }}>
                  {activeTab === 'overview' && (
                    <OverviewTab
                      crawlSpec={currentCrawlSpec}
                      isNewCrawl={isNewCrawl}
                      selectedCrawl={selectedCrawl}
                      existingCrawls={crawls}
                      onCrawlSpecChange={setNewCrawlSpec}
                      onCrawlCreated={handleCrawlCreated}
                    />
                  )}
                  {activeTab === 'sources' && (
                    <SourcesTab
                      crawlSpec={currentCrawlSpec}
                      isNewCrawl={isNewCrawl}
                      onCrawlSpecChange={setNewCrawlSpec}
                      onOpenSearchEngine={() => setIsSearchEngineModalOpen(true)}
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
                    <ResultsTab selectedCrawl={selectedCrawl} />
                  )}
                </div>
              </div>
            </div>
          )}
          
          <ToastContainer toasts={toasts} onRemoveToast={removeToast} />
          
          <CloneExistingModal
            isOpen={isCloneModalOpen}
            crawls={crawls}
            onClose={() => setIsCloneModalOpen(false)}
            onClone={handleCloneExisting}
          />
          
          <SearchEngineModal
            isOpen={isSearchEngineModalOpen}
            onClose={() => setIsSearchEngineModalOpen(false)}
            onAddUrls={handleAddSearchUrls}
          />
        </div>
      </div>
    </div>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AppContent />
    </ThemeProvider>
  );
}

export default App;
