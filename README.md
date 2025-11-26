# Time Series Dashboard

A modern web application for analyzing financial and macroeconomic time series data with AI-powered insights. Load data from Yahoo Finance or Haver Analytics, select a time period of interest, and use AI-powered web search to understand what caused price movements.

## Features

- **Yahoo Finance Integration**: Load any stock ticker data (e.g., NVDA, AAPL, MSFT)
- **Haver Analytics Integration**: Browse databases and series hierarchically
- **Interactive Charts**: Visualize time series with Recharts
- **Range Selection**: Use the brush selector to highlight a period of interest
- **AI-Powered Analysis**: Search for explanations of price movements using Parallel API

## Architecture

```
├── backend/                  # FastAPI Python backend
│   ├── main.py              # FastAPI app with endpoints
│   ├── services/
│   │   ├── yahoo_finance.py # yfinance data fetching
│   │   ├── haver_service.py # Haver Analytics integration
│   │   └── parallel_search.py # Parallel API for web search
│   └── requirements.txt
├── frontend/                 # React + TypeScript
│   ├── src/
│   │   ├── components/      # React components
│   │   ├── hooks/           # Custom hooks
│   │   └── App.tsx          # Main application
│   └── package.json
└── README.md
```

## Prerequisites

- Python 3.9+
- Node.js 18+
- API Keys:
  - `PARALLEL_API_KEY` - For AI-powered web search
  - `HAVER_API_KEY` - For Haver Analytics data (optional, only needed for macro data)

## Setup

### 1. Clone and Setup Environment Variables

```bash
# Create a .env file in the backend directory
cd backend
cp ../.env.example .env  # Or create manually

# Edit .env and add your API keys:
# PARALLEL_API_KEY=your_parallel_api_key_here
# HAVER_API_KEY=your_haver_api_key_here
```

### 2. Backend Setup

```bash
# Navigate to backend directory
cd backend

# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
# venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Frontend Setup

```bash
# Navigate to frontend directory
cd frontend

# Install dependencies
npm install
```

## Running the Application

### Option 1: Run Both Servers Separately

**Terminal 1 - Backend:**
```bash
cd backend
source venv/bin/activate  # or venv\Scripts\activate on Windows
uvicorn main:app --reload --port 8000
```

**Terminal 2 - Frontend:**
```bash
cd frontend
npm run dev
```

### Option 2: Quick Start Script

Create a `start.sh` script:
```bash
#!/bin/bash
# Start backend in background
cd backend && source venv/bin/activate && uvicorn main:app --reload --port 8000 &
# Start frontend
cd frontend && npm run dev
```

## Usage

1. **Open the Application**: Navigate to `http://localhost:3000`

2. **Select Data Source**:
   - **Yahoo Finance**: Enter a stock ticker (e.g., `NVDA`, `AAPL`, `TSLA`)
   - **Haver Analytics**: Browse databases → Select a database → Select a series

3. **Load Data**: Click "Load Data" to fetch and display the time series

4. **Select a Time Range**: Use the brush selector at the bottom of the chart to highlight a period you want to analyze

5. **Ask a Question**: Enter your question about the price movement (e.g., "Why did the stock increase during this period?")

6. **Get AI-Powered Insights**: Click "Search for Explanation" to get AI-analyzed results with citations

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/yahoo/{ticker}` | GET | Fetch Yahoo Finance data |
| `/api/haver/databases` | GET | List Haver databases |
| `/api/haver/series/{database}` | GET | List series in a database |
| `/api/haver/{database}/{series}` | GET | Fetch Haver time series |
| `/api/search` | POST | AI-powered event search |

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `PARALLEL_API_KEY` | Yes | API key for Parallel web search |
| `HAVER_API_KEY` | No | API key for Haver Analytics (needed for macro data) |

## Tech Stack

**Backend:**
- FastAPI - Modern Python web framework
- yfinance - Yahoo Finance data fetching
- haver - Haver Analytics Python client
- parallel - Parallel AI API client

**Frontend:**
- React 18 with TypeScript
- Vite - Build tool
- Recharts - Charting library with brush selection
- Tailwind CSS - Styling
- Axios - HTTP client

## Troubleshooting

### Backend won't start
- Ensure Python 3.9+ is installed
- Check that all dependencies are installed: `pip install -r requirements.txt`
- Verify `.env` file exists with required API keys

### Frontend won't start
- Ensure Node.js 18+ is installed
- Run `npm install` to install dependencies
- Check that port 3000 is available

### Can't connect to API
- Ensure backend is running on port 8000
- Check CORS settings if running on different ports
- Verify the proxy configuration in `vite.config.ts`

### Haver data not loading
- Verify `HAVER_API_KEY` is set correctly
- Check that you have access to the requested database

## License

MIT
