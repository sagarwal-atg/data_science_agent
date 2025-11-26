# Usage Examples

This guide provides examples of how to use the crypto and forex data features.

## Quick Start

### 1. Load Cryptocurrency Data

**Via UI:**
1. Open the application
2. Click the "Crypto" tab in the data source selector
3. Select a cryptocurrency from the dropdown (e.g., BTC, ETH, SOL)
4. Click "Load Data"

**Via API:**
```bash
# Get list of available cryptos
curl http://localhost:8000/api/crypto/popular

# Get Bitcoin data for last 5 years (default)
curl http://localhost:8000/api/crypto/BTC

# Get Ethereum data for specific date range
curl "http://localhost:8000/api/crypto/ETH?start_date=2024-01-01&end_date=2024-11-26"

# Works with different ticker formats
curl http://localhost:8000/api/crypto/BTC-USD
curl http://localhost:8000/api/crypto/btc
```

**Response:**
```json
{
  "ticker": "BTC-USD",
  "timestamps": ["2019-11-26T00:00:00", "2019-11-27T00:00:00", ...],
  "values": [7156.88, 7322.09, ...],
  "data_type": "close",
  "currency": "USD"
}
```

### 2. Load Forex Data

**Via UI:**
1. Open the application
2. Click the "Forex" tab in the data source selector
3. Select a currency pair from the dropdown (e.g., EUR/USD, GBP/USD)
4. Click "Load Data"

**Via API:**
```bash
# Get list of available forex pairs
curl http://localhost:8000/api/forex/popular

# Get EUR/USD data
curl http://localhost:8000/api/forex/EURUSD

# Works with different formats
curl http://localhost:8000/api/forex/EUR/USD
curl http://localhost:8000/api/forex/EURUSD=X

# Get data for specific date range
curl "http://localhost:8000/api/forex/GBPUSD?start_date=2024-01-01&end_date=2024-11-26"
```

**Response:**
```json
{
  "ticker": "EURUSD=X",
  "base_currency": "EUR",
  "quote_currency": "USD",
  "timestamps": ["2019-11-26T00:00:00", "2019-11-27T00:00:00", ...],
  "values": [1.1012, 1.1024, ...],
  "data_type": "close"
}
```

## Analysis Examples

### Example 1: Analyze Bitcoin Price Drop

1. Load BTC data
2. Use the brush selector to select a period of decline
3. Switch to the "Explain" tab
4. Ask: "Why did Bitcoin drop during this period?"
5. Get AI-powered analysis with news citations

### Example 2: Find Critical Events in EUR/USD

1. Load EUR/USD data
2. Switch to the "Events" tab
3. Click "Find Critical Events"
4. View timeline of major economic events affecting the exchange rate

### Example 3: Forecast Ethereum Price

1. Load ETH data
2. Switch to the "Forecast" tab
3. Select a future date range using the range selector
4. Click "Run Backtest"
5. View forecast accuracy with MAPE metrics

## Python Examples

### Using the Services Directly

```python
from services.crypto_service import fetch_crypto_data, list_popular_cryptos
from services.forex_service import fetch_forex_data, list_popular_forex_pairs
import asyncio

async def main():
    # Get popular cryptos
    cryptos = await list_popular_cryptos()
    print(f"Available cryptos: {[c['symbol'] for c in cryptos]}")
    
    # Fetch Bitcoin data
    btc_data = await fetch_crypto_data("BTC", "2024-01-01", "2024-11-26")
    print(f"BTC: {len(btc_data.timestamps)} data points")
    print(f"Latest price: ${btc_data.values[-1]:,.2f} {btc_data.currency}")
    
    # Get popular forex pairs
    pairs = await list_popular_forex_pairs()
    print(f"Available pairs: {[p['pair'] for p in pairs]}")
    
    # Fetch EUR/USD data
    eurusd_data = await fetch_forex_data("EURUSD", "2024-01-01", "2024-11-26")
    print(f"EUR/USD: {len(eurusd_data.timestamps)} data points")
    print(f"Latest rate: {eurusd_data.values[-1]:.4f}")

asyncio.run(main())
```

## JavaScript/TypeScript Examples

### Using the API Client

