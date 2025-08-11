# Prospector - Best-First-Search Web Crawler

[![Python 3.12](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Prospector** is a sophisticated web crawler that implements a **best-first-search** strategy to intelligently prioritize crawling based on content relevance. Unlike traditional breadth-first crawlers that visit all links equally, Prospector scores content and visits the most relevant pages first.

## 🎯 Overview

Prospector combines intelligent content analysis with efficient crawling to:
- **Prioritize relevant content** using configurable scoring algorithms
- **Scale crawling operations** with concurrent worker pools
- **Adapt to different content types** through pluggable analyzers and handlers
- **Provide robust error handling** with retry logic and comprehensive logging

## 📋 Requirements & Design Philosophy

### Core Requirements
- **Best-first search crawling** with content-based prioritization
- **Concurrent processing** with configurable worker pools
- **Pluggable architecture** for analyzers, scrapers, and handlers
- **Comprehensive error handling** with logging and recovery
- **Configuration-driven** operation via Pydantic Settings
- **Production-ready** with proper resource management

### Design Principles
- **Modularity**: Each component has a single responsibility
- **Extensibility**: Easy to add new analyzers, scrapers, and handlers
- **Configurability**: All behavior controlled via settings and environment variables
- **Robustness**: Graceful handling of failures at every level
- **Performance**: Efficient resource usage with connection pooling and async operations

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Prospector    │    │   ScoreAnalyzer │    │ CrawlRecordHandler│
│   (Orchestrator)│───▶│   (Content      │───▶│   (Output       │
│                 │    │    Scoring)     │    │    Processing)  │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       ▲                       
         ▼                       │                       
┌─────────────────┐    ┌─────────────────┐              
│     Scraper     │    │   CrawlRecord   │              
│  (Web Content   │───▶│   (Data Model)  │              
│   Extraction)   │    │                 │              
└─────────────────┘    └─────────────────┘              
```

## 🧩 Core Components

### 1. Prospector (Main Orchestrator)

The **Prospector** class is the central orchestrator that manages the entire crawling process.

**Key Responsibilities:**
- Manages multiple concurrent crawls with separate state tracking
- Maintains thread-safe frontier queues sorted by content relevance scores
- Coordinates worker pools for parallel URL processing
- Integrates all components (scrapers, analyzers, handlers)

**Design Features:**
- **Thread-safe state management** using locks and thread-safe data structures
- **Best-first frontier** implemented with `SortedList` for efficient ordering
- **Worker pool coordination** with configurable concurrency
- **Lifecycle management** for starting, stopping, and cleaning up crawls

```python
# Example usage
prospector = Prospector()
crawl_id = prospector.submit(crawl_spec)
prospector.start(crawl_id)
```

### 2. Scrapers (Content Extraction)

**Scrapers** extract content and links from web pages, handling both static and dynamic content.

#### PlaywrightScraper
- **Purpose**: Extract content from modern web pages with JavaScript
- **Technology**: Uses Playwright for browser automation
- **Features**: 
  - Dynamic content rendering
  - Configurable timeouts and user agents
  - Link extraction and normalization
  - Error handling for network issues

**Design Pattern:**
```python
class Scraper(ABC):
    @abstractmethod
    def scrape(self, url: str) -> CrawlRecord:
        """Extract content and links from a web page."""
```

### 3. ScoreAnalyzers (Content Intelligence)

**ScoreAnalyzers** evaluate content relevance using different algorithms, enabling intelligent crawl prioritization.

#### KeywordScoreAnalyzer
- **Purpose**: Score content based on keyword matching
- **Algorithm**: Weighted keyword counting with sigmoid normalization
- **Features**:
  - Case-insensitive matching
  - Multiple occurrence counting
  - Configurable keyword weights
  - Normalized 0-1 scoring range

#### LLMServiceScoreAnalyzer
- **Purpose**: Leverage AI/LLM services for sophisticated content evaluation
- **Integration**: HTTP POST requests to external LLM services
- **Features**:
  - Configurable prompts and output formats
  - Connection pooling for performance
  - Comprehensive error handling
  - Retry logic with exponential backoff

**Design Pattern:**
```python
class ScoreAnalyzer(ABC):
    @abstractmethod
    def score(self, content: Any) -> float:
        """Return relevance score between 0 and 1."""
```

### 4. CrawlRecordHandlers (Output Processing)

**CrawlRecordHandlers** process and store crawled content using different storage strategies.

#### FsStoreCrawlRecordHandler
- **Purpose**: Store crawl records as JSON files on the filesystem
- **Organization**: Structured by crawl name and datetime
- **Features**:
  - Automatic directory creation
  - URL-based filename generation (MD5 hash)
  - JSON serialization with proper encoding

#### ServiceCrawlRecordHandler
- **Purpose**: Send crawl records to external web services
- **Integration**: HTTP POST with JSON payloads
- **Features**:
  - Tenacity-based retry logic (3 attempts, exponential backoff)
  - Connection pooling for efficiency
  - Comprehensive error logging
  - Graceful failure handling

**Design Pattern:**
```python
class CrawlRecordHandler(ABC):
    @abstractmethod
    def handle(self, crawl_record: CrawlRecord, crawl_name: str, crawl_datetime: str):
        """Process a crawl record."""
```

## 🔧 Technology Stack

### Core Dependencies
- **Python 3.12+**: Modern Python with type hints and performance improvements
- **Pydantic v2**: Data validation, serialization, and settings management
- **Pydantic Settings**: Environment-based configuration
- **SortedContainers**: Efficient sorted data structures for frontier management
- **Requests**: HTTP client with session management and connection pooling
- **Tenacity**: Retry logic with configurable strategies

### Web Scraping
- **Playwright**: Browser automation for dynamic content extraction
- **urllib.parse**: URL parsing and normalization

### Testing & Quality
- **Pytest**: Comprehensive testing framework
- **Syrupy**: Snapshot testing for complex data structures
- **unittest.mock**: Mocking and patching for isolated testing

### Optional Integrations
- **External LLM Services**: REST APIs for AI-powered content scoring
- **External Storage Services**: HTTP endpoints for crawl record processing

## 📁 Project Structure

```
prospector/                                      # Prospector project root folder
├── src/                                         # Source folder
    ├── prospector/                              # Prospector top-level package
       ├── core/                                 # Core component package
           ├── __init__.py                       # Package initialization and exports
           ├── models.py                         # Pydantic data models
           ├── prospector.py                     # Prospector orchestrator
           ├── handlers/                         # Crawl output handlers package
               ├── __init__.py                   # Package initialization and exports
               ├── service_call_handler.py       # Service call output processing
               └── fs_store_handler.py           # Filesystem storage output processing
           ├── score_analyzers/                  # Page scoring package
               ├── __init__.py                   # Package initialization and exports
               ├── keyword_score_analyzer.py.    # Keyword matching scorer
               └── llm_service_score_analyzer.py # LLM service-based scorer
           ├── scrapers/                         # Web scapers package
               ├── __init__.py                   # Package initialization and exports
               ├── scraper.py                    # Web scraper abstract base class
               └── playwright_scraper.py         # Web scraper plarywright implementation
           ├── settings/                         # Configuration package
               ├── __init__.py                   # Package initialization and exports
               └── settings.py                   # Configuration classes
       ├── api/v1                                # Version 1 FastAPI web API package
            ├── __init__.py                      # Package initialization and exports
            ├── api.py                           # FastAPI APIRouter
            ├── models.py                        # Pydantic web API models
            └── routers/                         # Pydantic Routers for endpoint groups
                ├── __init__.py                  # Package initialization and exports
                ├── crawl.py                     # FastAPI Router with crawl-related endpoints
       ├── logging.yml                           # Logging configuration YAML file
       └── main.py                               # FastAPI web service main file
├── tests/                                       # Tests folder
    ├── conftest.py                              # Pytest fixtures and configuration
    ├── test_prospector.py                       # Core orchestrator tests
    ├── test_scrapers.py                         # Scraper component tests
    ├── test_score_analyzers.py                  # Analyzer component tests
    ├── test_handlers.py                         # Handler component tests
    └── test_models.py                           # Data model tests
├── pytest.ini                                   # Pytest configuration
└──README.md                                     # This documentation
```

## ⚙️ Configuration

### Environment Variables

Prospector uses environment variable prefixes for different components:

```bash
# Prospector Core Settings
PROSPECTOR_HANDLER_TYPE=file_system  # or service_call
PROSPECTOR_MAX_WORKERS=10

# Scraper Settings  
SCRAPER_TIMEOUT=30
SCRAPER_USER_AGENT="Prospector/1.0"
SCRAPER_JAVASCRIPT_ENABLED=true

# Score Analyzer Settings
ANALYZER_LLM_SERVICE_URL=http://localhost:8000/score
ANALYZER_LLM_REQUEST_TIMEOUT=60

# Handler Settings
HANDLER_OUTPUT_DIRECTORY=./crawl_data
HANDLER_SERVICE_URL=http://localhost:8000/handle_record
HANDLER_SERVICE_MAX_RETRIES=3
```

### Programmatic Configuration

```python
from prospector.settings import ProspectorSettings, HandlerType

settings = ProspectorSettings(
    handler_type=HandlerType.SERVICE_CALL,
    max_workers=8
)
```

## 🚀 Usage Examples

### Basic Crawling with Keyword Analysis

```python
from prospector import (
    Prospector, CrawlSpec, AnalyzerSpec, WeightedKeyword
)

# Define scoring criteria
keywords = [
    WeightedKeyword(keyword="python", weight=1.0),
    WeightedKeyword(keyword="machine learning", weight=0.8),
    WeightedKeyword(keyword="tutorial", weight=0.6)
]

# Configure analyzer
analyzer_spec = AnalyzerSpec(
    name="KeywordScoreAnalyzer",
    composite_weight=1.0,
    params=keywords
)

# Set up crawl
crawl_spec = CrawlSpec(
    name="python_tutorials",
    seed_urls=["https://docs.python.org", "https://realpython.com"],
    analyzer_specs=[analyzer_spec],
    worker_count=4,
    domain_blacklist=["spam.com", "malicious.net"]
)

# Execute crawl
prospector = Prospector()
crawl_id = prospector.submit(crawl_spec)
prospector.start(crawl_id)

# Later: stop and cleanup
prospector.stop(crawl_id)
prospector.delete(crawl_id)
```

### Multi-Analyzer Crawling (Keywords + LLM)

```python
from prospector import LLMServiceScoreAnalyzer

# Combine keyword and LLM analysis
keyword_spec = AnalyzerSpec(
    name="KeywordScoreAnalyzer",
    composite_weight=0.4,
    params=keywords
)

llm_spec = AnalyzerSpec(
    name="LLMServiceScoreAnalyzer", 
    composite_weight=0.6,
    params=None  # Uses configured LLM service
)

crawl_spec = CrawlSpec(
    name="hybrid_analysis_crawl",
    seed_urls=["https://example.com"],
    analyzer_specs=[keyword_spec, llm_spec],
    worker_count=3
)
```

### Service-Based Output Processing

```python
import os
from prospector.settings import HandlerType

# Configure for service output
os.environ['PROSPECTOR_HANDLER_TYPE'] = 'service_call'
os.environ['HANDLER_SERVICE_URL'] = 'https://api.mycompany.com/crawl-records'

# Prospector will automatically use ServiceCrawlRecordHandler
prospector = Prospector()
```

## 🧪 Testing

### Running Tests

```bash
# Install dependencies
pip install pytest playwright tenacity

# Install Playwright browsers
playwright install chromium

# Run all tests
pytest -v

# Run specific test categories
pytest tests/test_prospector.py -v
pytest tests/test_score_analyzers.py -v

# Run with coverage
pytest --cov=prospector tests/
```

### Test Structure

- **Unit Tests**: Each component tested in isolation with mocks
- **Integration Tests**: Cross-component interaction testing
- **Error Handling Tests**: Comprehensive failure scenario coverage
- **Performance Tests**: Thread safety and concurrency validation

## 🔮 Future Enhancements

### Planned Features
- **Persistent State**: Redis/database integration for crawl resumption
- **Advanced Scrapers**: Support for PDFs, images, and multimedia content
- **Machine Learning Analyzers**: Built-in ML models for content classification
- **Distributed Crawling**: Multi-node coordination for large-scale operations
- **Real-time Monitoring**: WebSocket-based crawl progress tracking
- **Content Deduplication**: Advanced algorithms for identifying duplicate content

### Extension Points
- **Custom Scrapers**: Implement domain-specific content extraction
- **Specialized Analyzers**: Add industry-specific scoring algorithms  
- **Alternative Handlers**: Support for databases, cloud storage, message queues
- **Monitoring Integrations**: Prometheus metrics, custom dashboards

## 📄 License

MIT License - see LICENSE file for details.

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup

```bash
git clone https://github.com/your-org/prospector.git
cd prospector
pip install -e .[dev]
pre-commit install
pytest
```

## 📧 Support

For questions, issues, or contributions:
- **Issues**: [GitHub Issues](https://github.com/your-org/prospector/issues)
- **Discussions**: [GitHub Discussions](https://github.com/your-org/prospector/discussions)
- **Documentation**: [Wiki](https://github.com/your-org/prospector/wiki)

---

## Feature Roadmap

- Revisit Delta Check
- Dynamic content extraction
- Anti-Bot Avoidance
- Search engine seeding

**Prospector** - Intelligent web crawling with best-first search prioritization 🎯