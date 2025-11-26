# Crypto and Forex Data Implementation

This document outlines the implementation of cryptocurrency and forex data support in the Time Series Dashboard.

## Overview

Added support for two new data sources:
1. **Cryptocurrency Data** - Access to popular cryptocurrencies via Yahoo Finance
2. **Forex Data** - Foreign exchange rates for major currency pairs via Yahoo Finance

## Backend Changes

### New Services

#### 1. `backend/services/crypto_service.py`
- Fetches cryptocurrency data using yfinance
- Supports popular cryptos: BTC, ETH, SOL, XRP, ADA, DOGE, and more
- Auto-normalizes ticker formats (e.g., `BTC` → `BTC-USD`)
- Returns data with proper currency metadata

Key Functions:
- `fetch_crypto_data(ticker, start_date, end_date)` - Fetch crypto price data
- `list_popular_cryptos()` - Returns list of supported cryptocurrencies
- `normalize_crypto_ticker(ticker)` - Handles various ticker formats

#### 2. `backend/services/forex_service.py`
- Fetches forex exchange rate data using yfinance
- Supports major currency pairs: EUR/USD, GBP/USD, USD/JPY, etc.
- Handles multiple ticker formats (EURUSD, EUR/USD, EURUSD=X)
- Returns data with base and quote currency metadata

Key Functions:
- `fetch_forex_data(pair, start_date, end_date)` - Fetch forex rates
- `list_popular_forex_pairs()` - Returns list of supported pairs
- `normalize_forex_ticker(ticker)` - Parses and validates forex pair formats

### API Endpoints

Added 4 new endpoints in `backend/main.py`:

1. **GET `/api/crypto/popular`**
   - Lists all available cryptocurrencies
   - Returns: `{ "cryptos": [{ "symbol": "BTC", "ticker": "BTC-USD", "name": "BTC" }, ...] }`

2. **GET `/api/crypto/{ticker}`**
   - Fetches crypto price data
   - Query params: `start_date`, `end_date` (optional)
   - Returns: `CryptoTimeSeriesData` with timestamps, values, and currency

3. **GET `/api/forex/popular`**
   - Lists all available forex pairs
   - Returns: `{ "pairs": [{ "pair": "EURUSD", "base": "EUR", "quote": "USD", ... }, ...] }`

4. **GET `/api/forex/{pair}`**
   - Fetches forex exchange rate data
   - Query params: `start_date`, `end_date` (optional)
   - Returns: `ForexTimeSeriesData` with timestamps, values, and currency pair info

## Frontend Changes

### Type Definitions

Updated `frontend/src/types.ts`:
- Added `'crypto'` and `'forex'` to `DataSource` type
- New interfaces:
  - `CryptoSymbol` - Crypto symbol metadata
  - `CryptoTimeSeriesData` - Crypto data response
  - `ForexPair` - Forex pair metadata
  - `ForexTimeSeriesData` - Forex data response

### API Client

Updated `frontend/src/api.ts`:
- `fetchPopularCryptos()` - Get list of cryptos
- `fetchCryptoData(ticker, startDate?, endDate?)` - Fetch crypto data
- `fetchPopularForexPairs()` - Get list of forex pairs
- `fetchForexData(pair, startDate?, endDate?)` - Fetch forex data

### Components

#### DataSourceSelector (`frontend/src/components/DataSourceSelector.tsx`)
- Added two new tabs: "Crypto" and "Forex"
- New UI for selecting cryptocurrencies from dropdown
- New UI for selecting forex pairs from dropdown
- Auto-loads popular options when tab is selected

#### useTimeSeriesData Hook (`frontend/src/hooks/useTimeSeriesData.ts`)
- Added `loadCryptoData(ticker)` function
- Added `loadForexData(pair)` function
- Proper currency and ticker formatting for each data source

#### App Component (`frontend/src/App.tsx`)
- Integrated crypto and forex handlers with DataSourceSelector
- Passes new handler functions to child components

## Data Flow

```
User selects "Crypto" tab
    ↓
Component loads popular cryptos via API
    ↓
User selects cryptocurrency (e.g., BTC)
    ↓
Frontend calls fetchCryptoData("BTC")
    ↓
Backend normalizes to "BTC-USD"
    ↓
Backend fetches data from Yahoo Finance via yfinance
    ↓
Backend returns structured data with timestamps, values, currency
    ↓
Frontend transforms and displays in chart
```

## Supported Assets

### Cryptocurrencies (15+)
- Bitcoin (BTC)
- Ethereum (ETH)
- Tether (USDT)
- Binance Coin (BNB)
- Solana (SOL)
- XRP
- USD Coin (USDC)
- Cardano (ADA)
- Dogecoin (DOGE)
- TRON (TRX)
- Avalanche (AVAX)
- Polkadot (DOT)
- Polygon (MATIC)
- Chainlink (LINK)
- Uniswap (UNI)

### Forex Pairs (15+)
- EUR/USD - Euro vs US Dollar
- GBP/USD - British Pound vs US Dollar
- USD/JPY - US Dollar vs Japanese Yen
- AUD/USD - Australian Dollar vs US Dollar
- USD/CAD - US Dollar vs Canadian Dollar
- USD/CHF - US Dollar vs Swiss Franc
- NZD/USD - New Zealand Dollar vs US Dollar
- EUR/GBP - Euro vs British Pound
- EUR/JPY - Euro vs Japanese Yen
- GBP/JPY - British Pound vs Japanese Yen
- AUD/JPY - Australian Dollar vs Japanese Yen
- EUR/AUD - Euro vs Australian Dollar
- EUR/CHF - Euro vs Swiss Franc
- GBP/AUD - British Pound vs Australian Dollar
- GBP/CAD - British Pound vs Canadian Dollar

## Benefits

1. **No Additional Dependencies**: Uses existing yfinance library
2. **Consistent API**: Same pattern as Yahoo Finance endpoints
3. **Real-time Data**: Leverages Yahoo Finance's real-time pricing
4. **Flexible Format Support**: Handles multiple ticker/pair formats
5. **Type Safety**: Full TypeScript support throughout

## Testing

To test the new features:

1. **Start the backend**:
   ```bash
   cd backend
   uvicorn main:app --reload
   ```

2. **Start the frontend**:
   ```bash
   cd frontend
   npm run dev
   ```

3. **Test Crypto**:
   - Click "Crypto" tab
   - Select "BTC" from dropdown
   - Click "Load Data"
   - Chart should display Bitcoin price history

4. **Test Forex**:
   - Click "Forex" tab
   - Select "EUR/USD" from dropdown
   - Click "Load Data"
   - Chart should display EUR/USD exchange rate history

## Future Enhancements

Possible improvements:
- Add more cryptocurrencies (top 50-100 by market cap)
- Add exotic forex pairs
- Support for crypto/crypto pairs (BTC/ETH)
- Real-time price updates via websockets
- Additional metadata (24h volume, market cap for crypto)
- Historical volatility indicators
- Support for different base currencies in crypto (EUR, GBP, etc.)
