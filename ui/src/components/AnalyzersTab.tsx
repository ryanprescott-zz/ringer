import React, { useState } from 'react';
import { CrawlSpec, AnalyzerSpec, WeightedKeyword, WeightedRegex, NewTerm } from '../types';

interface AnalyzersTabProps {
  crawlSpec: CrawlSpec | null;
  isNewCrawl: boolean;
  onCrawlSpecChange: (spec: CrawlSpec) => void;
}

export const AnalyzersTab: React.FC<AnalyzersTabProps> = ({
  crawlSpec,
  isNewCrawl,
  onCrawlSpecChange,
}) => {
  const [selectedAnalyzer, setSelectedAnalyzer] = useState<string>('Term Matching');
  const [newTerm, setNewTerm] = useState<NewTerm>({
    type: 'Keyword',
    term: '',
    matchCase: false,
    weight: 1.0,
  });

  const getOrCreateAnalyzer = (name: string): AnalyzerSpec => {
    const existing = crawlSpec?.analyzer_specs.find(spec => spec.name === name);
    if (existing) return existing;

    if (name === 'KeywordScoreAnalyzer') {
      return {
        name: 'KeywordScoreAnalyzer',
        composite_weight: 1.0,
        keywords: [],
        regexes: [],
      };
    } else if (name === 'DhLlmScoreAnalyzer') {
      return {
        name: 'DhLlmScoreAnalyzer',
        composite_weight: 1.0,
        prompt_input: { prompt: '' },
        text_inputs: [],
        field_map: { Score: 'string' },
      };
    }

    return {
      name,
      composite_weight: 1.0,
    };
  };

  const updateAnalyzer = (updatedAnalyzer: AnalyzerSpec) => {
    if (!crawlSpec) return;

    const existingIndex = crawlSpec.analyzer_specs.findIndex(
      spec => spec.name === updatedAnalyzer.name
    );

    let newAnalyzerSpecs;
    if (existingIndex >= 0) {
      newAnalyzerSpecs = [...crawlSpec.analyzer_specs];
      newAnalyzerSpecs[existingIndex] = updatedAnalyzer;
    } else {
      newAnalyzerSpecs = [...crawlSpec.analyzer_specs, updatedAnalyzer];
    }

    onCrawlSpecChange({
      ...crawlSpec,
      analyzer_specs: newAnalyzerSpecs,
    });
  };

  const handleAddTerm = () => {
    if (!newTerm.term.trim()) return;

    const analyzer = getOrCreateAnalyzer('KeywordScoreAnalyzer');
    
    if (newTerm.type === 'Keyword') {
      const newKeyword: WeightedKeyword = {
        keyword: newTerm.term,
        weight: newTerm.weight,
      };
      updateAnalyzer({
        ...analyzer,
        keywords: [...(analyzer.keywords || []), newKeyword],
      });
    } else {
      const newRegex: WeightedRegex = {
        regex: newTerm.term,
        weight: newTerm.weight,
        flags: newTerm.matchCase ? 0 : 2, // 2 = case insensitive
      };
      updateAnalyzer({
        ...analyzer,
        regexes: [...(analyzer.regexes || []), newRegex],
      });
    }

    setNewTerm({
      type: 'Keyword',
      term: '',
      matchCase: false,
      weight: 1.0,
    });
  };

  const handleRemoveTerm = (type: 'keyword' | 'regex', index: number) => {
    const analyzer = getOrCreateAnalyzer('KeywordScoreAnalyzer');
    
    if (type === 'keyword') {
      const newKeywords = (analyzer.keywords || []).filter((_, i) => i !== index);
      updateAnalyzer({ ...analyzer, keywords: newKeywords });
    } else {
      const newRegexes = (analyzer.regexes || []).filter((_, i) => i !== index);
      updateAnalyzer({ ...analyzer, regexes: newRegexes });
    }
  };

  const handlePromptChange = (prompt: string) => {
    const analyzer = getOrCreateAnalyzer('DhLlmScoreAnalyzer');
    updateAnalyzer({
      ...analyzer,
      prompt_input: { prompt },
    });
  };

  const handleCompositeWeightChange = (analyzerName: string, weight: number) => {
    const analyzer = getOrCreateAnalyzer(analyzerName);
    updateAnalyzer({ ...analyzer, composite_weight: weight });
  };


  const currentAnalyzer = getOrCreateAnalyzer(
    selectedAnalyzer === 'Term Matching' ? 'KeywordScoreAnalyzer' : 'DhLlmScoreAnalyzer'
  );

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 3fr', gap: '2rem' }}>
      {/* Analyzer Selection */}
      <div>
        <h3 style={{ 
          fontSize: '1.125rem', 
          fontWeight: '600', 
          color: 'var(--text-primary)',
          marginBottom: '1rem',
          margin: 0
        }}>
          Analyzer
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {['Term Matching', 'DH LLM Prompt'].map((analyzer) => (
            <button
              key={analyzer}
              onClick={() => setSelectedAnalyzer(analyzer)}
              className={selectedAnalyzer === analyzer ? 'btn-primary' : 'btn-secondary'}
              style={{
                width: '100%',
                textAlign: 'left',
                padding: '0.75rem 1rem',
                borderRadius: '0.375rem'
              }}
            >
              {analyzer}
            </button>
          ))}
        </div>
      </div>

      {/* Analyzer Configuration */}
      <div>
        {selectedAnalyzer === 'Term Matching' && (
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <h4 style={{ 
                fontSize: '1.125rem', 
                fontWeight: '600', 
                color: 'var(--text-primary)',
                margin: 0
              }}>
                Terms
              </h4>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <label style={{ 
                  fontSize: '1.125rem', 
                  fontWeight: '600', 
                  color: 'var(--text-primary)'
                }}>
                  Composite Weight
                </label>
                <input
                  type="number"
                  value={currentAnalyzer.composite_weight}
                  onChange={(e) => handleCompositeWeightChange(
                    currentAnalyzer.name,
                    parseFloat(e.target.value) || 0
                  )}
                  disabled={!isNewCrawl}
                  step="0.1"
                  className="input-field"
                  style={{ width: '8rem' }}
                />
              </div>
            </div>
            
            {/* Terms Table */}
            <div className="table-container" style={{ marginBottom: '1rem' }}>
              <table className="table">
                <thead className="table-header">
                  <tr>
                    <th className="table-header" style={{ borderRight: '1px solid var(--border-primary)' }}>Type</th>
                    <th className="table-header" style={{ borderRight: '1px solid var(--border-primary)' }}>Term</th>
                    <th className="table-header" style={{ borderRight: '1px solid var(--border-primary)' }}>Match Case</th>
                    <th className="table-header" style={{ borderRight: '1px solid var(--border-primary)' }}>Weight</th>
                    {isNewCrawl && (
                      <th className="table-header">Actions</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {(currentAnalyzer.keywords || []).map((keyword, index) => (
                    <tr key={`keyword-${index}`}>
                      <td style={{ borderRight: '1px solid var(--border-secondary)', padding: '0.75rem 1rem', fontSize: '0.875rem' }}>Keyword</td>
                      <td style={{ borderRight: '1px solid var(--border-secondary)', padding: '0.75rem 1rem', fontSize: '0.875rem' }}>{keyword.keyword}</td>
                      <td style={{ borderRight: '1px solid var(--border-secondary)', padding: '0.75rem 1rem', fontSize: '0.875rem', textAlign: 'center' }}>
                        <input type="checkbox" disabled style={{ borderRadius: '0.25rem' }} />
                      </td>
                      <td style={{ borderRight: '1px solid var(--border-secondary)', padding: '0.75rem 1rem', fontSize: '0.875rem' }}>{keyword.weight}</td>
                      {isNewCrawl && (
                        <td style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>
                          <button
                            onClick={() => handleRemoveTerm('keyword', index)}
                            className="btn-circle btn-danger"
                            style={{ width: '1.5rem', height: '1.5rem', fontSize: '0.75rem' }}
                          >
                            ⊖
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                  {(currentAnalyzer.regexes || []).map((regex, index) => (
                    <tr key={`regex-${index}`}>
                      <td style={{ borderRight: '1px solid var(--border-secondary)', padding: '0.75rem 1rem', fontSize: '0.875rem' }}>Regex</td>
                      <td style={{ borderRight: '1px solid var(--border-secondary)', padding: '0.75rem 1rem', fontSize: '0.875rem' }}>{regex.regex}</td>
                      <td style={{ borderRight: '1px solid var(--border-secondary)', padding: '0.75rem 1rem', fontSize: '0.875rem', textAlign: 'center' }}>
                        <input
                          type="checkbox"
                          checked={regex.flags !== 2}
                          disabled
                          style={{ borderRadius: '0.25rem' }}
                        />
                      </td>
                      <td style={{ borderRight: '1px solid var(--border-secondary)', padding: '0.75rem 1rem', fontSize: '0.875rem' }}>{regex.weight}</td>
                      {isNewCrawl && (
                        <td style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>
                          <button
                            onClick={() => handleRemoveTerm('regex', index)}
                            className="btn-circle btn-danger"
                            style={{ width: '1.5rem', height: '1.5rem', fontSize: '0.75rem' }}
                          >
                            ⊖
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>

            {/* Add Term Controls */}
            {isNewCrawl && (
              <div className="table-container" style={{ background: 'var(--bg-secondary)' }}>
                <table className="table">
                  <tbody>
                    <tr>
                      <td style={{ borderRight: '1px solid var(--border-primary)', padding: '0.75rem 1rem' }}>
                        <select
                          value={newTerm.type}
                          onChange={(e) => setNewTerm({ ...newTerm, type: e.target.value as 'Keyword' | 'Regex' })}
                          className="input-field"
                          style={{ width: '100%', padding: '0.5rem' }}
                        >
                          <option value="Keyword">Keyword</option>
                          <option value="Regex">Regex</option>
                        </select>
                      </td>
                      <td style={{ borderRight: '1px solid var(--border-primary)', padding: '0.75rem 1rem' }}>
                        <input
                          type="text"
                          value={newTerm.term}
                          onChange={(e) => setNewTerm({ ...newTerm, term: e.target.value })}
                          placeholder="Enter term..."
                          className="input-field"
                          style={{ width: '100%', padding: '0.5rem' }}
                        />
                      </td>
                      <td style={{ borderRight: '1px solid var(--border-primary)', padding: '0.75rem 1rem', textAlign: 'center' }}>
                        <input
                          type="checkbox"
                          checked={newTerm.matchCase}
                          onChange={(e) => setNewTerm({ ...newTerm, matchCase: e.target.checked })}
                          style={{ borderRadius: '0.25rem' }}
                        />
                      </td>
                      <td style={{ borderRight: '1px solid var(--border-primary)', padding: '0.75rem 1rem' }}>
                        <input
                          type="number"
                          value={newTerm.weight}
                          onChange={(e) => setNewTerm({ ...newTerm, weight: parseFloat(e.target.value) || 0 })}
                          step="0.1"
                          className="input-field"
                          style={{ width: '100%', padding: '0.5rem' }}
                        />
                      </td>
                      <td style={{ padding: '0.75rem 1rem', textAlign: 'center' }}>
                        <button
                          onClick={handleAddTerm}
                          disabled={!newTerm.term.trim()}
                          className="btn-primary"
                        >
                          Add
                        </button>
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>
            )}
          </div>
        )}

        {selectedAnalyzer === 'DH LLM Prompt' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
            {/* Composite Weight */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <h4 style={{ 
                fontSize: '1.125rem', 
                fontWeight: '600', 
                color: 'var(--text-primary)',
                margin: 0
              }}>
                Prompt
              </h4>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                <label style={{ 
                  fontSize: '1.125rem', 
                  fontWeight: '600', 
                  color: 'var(--text-primary)'
                }}>
                  Composite Weight
                </label>
                <input
                  type="number"
                  value={currentAnalyzer.composite_weight}
                  onChange={(e) => handleCompositeWeightChange(
                    currentAnalyzer.name,
                    parseFloat(e.target.value) || 0
                  )}
                  disabled={!isNewCrawl}
                  step="0.1"
                  className="input-field"
                  style={{ width: '8rem' }}
                />
              </div>
            </div>
            
            {/* Prompt */}
            <div>
              <textarea
                value={currentAnalyzer.prompt_input?.prompt || ''}
                onChange={(e) => handlePromptChange(e.target.value)}
                disabled={!isNewCrawl}
                rows={6}
                className="input-field"
                style={{ 
                  width: '100%',
                  padding: '0.75rem 1rem',
                  borderRadius: '0.5rem',
                  resize: 'vertical'
                }}
                placeholder="Enter LLM prompt..."
              />
            </div>

          </div>
        )}
      </div>
    </div>
  );
};
