import React from 'react';

import { CrawlSpec } from '../types';

interface SourcesTabProps {
  crawlSpec: CrawlSpec | null;
  isNewCrawl: boolean;
  onCrawlSpecChange: (spec: CrawlSpec) => void;
  onOpenSearchEngine: () => void;
}

export const SourcesTab: React.FC<SourcesTabProps> = ({
  crawlSpec,
  isNewCrawl,
  onCrawlSpecChange,
  onOpenSearchEngine,
}) => {

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


  const seeds = crawlSpec?.seeds || [];

  return (
    <div>
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ 
            fontSize: '1.125rem', 
            fontWeight: '600', 
            color: 'var(--text-primary)',
            margin: 0
          }}>
            Source URLs
          </h3>
          {isNewCrawl && (
            <button
              onClick={onOpenSearchEngine}
              className="btn-primary"
            >
              Search Engine
            </button>
          )}
        </div>

        <div className="table-container" style={{ border: '1px solid var(--border-primary)' }}>
          {seeds.length === 0 && !isNewCrawl && (
            <div style={{ 
              padding: '2rem', 
              textAlign: 'center',
              color: 'var(--text-secondary)'
            }}>
              No source URLs configured
            </div>
          )}
          
          {seeds.map((url, index) => (
            <div
              key={index}
              style={{
                display: 'flex',
                alignItems: 'center',
                padding: '0.75rem',
                borderBottom: index < seeds.length - 1 ? '1px solid var(--border-secondary)' : 'none'
              }}
            >
              <input
                type="url"
                value={url}
                onChange={(e) => handleUrlChange(index, e.target.value)}
                disabled={!isNewCrawl}
                className="input-field"
                style={{ 
                  flex: 1,
                  marginRight: '0.5rem',
                  border: 'none',
                  background: 'transparent',
                  padding: '0.5rem'
                }}
                placeholder="Enter URL..."
              />
              {isNewCrawl && (
                <button
                  onClick={() => handleRemoveUrl(index)}
                  className="btn-danger btn-circle"
                  style={{ 
                    width: '1.5rem',
                    height: '1.5rem',
                    fontSize: '0.875rem'
                  }}
                  title="Remove URL"
                >
                  ⊖
                </button>
              )}
            </div>
          ))}
          
          {isNewCrawl && (
            <div style={{ 
              padding: '0.75rem',
              borderTop: seeds.length > 0 ? '1px solid var(--border-secondary)' : 'none',
              display: 'flex',
              justifyContent: 'flex-end'
            }}>
              <button
                onClick={handleAddUrl}
                className="btn-circle btn-primary"
                style={{ 
                  width: '1.5rem',
                  height: '1.5rem',
                  fontSize: '0.875rem',
                  fontWeight: 'bold'
                }}
                title="Add URL"
              >
                +
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