```typescript
import { 
  fetchCryptoData, 
  fetchForexData, 
  fetchPopularCryptos,
  fetchPopularForexPairs 
} from './api';

// Get and display crypto data
async function loadBitcoin() {
  try {
    const data = await fetchCryptoData('BTC', '2024-01-01', '2024-11-26');
    console.log(`Loaded ${data.timestamps.length} BTC data points`);
    console.log(`Latest: $${data.values[data.values.length - 1]} ${data.currency}`);
  } catch (error) {
    console.error('Failed to load Bitcoin data:', error);
  }
}

// Get and display forex data
async function loadEURUSD() {
  try {
    const data = await fetchForexData('EURUSD', '2024-01-01', '2024-11-26');
    console.log(`Loaded ${data.timestamps.length} EUR/USD data points`);
    console.log(`${data.base_currency}/${data.quote_currency}: ${data.values[data.values.length - 1]}`);
  } catch (error) {
    console.error('Failed to load EUR/USD data:', error);
  }
}

// List all available options
async function listAvailableData() {
  const cryptos = await fetchPopularCryptos();
  const pairs = await fetchPopularForexPairs();
  
  console.log('Cryptocurrencies:', cryptos.map(c => c.symbol).join(', '));
  console.log('Forex Pairs:', pairs.map(p => p.pair).join(', '));
}
```

## Integration with Existing Features

### 1. Crypto + AI Explanation

```typescript
// Load crypto data
await loadCryptoData('BTC');

// Select a date range
const range = {
  startDate: '2024-10-01',
  endDate: '2024-11-01',
  startIndex: 250,
  endIndex: 280
};

// Search for explanation
const result = await searchTimeSeriesEvent({
  ticker: 'BTC-USD',
  query: 'Why did Bitcoin surge in October 2024?',
  start_date: range.startDate,
  end_date: range.endDate,
  change_description: 'increased by 15000.00 (+18.5%)'
});

console.log(result.content); // AI-generated explanation
```

### 2. Forex + Critical Events

```typescript
// Load forex data
await loadForexData('EURUSD');

// Find critical events
const events = await searchCriticalEvents({
  ticker: 'EUR/USD',
  start_date: '2024-01-01',
  end_date: '2024-11-26',
  num_events: 10
});

events.events.forEach(event => {
  console.log(`${event.date}: ${event.summary}`);
});
```

### 3. Crypto + Backtesting

```typescript
// Load Ethereum data
const ethData = await fetchCryptoData('ETH');

// Run backtest
const backtest = await runBacktest({
  ticker: 'ETH-USD',
  timestamps: ethData.timestamps,
  values: ethData.values,
  start_date: '2024-10-01',
  end_date: '2024-11-26'
});

console.log(`Forecast accuracy (MAPE): ${backtest.mape.toFixed(2)}%`);
console.log(`Mean Absolute Error: ${backtest.mae.toFixed(2)}`);
```

## Troubleshooting

### Crypto Data Issues

**Problem**: "No data found for crypto ticker: XXX"
- **Solution**: Check if the crypto is in the supported list. Try using the full format (e.g., `BTC-USD` instead of just `BTC`)

**Problem**: Data seems outdated
- **Solution**: Yahoo Finance data is updated regularly but may have a slight delay. Check the timestamps in the response.

### Forex Data Issues

**Problem**: "Invalid forex ticker format"
- **Solution**: Use one of these formats: `EURUSD`, `EUR/USD`, or `EURUSD=X`

**Problem**: Exchange rate looks inverted
- **Solution**: Check the base and quote currencies in the response. EUR/USD = 1.10 means 1 EUR = 1.10 USD

### API Connection Issues

**Problem**: "Failed to fetch data: Network Error"
- **Solution**: 
  1. Ensure backend is running on port 8000
  2. Check that the frontend proxy is configured correctly
  3. Verify CORS settings in backend

**Problem**: 429 Too Many Requests
- **Solution**: Yahoo Finance has rate limits. Wait a few minutes before making more requests.

## Best Practices

1. **Date Ranges**: Don't request more data than needed. 5 years is often sufficient for most analysis.

2. **Caching**: The backend caches Haver data automatically. Consider implementing similar caching for crypto/forex if making frequent requests.

3. **Error Handling**: Always wrap API calls in try-catch blocks and provide user feedback.

4. **Currency Display**: Always show the currency alongside values for clarity.

5. **Timezone Awareness**: All timestamps are in UTC. Convert to local timezone if needed for display.

6. **Performance**: When displaying large datasets (>1000 points), consider downsampling for the chart while keeping full data for analysis.
