import { useState, useEffect } from 'react';
import type { DataSource, HaverDatabase, HaverSeries, CryptoSymbol, ForexPair } from '../types';
import { 
  fetchHaverDatabases, 
  fetchHaverSeries, 
  fetchPopularCryptos, 
  fetchPopularForexPairs 
} from '../api';

interface DataSourceSelectorProps {
  onLoadYahoo: (ticker: string) => void;
  onLoadHaver: (database: string, series: string) => void;
  onLoadCrypto: (ticker: string) => void;
  onLoadForex: (pair: string) => void;
  loading: boolean;
}

export function DataSourceSelector({
  onLoadYahoo,
  onLoadHaver,
  onLoadCrypto,
  onLoadForex,
  loading,
}: DataSourceSelectorProps) {
  const [dataSource, setDataSource] = useState<DataSource>('yahoo');
  const [yahooTicker, setYahooTicker] = useState('NVDA');

  // Haver state
  const [databases, setDatabases] = useState<HaverDatabase[]>([]);
  const [selectedDatabase, setSelectedDatabase] = useState<string>('');
  const [series, setSeries] = useState<HaverSeries[]>([]);
  const [selectedSeries, setSelectedSeries] = useState<string>('');
  const [loadingDatabases, setLoadingDatabases] = useState(false);
  const [loadingSeries, setLoadingSeries] = useState(false);
  const [seriesSearch, setSeriesSearch] = useState('');

  // Crypto state
  const [cryptos, setCryptos] = useState<CryptoSymbol[]>([]);
  const [selectedCrypto, setSelectedCrypto] = useState<string>('BTC');
  const [loadingCryptos, setLoadingCryptos] = useState(false);

  // Forex state
  const [forexPairs, setForexPairs] = useState<ForexPair[]>([]);
  const [selectedForexPair, setSelectedForexPair] = useState<string>('EURUSD');
  const [loadingForexPairs, setLoadingForexPairs] = useState(false);

  useEffect(() => {
    if (dataSource === 'haver' && databases.length === 0) {
      loadDatabases();
    }
    if (dataSource === 'crypto' && cryptos.length === 0) {
      loadCryptos();
    }
    if (dataSource === 'forex' && forexPairs.length === 0) {
      loadForexPairs();
    }
  }, [dataSource]);

  useEffect(() => {
    if (selectedDatabase) {
      loadSeriesForDatabase(selectedDatabase);
    }
  }, [selectedDatabase]);

  const loadDatabases = async () => {
    setLoadingDatabases(true);
    try {
      const dbs = await fetchHaverDatabases();
      setDatabases(dbs);
    } catch (err) {
      console.error('Failed to load databases:', err);
    } finally {
      setLoadingDatabases(false);
    }
  };

  const loadSeriesForDatabase = async (db: string) => {
    setLoadingSeries(true);
    setSeries([]);
    setSelectedSeries('');
    try {
      const seriesList = await fetchHaverSeries(db);
      setSeries(seriesList);
    } catch (err) {
      console.error('Failed to load series:', err);
    } finally {
      setLoadingSeries(false);
    }
  };

  const loadCryptos = async () => {
    setLoadingCryptos(true);
    try {
      const cryptoList = await fetchPopularCryptos();
      setCryptos(cryptoList);
    } catch (err) {
      console.error('Failed to load cryptos:', err);
    } finally {
      setLoadingCryptos(false);
    }
  };

  const loadForexPairs = async () => {
    setLoadingForexPairs(true);
    try {
      const pairs = await fetchPopularForexPairs();
      setForexPairs(pairs);
    } catch (err) {
      console.error('Failed to load forex pairs:', err);
    } finally {
      setLoadingForexPairs(false);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (dataSource === 'yahoo') {
      if (yahooTicker.trim()) {
        onLoadYahoo(yahooTicker.trim().toUpperCase());
      }
    } else if (dataSource === 'haver') {
      if (selectedDatabase && selectedSeries) {
        onLoadHaver(selectedDatabase, selectedSeries);
      }
    } else if (dataSource === 'crypto') {
      if (selectedCrypto) {
        onLoadCrypto(selectedCrypto);
      }
    } else if (dataSource === 'forex') {
      if (selectedForexPair) {
        onLoadForex(selectedForexPair);
      }
    }
  };

  const filteredSeries = series.filter(
    (s) =>
      s.name.toLowerCase().includes(seriesSearch.toLowerCase()) ||
      s.description.toLowerCase().includes(seriesSearch.toLowerCase())
  );

  return (
    <div className="bg-white rounded-xl p-3 border border-cream-200">
      {/* Compact Source Toggle */}
      <div className="flex gap-1 mb-3 bg-cream-100 p-1 rounded-lg">
        <button
          onClick={() => setDataSource('yahoo')}
          className={`flex-1 py-1.5 px-2 rounded-md text-xs font-medium transition-all ${dataSource === 'yahoo'
              ? 'bg-white text-slate-800 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
            }`}
        >
          Yahoo
        </button>
        <button
          onClick={() => setDataSource('crypto')}
          className={`flex-1 py-1.5 px-2 rounded-md text-xs font-medium transition-all ${dataSource === 'crypto'
              ? 'bg-white text-slate-800 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
            }`}
        >
          Crypto
        </button>
        <button
          onClick={() => setDataSource('forex')}
          className={`flex-1 py-1.5 px-2 rounded-md text-xs font-medium transition-all ${dataSource === 'forex'
              ? 'bg-white text-slate-800 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
            }`}
        >
          Forex
        </button>
        <button
          onClick={() => setDataSource('haver')}
          className={`flex-1 py-1.5 px-2 rounded-md text-xs font-medium transition-all ${dataSource === 'haver'
              ? 'bg-white text-slate-800 shadow-sm'
              : 'text-slate-500 hover:text-slate-700'
            }`}
        >
          Haver
        </button>
      </div>

      <form onSubmit={handleSubmit} className="space-y-2">
        {dataSource === 'yahoo' ? (
          <div className="flex gap-2">
            <input
              type="text"
              value={yahooTicker}
              onChange={(e) => setYahooTicker(e.target.value)}
              placeholder="NVDA, AAPL..."
              className="flex-1 px-3 py-2 bg-cream-50 border border-cream-200 rounded-lg text-sm text-slate-800 placeholder-slate-400 focus:outline-none focus:border-coral-400"
            />
            <button
              type="submit"
              disabled={loading || !yahooTicker.trim()}
              className="px-4 py-2 bg-coral-500 text-white font-medium rounded-lg hover:bg-coral-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                'Load'
              )}
            </button>
          </div>
        ) : dataSource === 'crypto' ? (
          <div className="space-y-2">
            {loadingCryptos ? (
              <div className="flex items-center gap-2 text-slate-500 py-2 text-xs">
                <div className="w-3 h-3 border-2 border-coral-200 border-t-coral-500 rounded-full animate-spin" />
                Loading cryptocurrencies...
              </div>
            ) : (
              <select
                value={selectedCrypto}
                onChange={(e) => setSelectedCrypto(e.target.value)}
                className="w-full px-3 py-2 bg-cream-50 border border-cream-200 rounded-lg text-sm text-slate-800 focus:outline-none focus:border-coral-400"
              >
                {cryptos.map((crypto) => (
                  <option key={crypto.symbol} value={crypto.symbol}>
                    {crypto.symbol} ({crypto.ticker})
                  </option>
                ))}
              </select>
            )}
            <button
              type="submit"
              disabled={loading || !selectedCrypto}
              className="w-full py-2 bg-coral-500 text-white font-medium rounded-lg hover:bg-coral-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
              ) : (
                'Load Data'
              )}
            </button>
          </div>
        ) : dataSource === 'forex' ? (
          <div className="space-y-2">
            {loadingForexPairs ? (
              <div className="flex items-center gap-2 text-slate-500 py-2 text-xs">
                <div className="w-3 h-3 border-2 border-coral-200 border-t-coral-500 rounded-full animate-spin" />
                Loading forex pairs...
              </div>
            ) : (
              <select
                value={selectedForexPair}
                onChange={(e) => setSelectedForexPair(e.target.value)}
                className="w-full px-3 py-2 bg-cream-50 border border-cream-200 rounded-lg text-sm text-slate-800 focus:outline-none focus:border-coral-400"
              >
                {forexPairs.map((pair) => (
                  <option key={pair.pair} value={pair.pair}>
                    {pair.base}/{pair.quote} ({pair.pair})
                  </option>
                ))}
              </select>
            )}
            <button
              type="submit"
              disabled={loading || !selectedForexPair}
              className="w-full py-2 bg-coral-500 text-white font-medium rounded-lg hover:bg-coral-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
            >
              {loading ? (
                <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
              ) : (
                'Load Data'
              )}
            </button>
          </div>
        ) : dataSource === 'haver' ? (
          <div className="space-y-2">
            {loadingDatabases ? (
              <div className="flex items-center gap-2 text-slate-500 py-2 text-xs">
                <div className="w-3 h-3 border-2 border-coral-200 border-t-coral-500 rounded-full animate-spin" />
                Loading databases...
              </div>
            ) : (
              <select
                value={selectedDatabase}
                onChange={(e) => setSelectedDatabase(e.target.value)}
                className="w-full px-3 py-2 bg-cream-50 border border-cream-200 rounded-lg text-sm text-slate-800 focus:outline-none focus:border-coral-400"
              >
                <option value="">Select database...</option>
                {databases.map((db) => (
                  <option key={db.code} value={db.code}>
                    {db.code} - {db.name}
                  </option>
                ))}
              </select>
            )}

            {selectedDatabase && (
              <>
                {loadingSeries ? (
                  <div className="flex items-center gap-2 text-slate-500 py-2 text-xs">
                    <div className="w-3 h-3 border-2 border-coral-200 border-t-coral-500 rounded-full animate-spin" />
                    Loading series...
                  </div>
                ) : (
                  <>
                    <input
                      type="text"
                      value={seriesSearch}
                      onChange={(e) => setSeriesSearch(e.target.value)}
                      placeholder="Search series..."
                      className="w-full px-3 py-1.5 bg-cream-50 border border-cream-200 rounded-lg text-xs text-slate-800 placeholder-slate-400 focus:outline-none focus:border-coral-400"
                    />
                    <div className="max-h-32 overflow-y-auto bg-cream-50 rounded-lg border border-cream-200">
                      {filteredSeries.slice(0, 50).map((s) => (
                        <button
                          key={s.name}
                          type="button"
                          onClick={() => setSelectedSeries(s.name)}
                          className={`w-full text-left px-3 py-1.5 border-b border-cream-100 last:border-b-0 transition-colors text-xs ${selectedSeries === s.name
                              ? 'bg-coral-50 text-coral-600'
                              : 'hover:bg-cream-100 text-slate-700'
                            }`}
                        >
                          <div className="font-mono text-[11px]">{s.name}</div>
                          <div className="text-[10px] text-slate-500 truncate">
                            {s.description}
                          </div>
                        </button>
                      ))}
                    </div>
                  </>
                )}

                <button
                  type="submit"
                  disabled={loading || !selectedDatabase || !selectedSeries}
                  className="w-full py-2 bg-coral-500 text-white font-medium rounded-lg hover:bg-coral-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all text-sm"
                >
                  {loading ? (
                    <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin mx-auto" />
                  ) : (
                    'Load Data'
                  )}
                </button>
              </>
            )}
          </div>
        ) : null}
      </form>
    </div>
  );
}
