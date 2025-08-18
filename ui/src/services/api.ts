import axios from 'axios';
import {
  CrawlInfoResponse,
  CreateCrawlRequest,
  CreateCrawlResponse,
  StartCrawlRequest,
  StartCrawlResponse,
  StopCrawlRequest,
  StopCrawlResponse,
  DeleteCrawlRequest,
  DeleteCrawlResponse,
  SeedUrlScrapeRequest,
  SeedUrlScrapeResponse,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://prospector';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
});

export const crawlApi = {
  // Get all crawl information
  getAllCrawlInfo: async (): Promise<CrawlInfoResponse> => {
    const response = await api.get('/api/v1/crawl/info');
    return response.data;
  },

  // Create a new crawl
  createCrawl: async (request: CreateCrawlRequest): Promise<CreateCrawlResponse> => {
    const response = await api.post('/api/v1/crawl/create', request);
    return response.data;
  },

  // Start a crawl
  startCrawl: async (request: StartCrawlRequest): Promise<StartCrawlResponse> => {
    const response = await api.post('/api/v1/crawl/start', request);
    return response.data;
  },

  // Stop a crawl
  stopCrawl: async (request: StopCrawlRequest): Promise<StopCrawlResponse> => {
    const response = await api.post('/api/v1/crawl/stop', request);
    return response.data;
  },

  // Delete a crawl
  deleteCrawl: async (request: DeleteCrawlRequest): Promise<DeleteCrawlResponse> => {
    const response = await api.delete('/api/v1/crawl/delete', { data: request });
    return response.data;
  },

  // Export crawl spec
  exportCrawlSpec: async (crawlId: string): Promise<void> => {
    const response = await api.get(`/api/v1/crawl/${crawlId}/spec/export`, {
      responseType: 'blob',
    });
    
    // Create download link
    const url = window.URL.createObjectURL(new Blob([response.data]));
    const link = document.createElement('a');
    link.href = url;
    
    // Extract filename from content-disposition header
    const contentDisposition = response.headers['content-disposition'];
    let filename = `crawl_spec_${crawlId}.json`;
    if (contentDisposition) {
      const filenameMatch = contentDisposition.match(/filename=(.+)/);
      if (filenameMatch) {
        filename = filenameMatch[1].replace(/"/g, '');
      }
    }
    
    link.setAttribute('download', filename);
    document.body.appendChild(link);
    link.click();
    link.remove();
    window.URL.revokeObjectURL(url);
  },

  // Collect seed URLs from search engines
  collectSeedUrls: async (request: SeedUrlScrapeRequest): Promise<SeedUrlScrapeResponse> => {
    const response = await api.post('/api/v1/seeds/collect', request);
    return response.data;
  },
};
