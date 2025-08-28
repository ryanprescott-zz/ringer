import React, { useState } from 'react';
import { CrawlSpec, AnalyzerSpec, WeightedKeyword, WeightedRegex, NewTerm, OutputField } from '../types';

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
  const [newOutputField, setNewOutputField] = useState<OutputField>({
    name: '',
    type: 'string',
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

  const handleAddOutputField = () => {
    if (!newOutputField.name.trim()) return;

    const analyzer = getOrCreateAnalyzer('DhLlmScoreAnalyzer');
    const newFieldMap = { ...(analyzer.field_map || {}) };
    newFieldMap[newOutputField.name] = newOutputField.type;

    updateAnalyzer({
      ...analyzer,
      field_map: newFieldMap,
    });

    setNewOutputField({ name: '', type: 'string' });
  };

  const handleRemoveOutputField = (fieldName: string) => {
    const analyzer = getOrCreateAnalyzer('DhLlmScoreAnalyzer');
    const newFieldMap = { ...(analyzer.field_map || {}) };
    delete newFieldMap[fieldName];

    updateAnalyzer({
      ...analyzer,
      field_map: newFieldMap,
    });
  };

  const currentAnalyzer = getOrCreateAnalyzer(
    selectedAnalyzer === 'Term Matching' ? 'KeywordScoreAnalyzer' : 'DhLlmScoreAnalyzer'
  );

  return (
    <div className="grid grid-cols-4 gap-6">
      {/* Analyzer Selection */}
      <div className="col-span-1">
        <h3 className="text-lg font-medium mb-4">Analyzer</h3>
        <div className="space-y-2">
          {['Term Matching', 'DH LLM Prompt'].map((analyzer) => (
            <button
              key={analyzer}
              onClick={() => setSelectedAnalyzer(analyzer)}
              className={`w-full text-left px-3 py-2 rounded ${
                selectedAnalyzer === analyzer
                  ? 'bg-ringer-blue text-white'
                  : 'bg-gray-100 hover:bg-gray-200'
              }`}
            >
              {analyzer}
            </button>
          ))}
        </div>
      </div>

      {/* Analyzer Configuration */}
      <div className="col-span-3">
        {selectedAnalyzer === 'Term Matching' && (
          <div>
            <div className="flex items-center justify-between mb-4">
              <h4 className="text-lg font-medium">Terms</h4>
              <div className="flex items-center space-x-3">
                <label className="text-lg font-medium text-gray-700">
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
                  className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ringer-blue disabled:bg-gray-100"
                />
              </div>
            </div>
            
            {/* Terms Table */}
            <div className="border border-gray-300 mb-4">
              <table className="w-full">
                <thead className="bg-table-header">
                  <tr>
                    <th className="px-4 py-2 text-left text-sm font-medium text-black border-r border-gray-300">Type</th>
                    <th className="px-4 py-2 text-left text-sm font-medium text-black border-r border-gray-300">Term</th>
                    <th className="px-4 py-2 text-left text-sm font-medium text-black border-r border-gray-300">Match Case</th>
                    <th className="px-4 py-2 text-left text-sm font-medium text-black border-r border-gray-300">Weight</th>
                    {isNewCrawl && (
                      <th className="px-4 py-2 text-left text-sm font-medium text-black">Actions</th>
                    )}
                  </tr>
                </thead>
                <tbody>
                  {(currentAnalyzer.keywords || []).map((keyword, index) => (
                    <tr key={`keyword-${index}`} className="border-t border-gray-300">
                      <td className="px-4 py-2 text-sm border-r border-gray-300">Keyword</td>
                      <td className="px-4 py-2 text-sm border-r border-gray-300">{keyword.keyword}</td>
                      <td className="px-4 py-2 text-sm text-center border-r border-gray-300">
                        <input type="checkbox" disabled className="rounded" />
                      </td>
                      <td className="px-4 py-2 text-sm border-r border-gray-300">{keyword.weight}</td>
                      {isNewCrawl && (
                        <td className="px-4 py-2 text-center">
                          <button
                            onClick={() => handleRemoveTerm('keyword', index)}
                            className="w-6 h-6 bg-red-600 text-white rounded-full flex items-center justify-center hover:bg-red-700 text-xs"
                          >
                            ⊖
                          </button>
                        </td>
                      )}
                    </tr>
                  ))}
                  {(currentAnalyzer.regexes || []).map((regex, index) => (
                    <tr key={`regex-${index}`} className="border-t border-gray-300">
                      <td className="px-4 py-2 text-sm border-r border-gray-300">Regex</td>
                      <td className="px-4 py-2 text-sm border-r border-gray-300">{regex.regex}</td>
                      <td className="px-4 py-2 text-sm text-center border-r border-gray-300">
                        <input
                          type="checkbox"
                          checked={regex.flags !== 2}
                          disabled
                          className="rounded"
                        />
                      </td>
                      <td className="px-4 py-2 text-sm border-r border-gray-300">{regex.weight}</td>
                      {isNewCrawl && (
                        <td className="px-4 py-2 text-center">
                          <button
                            onClick={() => handleRemoveTerm('regex', index)}
                            className="w-6 h-6 bg-red-600 text-white rounded-full flex items-center justify-center hover:bg-red-700 text-xs"
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
              <div className="border border-gray-300 bg-gray-50">
                <table className="w-full">
                  <tbody>
                    <tr className="border-t border-gray-300">
                      <td className="px-4 py-2 border-r border-gray-300">
                        <select
                          value={newTerm.type}
                          onChange={(e) => setNewTerm({ ...newTerm, type: e.target.value as 'Keyword' | 'Regex' })}
                          className="w-full px-2 py-1 border border-gray-300 focus:outline-none focus:ring-1 focus:ring-ringer-blue"
                        >
                          <option value="Keyword">Keyword</option>
                          <option value="Regex">Regex</option>
                        </select>
                      </td>
                      <td className="px-4 py-2 border-r border-gray-300">
                        <input
                          type="text"
                          value={newTerm.term}
                          onChange={(e) => setNewTerm({ ...newTerm, term: e.target.value })}
                          placeholder="Enter term..."
                          className="w-full px-2 py-1 border border-gray-300 focus:outline-none focus:ring-1 focus:ring-ringer-blue"
                        />
                      </td>
                      <td className="px-4 py-2 text-center border-r border-gray-300">
                        <input
                          type="checkbox"
                          checked={newTerm.matchCase}
                          onChange={(e) => setNewTerm({ ...newTerm, matchCase: e.target.checked })}
                          className="rounded"
                        />
                      </td>
                      <td className="px-4 py-2 border-r border-gray-300">
                        <input
                          type="number"
                          value={newTerm.weight}
                          onChange={(e) => setNewTerm({ ...newTerm, weight: parseFloat(e.target.value) || 0 })}
                          step="0.1"
                          className="w-full px-2 py-1 border border-gray-300 focus:outline-none focus:ring-1 focus:ring-ringer-blue"
                        />
                      </td>
                      <td className="px-4 py-2 text-center">
                        <button
                          onClick={handleAddTerm}
                          disabled={!newTerm.term.trim()}
                          className="px-3 py-1 bg-ringer-blue text-white hover:bg-ringer-dark-blue disabled:opacity-50"
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
          <div className="space-y-6">
            {/* Composite Weight */}
            <div className="flex items-center justify-between">
              <h4 className="text-lg font-medium">Prompt</h4>
              <div className="flex items-center space-x-3">
                <label className="text-lg font-medium text-gray-700">
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
                  className="w-32 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ringer-blue disabled:bg-gray-100"
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
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-ringer-blue disabled:bg-gray-100"
                placeholder="Enter LLM prompt..."
              />
            </div>

            {/* Output Format */}
            <div>
              <h4 className="text-md font-medium mb-3">Output Format</h4>
              <div className="border border-gray-300">
                <table className="w-full">
                  <thead className="bg-table-header">
                    <tr>
                      <th className="px-4 py-2 text-left text-sm font-medium text-black border-r border-gray-300">Name</th>
                      <th className="px-4 py-2 text-left text-sm font-medium text-black border-r border-gray-300">Type</th>
                      {isNewCrawl && (
                        <th className="px-4 py-2 text-left text-sm font-medium text-black">Actions</th>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(currentAnalyzer.field_map || {}).map(([name, type]) => (
                      <tr key={name} className="border-t border-gray-300">
                        <td className="px-4 py-2 text-sm border-r border-gray-300">{name}</td>
                        <td className="px-4 py-2 text-sm border-r border-gray-300">{type}</td>
                        {isNewCrawl && (
                          <td className="px-4 py-2 text-center">
                            <button
                              onClick={() => handleRemoveOutputField(name)}
                              className="w-6 h-6 bg-red-600 text-white rounded-full flex items-center justify-center hover:bg-red-700 text-xs"
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

              {/* Add Output Field Controls */}
              {isNewCrawl && (
                <div className="border-t border-gray-300 bg-gray-50">
                  <table className="w-full">
                    <tbody>
                      <tr>
                        <td className="px-4 py-2 border-r border-gray-300">
                          <input
                            type="text"
                            value={newOutputField.name}
                            onChange={(e) => setNewOutputField({ ...newOutputField, name: e.target.value })}
                            placeholder="Field name..."
                            className="w-full px-2 py-1 border border-gray-300 focus:outline-none focus:ring-1 focus:ring-ringer-blue"
                          />
                        </td>
                        <td className="px-4 py-2 border-r border-gray-300">
                          <select
                            value={newOutputField.type}
                            onChange={(e) => setNewOutputField({ ...newOutputField, type: e.target.value })}
                            className="w-full px-2 py-1 border border-gray-300 focus:outline-none focus:ring-1 focus:ring-ringer-blue"
                          >
                            <option value="string">string</option>
                            <option value="float">float</option>
                            <option value="int">int</option>
                            <option value="bool">bool</option>
                          </select>
                        </td>
                        <td className="px-4 py-2 text-center">
                          <button
                            onClick={handleAddOutputField}
                            disabled={!newOutputField.name.trim()}
                            className="w-6 h-6 bg-ringer-blue text-white rounded-sm flex items-center justify-center hover:bg-ringer-dark-blue disabled:opacity-50 text-sm font-bold"
                          >
                            +
                          </button>
                        </td>
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};
