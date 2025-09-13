import React, { useState, useEffect, useRef, useCallback } from 'react';

const OptionChain = () => {
  const [expiryDate, setExpiryDate] = useState(() => localStorage.getItem('optionChainExpiryDate') || '');
  const [data, setData] = useState<any>(() => {
    const savedData = localStorage.getItem('optionChainData');
    return savedData ? JSON.parse(savedData) : null;
  });
  const [isFetching, setIsFetching] = useState(() => localStorage.getItem('optionChainIsFetching') === 'true');
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    const role = 'Emperor';
    const instrument_key = 'NSE_INDEX|Nifty 50';

    try {
      await fetch(`/api/option_chain/fetch2`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          role,
          instrument_key,
          expiry_date: expiryDate,
        }),
      });

      const encodedInstrumentKey = encodeURIComponent(instrument_key);
      const response = await fetch(
        `/api/option_chain?instrument_key=${encodedInstrumentKey}&expiry_date=${expiryDate}`
      );
      const fetchedData = await response.json();
      setData(fetchedData);
    } catch (error) {
      console.error('Error fetching option chain data:', error);
    }
  }, [expiryDate]);

  const startFetching = () => {
    if (isFetching) return;
    setIsFetching(true);
  };

  const stopFetching = () => {
    if (!isFetching || !intervalRef.current) return;
    setIsFetching(false);
    clearInterval(intervalRef.current);
    intervalRef.current = null;
  };

  const clearData = () => {
    setData(null);
  };

  useEffect(() => {
    localStorage.setItem('optionChainExpiryDate', expiryDate);
  }, [expiryDate]);

  useEffect(() => {
    localStorage.setItem('optionChainData', JSON.stringify(data));
  }, [data]);

  useEffect(() => {
    localStorage.setItem('optionChainIsFetching', isFetching.toString());
  }, [isFetching]);

  useEffect(() => {
    if (isFetching) {
      // Fetch immediately when starting
      fetchData();
      // Start interval
      intervalRef.current = setInterval(fetchData, 10000);
    } else {
      // Stop interval when not fetching
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isFetching, fetchData]);

  return (
    <div style={{
      minHeight: '88%',
      width:'100%',
      backgroundColor: '#dcdcdc',
      padding: '0',
      fontFamily: 'Arial, sans-serif',
      display: 'flex',
    }}>
      <div style={{
        maxWidth: '100%',
        width: '100%',
        backgroundColor: 'white',
        borderRadius: '12px',
        boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
        overflow: 'hidden',
        display: 'flex',
        flexDirection: 'column',
      }}>
        {/* Header */}
        <div style={{ textAlign: 'center', marginBottom: '20px' }}>
          <h1 style={{ margin: 0, fontSize: '2.5em', fontWeight: 'bold' }}>Option Chain</h1>
          <p style={{ margin: '8px 0 0 0', fontSize: '1.2em', color: '#242526ff' }}>Real-time Option Chain Analytics</p>
        </div>

        {/* Controls */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: '15px',
          marginBottom: '20px',
          flexWrap: 'wrap',
        }}>
          <label htmlFor="expiry-date" style={{ fontWeight: '500' }}>Expiry Date:</label>
          <input
            type="date"
            id="expiry-date"
            value={expiryDate}
            onChange={(e) => setExpiryDate(e.target.value)}
            style={{
              padding: '6px 10px',
              fontSize: '1em',
              borderRadius: '6px',
              border: '1px solid #ced4da',
              outline: 'none',
              minWidth: '160px',
            }}
          />
          <button
            onClick={startFetching}
            disabled={isFetching || !expiryDate}
            style={{
              backgroundColor: '#2a2b2cff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 16px',
              cursor: isFetching || !expiryDate ? 'not-allowed' : 'pointer',
              opacity: isFetching || !expiryDate ? 0.6 : 1,
              transition: 'background-color 0.3s ease',
            }}
            onMouseEnter={e => { if (!(isFetching || !expiryDate)) e.currentTarget.style.backgroundColor = '#2a2b2cff'; }}
            onMouseLeave={e => { if (!(isFetching || !expiryDate)) e.currentTarget.style.backgroundColor = '#2a2b2cff'; }}
          >
            Fetch Data
          </button>
          <button
            onClick={stopFetching}
            disabled={!isFetching}
            style={{
              backgroundColor: '#2a2b2cff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 16px',
              cursor: !isFetching ? 'not-allowed' : 'pointer',
              opacity: !isFetching ? 0.6 : 1,
              transition: 'background-color 0.3s ease',
            }}
            onMouseEnter={e => { if (!!isFetching) e.currentTarget.style.backgroundColor = '#2a2b2cff'; }}
            onMouseLeave={e => { if (!!isFetching) e.currentTarget.style.backgroundColor = '#2a2b2cff'; }}
          >
            Stop Fetch
          </button>
          <button
            onClick={clearData}
            style={{
              backgroundColor: '#2a2b2cff',
              color: 'white',
              border: 'none',
              borderRadius: '6px',
              padding: '8px 16px',
              cursor: 'pointer',
              transition: 'background-color 0.3s ease',
            }}
            onMouseEnter={e => e.currentTarget.style.backgroundColor = '#2a2b2cff'}
            onMouseLeave={e => e.currentTarget.style.backgroundColor = '#2a2b2cff'}
          >
            Clear Data
          </button>
        </div>

        {/* Data Table */}
        {data && (
          <div style={{
            flex: 1,
            width: '100%',
            overflowY: 'auto',
            overflowX: 'auto',
            border: '1px solid #dee2e6',
            borderRadius: '8px',
            maxHeight: '60vh',
          }}>
            <table
              style={{
                width: '100%',
                borderCollapse: 'collapse',
                minWidth: '1200px',
                fontFamily: 'Arial, sans-serif',
                fontSize: '12px',
              }}
            >
              <thead>
                <tr style={{ backgroundColor: '#e9ecef' }}>
                  {/* Call Side Headers */}
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>OI</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Volume</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>IV</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>LTP</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Bid Price</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Bid Qty</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Ask Price</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Ask Qty</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Delta</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Gamma</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Theta</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Vega</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>POP</th>
                  {/* Center */}
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Strike Price</th>
                  {/* Put Side Headers (Mirrored) */}
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>POP</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Vega</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Theta</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Gamma</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Delta</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Ask Qty</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Ask Price</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Bid Qty</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Bid Price</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>LTP</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>IV</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>Volume</th>
                  <th style={{ padding: '6px', border: '1px solid #dee2e6' }}>OI</th>
                </tr>
              </thead>
              <tbody>
                {data.data.map((item: any, index: number) => {
                  const call = item.call_options;
                  const put = item.put_options;
                  return (
                    <tr key={index} style={{ borderBottom: '1px solid #dee2e6' }}>
                      {/* Call Side Data */}
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{call.market_data.oi}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{call.market_data.volume}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{call.option_greeks.iv}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{call.market_data.ltp}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{call.market_data.bid_price}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{call.market_data.bid_qty}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{call.market_data.ask_price}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{call.market_data.ask_qty}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{call.option_greeks.delta}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{call.option_greeks.gamma}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{call.option_greeks.theta}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{call.option_greeks.vega}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{call.option_greeks.pop}</td>
                      {/* Center */}
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{item.strike_price}</td>
                      {/* Put Side Data (Mirrored) */}
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{put.option_greeks.pop}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{put.option_greeks.vega}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{put.option_greeks.theta}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{put.option_greeks.gamma}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{put.option_greeks.delta}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{put.market_data.ask_qty}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{put.market_data.ask_price}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{put.market_data.bid_qty}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{put.market_data.bid_price}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{put.market_data.ltp}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{put.option_greeks.iv}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{put.market_data.volume}</td>
                      <td style={{ padding: '6px', border: '1px solid #dee2e6' }}>{put.market_data.oi}</td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
        </div>
    </div>
  );
};

export default OptionChain;
