# Ringer UI

A React TypeScript frontend for the Ringer web crawler service.

## Prerequisites

- Node.js 18+ 
- npm or yarn
- Ringer service running

## Development Setup

1. **Install dependencies:**
   ```bash
   cd ui
   npm install
   ```

2. **Configure API base URL (optional):**
   
   The UI connects to `http://ringer` by default. To use a different URL, create a `.env.local` file:
   ```bash
   echo "VITE_API_BASE_URL=http://localhost:8000" > .env.local
   ```

3. **Start the development server:**
   ```bash
   npm run dev
   ```
   
   The UI will be available at `http://localhost:5173`

4. **Build for production:**
   ```bash
   npm run build
   ```
   
   Built files will be in the `dist/` directory.

## Features

- **Crawl Management**: View, create, start, stop, and delete crawls
- **Real-time Updates**: Automatic polling of crawl status every second
- **Source Configuration**: Add seed URLs manually or via search engine queries
- **Analyzer Setup**: Configure keyword matching and LLM-based content scoring
- **Export Functionality**: Download crawl specifications as JSON

## Project Structure

```
ui/
├── src/
│   ├── components/          # React components
│   ├── types/              # TypeScript type definitions
│   ├── services/           # API service functions
│   ├── hooks/              # Custom React hooks
│   └── utils/              # Utility functions
├── public/                 # Static assets
└── dist/                   # Built application (after npm run build)
```

## API Configuration

The UI communicates with the Ringer service via REST API. Configure the base URL using the `VITE_API_BASE_URL` environment variable.

Default endpoints used:
- `GET /api/v1/crawl/info` - Fetch all crawl information
- `POST /api/v1/crawl/create` - Create new crawl
- `POST /api/v1/crawl/start` - Start crawl
- `POST /api/v1/crawl/stop` - Stop crawl  
- `DELETE /api/v1/crawl/delete` - Delete crawl
- `GET /api/v1/crawl/{crawl_id}/spec/export` - Export crawl spec
- `POST /api/v1/seeds/collect` - Collect seed URLs from search engines

## Development Commands

- `npm run dev` - Start development server with hot reload
- `npm run build` - Build for production
- `npm run preview` - Preview production build locally
- `npm run lint` - Run ESLint code analysis

## Troubleshooting

**Connection Issues:**
- Ensure Ringer service is running and accessible
- Check API base URL configuration in `.env.local`
- Verify CORS settings on the Ringer service

**Build Issues:**
- Clear node_modules and reinstall: `rm -rf node_modules package-lock.json && npm install`
- Check TypeScript errors: `npx tsc --noEmit`
