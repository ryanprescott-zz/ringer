export interface RunState {
  state: string;
  timestamp: string;
}

export interface WeightedKeyword {
  keyword: string;
  weight: number;
}

export interface WeightedRegex {
  regex: string;
  weight: number;
  flags: number;
}

export interface ScoringInput {
  prompt: string;
}

export interface FieldMap {
  [key: string]: string;
}

export interface AnalyzerSpec {
  name: string;
  composite_weight: number;
  keywords?: WeightedKeyword[];
  regexes?: WeightedRegex[];
  scoring_input?: ScoringInput;
  field_map?: FieldMap;
}

export interface CrawlSpec {
  name: string;
  seeds: string[];
  analyzer_specs: AnalyzerSpec[];
  worker_count: number;
  domain_blacklist: string[];
}

export interface CrawlStatus {
  crawl_id: string;
  crawl_name: string;
  current_state: string;
  state_history: RunState[];
  crawled_count: number;
  processed_count: number;
  error_count: number;
  frontier_size: number;
}

export interface CrawlInfo {
  crawl_spec: CrawlSpec;
  crawl_status: CrawlStatus;
}

export interface CrawlInfoResponse {
  crawls: CrawlInfo[];
}

export interface CrawlInfoListResponse {
  crawls: CrawlInfo[];
}

export interface CreateCrawlRequest {
  crawl_spec: CrawlSpec;
}

export interface CreateCrawlResponse {
  crawl_id: string;
  run_state: RunState;
}

export interface StartCrawlRequest {
  crawl_id: string;
}

export interface StartCrawlResponse {
  crawl_id: string;
  run_state: RunState;
}

export interface StopCrawlRequest {
  crawl_id: string;
}

export interface StopCrawlResponse {
  crawl_id: string;
  run_state: RunState;
}

export interface DeleteCrawlRequest {
  crawl_id: string;
}

export interface DeleteCrawlResponse {
  crawl_id: string;
  crawl_deleted_time: string;
}

export interface SearchEngineSeed {
  search_engine: string;
  query: string;
  result_count: number;
}

export interface SeedUrlScrapeRequest {
  search_engine_seeds: SearchEngineSeed[];
}

export interface SeedUrlScrapeResponse {
  seed_urls: string[];
}

export type SortDirection = 'asc' | 'desc';

export interface SortConfig {
  key: string;
  direction: SortDirection;
}

export interface NewTerm {
  type: 'Keyword' | 'Regex';
  term: string;
  matchCase: boolean;
  weight: number;
}

export interface OutputField {
  name: string;
  type: string;
}
