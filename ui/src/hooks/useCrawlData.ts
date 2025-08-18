import { useState, useEffect, useCallback } from 'react';
import { CrawlInfo, CrawlInfoResponse } from '../types';
import { crawlApi } from '../services/api';

export const useCrawlData = () => {
  const [crawls, setCrawls] = useState<CrawlInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const fetchCrawlData = useCallback(async () => {
    try {
      const response: CrawlInfoResponse = await crawlApi.getAllCrawlInfo();
      setCrawls(response.crawls);
      setError(null);
    } catch (err) {
      setError('Failed to fetch crawl data');
      console.error('Error fetching crawl data:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchCrawlData();
    
    // Poll every second
    const interval = setInterval(fetchCrawlData, 1000);
    
    return () => clearInterval(interval);
  }, [fetchCrawlData]);

  return { crawls, loading, error, refetch: fetchCrawlData };
};
