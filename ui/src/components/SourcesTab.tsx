import React, { useState } from 'react';
import { CrawlSpec } from '../types';
import { SearchEngineModal } from './SearchEngineModal';

interface SourcesTabProps {
  crawlSpec: CrawlSpec | null;
  isNewCrawl: boolean;
  onCrawlSpecChange: (spec: CrawlSpec) => void;
}

export const SourcesTab: React.FC<SourcesTabProps> = ({
  crawlSpec,
  isNewCrawl,
  onCrawlSpecChange,
}) => {
  const [isSearchModalOpen, setIsSearchModalOpen] = useState(false);

  const handleAddUrl = () => {
    if (crawlSpec) {
      onCrawlSpecChange({
        ...crawlSpec,
        seeds: [...crawlSpec.seeds, ''],
      });
    }
  };

  const handleUrlChange = (index: number, url: string) => {
    if (crawlSpec) {
      const newSeeds = [...crawlSpec.seeds];
      newSeeds[index] = url;
      onCrawlSpecChange({
        ...crawlSpec,
        seeds: newSeeds,
      });
    }
  };

  const handleRemoveUrl = (index: number) => {
    if (crawlSpec) {
      const newSeeds = crawlSpec.seeds.filter((_, i) => i !== index);
      onCrawlSpecChange({
        ...crawlSpec,
        seeds: newSeeds,
      });
    }
  };

  const handleAddSearchUrls = (urls: string[]) => {
    if (crawlSpec) {
      const uniqueUrls = urls.filter(url => !crawlSpec.seeds.includes(url));
      onCrawlSpecChange({
        ...crawlSpec,
        seeds: [...crawlSpec.seeds, ...uniqueUrls],
      });
    }
  };

  const seeds = crawlSpec?.seeds || [];

  return (
    <div className="space-y-6">
      <div>
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-lg font-medium">Source URLs</h3>
          {isNewCrawl && (
            <button
              onClick={setIsSearchModalOpen.bind(null, true)}
              className="px-4 py-2 bg-prospector-blue text-white rounded hover:bg-prospector-dark-blue"
            >
              Search Engine
            </button>
          )}
        </div>

        <div className="border border-gray-300 rounded-md">
          {seeds.length === 0 && !isNewCrawl && (
            <div className="p-4 text-gray-500 text-center">
              No source URLs configured
            </div>
          )}
          
          {seeds.map((url, index) => (
            <div
              key={index}
              className="flex items-center p-3 border-b border-gray-200 last:border-b-0"
            >
              <input
                type="url"
                value={url}
                onChange={(e) => handleUrlChange(index, e.target.value)}
                disabled={!isNewCrawl}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-prospector-blue disabled:bg-gray-100"
                placeholder="Enter URL..."
              />
              {isNewCrawl && (
                <button
                  onClick={() => handleRemoveUrl(index)}
                  className="ml-3 w-8 h-8 bg-red-600 text-white rounded-full flex items-center justify-center hover:bg-red-700"
                  title="Remove URL"
                >
                  ⊖
                </button>
              )}
            </div>
          ))}
          
          {isNewCrawl && (
            <div className="p-3 border-t border-gray-200 flex justify-end">
              <button
                onClick={handleAddUrl}
                className="w-8 h-8 bg-prospector-blue text-white rounded-full flex items-center justify-center hover:bg-prospector-dark-blue"
                title="Add URL"
              >
                +
              </button>
            </div>
          )}
        </div>
      </div>

      <SearchEngineModal
        isOpen={isSearchModalOpen}
        onClose={() => setIsSearchModalOpen(false)}
        onAddUrls={handleAddSearchUrls}
      />
    </div>
  );
};
