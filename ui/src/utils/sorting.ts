import { CrawlInfo, SortConfig } from '../types';

export const sortCrawls = (crawls: CrawlInfo[], sortConfig: SortConfig): CrawlInfo[] => {
  return [...crawls].sort((a, b) => {
    let aValue: any;
    let bValue: any;

    switch (sortConfig.key) {
      case 'name':
        aValue = a.crawl_spec.name;
        bValue = b.crawl_spec.name;
        break;
      case 'status':
        aValue = a.crawl_status.current_state;
        bValue = b.crawl_status.current_state;
        break;
      case 'results':
        aValue = a.crawl_status.crawled_count;
        bValue = b.crawl_status.crawled_count;
        break;
      case 'created':
        aValue = new Date(a.crawl_status.state_history[0]?.timestamp || 0);
        bValue = new Date(b.crawl_status.state_history[0]?.timestamp || 0);
        break;
      case 'lastUpdate':
        const aLastState = a.crawl_status.state_history[a.crawl_status.state_history.length - 1];
        const bLastState = b.crawl_status.state_history[b.crawl_status.state_history.length - 1];
        aValue = new Date(aLastState?.timestamp || 0);
        bValue = new Date(bLastState?.timestamp || 0);
        break;
      default:
        return 0;
    }

    if (aValue < bValue) {
      return sortConfig.direction === 'asc' ? -1 : 1;
    }
    if (aValue > bValue) {
      return sortConfig.direction === 'asc' ? 1 : -1;
    }
    return 0;
  });
};
