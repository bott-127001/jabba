import React, { useEffect, useState } from 'react';

interface MetricsData {
  current_price: number;
  totals: any;
  difference: any;
  difference_percent: any;
  bid_ask_imbalance: any;
  bid_ask_spread: any;
}

const MetricsPage = () => {
  const [metrics, setMetrics] = useState<MetricsData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [expiryDate, setExpiryDate] = React.useState(() => localStorage.getItem('optionChainExpiryDate') || '');

  const fetchMetrics = async () => {
    setLoading(true);
    setError(null);
    try {
      console.log("Fetching metrics with instrument_key: NSE_INDEX|Nifty 50, expiry_date:", expiryDate);
      // Replace with actual API endpoint and parameters
      const response = await fetch('/api/metrics/calculate_metrics', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          instrument_key: 'NSE_INDEX|Nifty 50',
          expiry_date: expiryDate,
        }),
      });
      if (!response.ok) {
        throw new Error(`Error fetching metrics: ${response.statusText}`);
      }
      const data = await response.json();
      console.log("Metrics data received:", data);
      if (data && Object.keys(data).length > 0 && data.current_price !== undefined) {
        setMetrics(data);
      } else {
        setMetrics(null);
        setError('No valid metrics data received');
      }
    } catch (err: any) {
      setError(err.message || 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    localStorage.setItem('metricsExpiryDate', expiryDate);
  }, [expiryDate]);

  React.useEffect(() => {
    if (expiryDate) {
      fetchMetrics();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [expiryDate]);

  if (loading) return <div>Loading metrics...</div>;
  if (error) return <div>Error: {error}</div>;

  // Prepare default empty metrics structure with zeros or placeholders
  const emptyMetrics = {
    current_price: 0,
    totals: { call: {}, put: {} },
    difference: { call: {}, put: {} },
    difference_percent: { call: {}, put: {} },
    bid_ask_imbalance: { call: 0, put: 0 },
    bid_ask_spread: { call: { bid_avg: 0, ask_avg: 0 }, put: { bid_avg: 0, ask_avg: 0 } },
  };

  const metricsToRender = metrics || emptyMetrics;

  const renderTable = (title: string, data: any) => {
    // Always render table structure, fill with '-' if data missing
    const callData = data && data.call ? data.call : {};
    const putData = data && data.put ? data.put : {};
    const keys = new Set([...Object.keys(callData), ...Object.keys(putData)]);
    return (
      <div style={{
        backgroundColor: '#f8f9fa',
        borderRadius: '12px',
        padding: '12px',
        boxShadow: '0 2px 10px rgba(0,0,0,0.1)'
      }}>
        <h3 style={{
          textAlign: 'center',
          marginBottom: '12px',
          color: '#495057',
          fontSize: '1.2em'
        }}>{title}</h3>
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ backgroundColor: '#e9ecef' }}>
              <th style={{ padding: '6px', border: '1px solid #dee2e6', fontWeight: 'bold' }}>Metric</th>
              <th style={{ padding: '6px', border: '1px solid #dee2e6', fontWeight: 'bold' }}>Call Side</th>
              <th style={{ padding: '6px', border: '1px solid #dee2e6', fontWeight: 'bold' }}>Put Side</th>
            </tr>
          </thead>
          <tbody>
            {[...keys].map((key, index) => (
              <tr key={key} style={index % 2 === 0 ? {} : { backgroundColor: '#f8f9fa' }}>
                <td style={{ padding: '6px', border: '1px solid #dee2e6', textAlign: 'center' }}>{key}</td>
                <td style={{ padding: '6px', border: '1px solid #dee2e6', textAlign: 'center', fontWeight: 'bold' }}>
                  {callData[key] !== undefined ? callData[key] : '-'}
                </td>
                <td style={{ padding: '6px', border: '1px solid #dee2e6', textAlign: 'center', fontWeight: 'bold' }}>
                  {putData[key] !== undefined ? putData[key] : '-'}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    );
  };

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: 'white',
      padding: '0',
      fontFamily: 'Arial, sans-serif'
    }}>
      <div style={{
        backgroundColor: '#e9ecef',
        minHeight: '100vh',
        padding: '0',
      }}>
        <div style={{
          maxWidth: '100%',
          margin: '0 auto',
          backgroundColor: 'white',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0,0,0,0.1)',
          overflow: 'hidden'
        }}>
        {/* Header */}
        <div style={{
          backgroundColor: '#303132ff',
          color: 'white',
          padding: '30px',
          textAlign: 'center'
        }}>
          <h1 style={{ margin: '0', fontSize: '2.5em', fontWeight: 'bold' }}>Nifty 50 Metrics Dashboard</h1>
          <p style={{ margin: '10px 0 0 0', fontSize: '1.2em', opacity: 0.9 }}>Real-time Option Chain Analytics</p>
        </div>

        {/* Current Price Card */}
        <div style={{
          padding: '30px',
          textAlign: 'center',
          backgroundColor: '#e9ecef'
        }}>
          <div style={{
            display: 'inline-block',
            padding: '15px 25px',
            backgroundColor: '#303132ff',
            color: 'white',
            borderRadius: '15px',
            boxShadow: '0 4px 15px rgba(0,0,0,0.2)',
            fontSize: '22px',
            fontWeight: 'bold'
          }}>
            Current Nifty 50 Price: ₹{metricsToRender.current_price.toLocaleString()}
          </div>
        </div>

        {/* Metrics Grid */}
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(3, 1fr)',
          gap: '20px',
          padding: '10px',
          backgroundColor: '#e9ecef'
        }}>
          {renderTable('Totals', metricsToRender.totals)}
          {renderTable('Difference', metricsToRender.difference)}
          {renderTable('Difference %', metricsToRender.difference_percent)}
          <div style={{
            backgroundColor: '#f8f9fa',
            borderRadius: '12px',
            padding: '12px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            color: '#212529'
          }}>
            <h3 style={{
              textAlign: 'center',
              marginBottom: '12px',
              fontSize: '1.2em',
              color: '#212529'
            }}>Bid-Ask Imbalance</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', color: '#212529', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: '#e9ecef' }}>
                <th style={{ padding: '6px', border: '1px solid #ced4da', fontWeight: 'bold' }}>Side</th>
                <th style={{ padding: '6px', border: '1px solid #ced4da', fontWeight: 'bold' }}>Value</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ padding: '6px', border: '1px solid #ced4da', textAlign: 'center' }}>Call</td>
                <td style={{ padding: '6px', border: '1px solid #ced4da', textAlign: 'center', fontWeight: 'bold' }}>
                  {metricsToRender.bid_ask_imbalance.call.toFixed(4)}
                </td>
              </tr>
              <tr style={{ backgroundColor: '#f8f9fa' }}>
                <td style={{ padding: '6px', border: '1px solid #ced4da', textAlign: 'center' }}>Put</td>
                <td style={{ padding: '6px', border: '1px solid #ced4da', textAlign: 'center', fontWeight: 'bold' }}>
                  {metricsToRender.bid_ask_imbalance.put.toFixed(4)}
                </td>
              </tr>
            </tbody>
            </table>
          </div>
          <div style={{
            backgroundColor: '#f8f9fa',
            borderRadius: '12px',
            padding: '12px',
            boxShadow: '0 2px 10px rgba(0,0,0,0.1)',
            color: '#212529'
          }}>
            <h3 style={{
              textAlign: 'center',
              marginBottom: '12px',
              fontSize: '1.2em',
              color: '#212529'
            }}>Bid-Ask Spread</h3>
            <table style={{ width: '100%', borderCollapse: 'collapse', color: '#212529', fontSize: '14px' }}>
            <thead>
              <tr style={{ backgroundColor: '#e9ecef' }}>
                <th style={{ padding: '6px', border: '1px solid #ced4da', fontWeight: 'bold' }}>Side</th>
                <th style={{ padding: '6px', border: '1px solid #ced4da', fontWeight: 'bold' }}>Bid Avg</th>
                <th style={{ padding: '6px', border: '1px solid #ced4da', fontWeight: 'bold' }}>Ask Avg</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td style={{ padding: '6px', border: '1px solid #ced4da', textAlign: 'center' }}>Call</td>
                <td style={{ padding: '6px', border: '1px solid #ced4da', textAlign: 'center', fontWeight: 'bold' }}>
                  {metricsToRender.bid_ask_spread.call.bid_avg.toFixed(4)}
                </td>
                <td style={{ padding: '6px', border: '1px solid #ced4da', textAlign: 'center', fontWeight: 'bold' }}>
                  {metricsToRender.bid_ask_spread.call.ask_avg.toFixed(4)}
                </td>
              </tr>
              <tr style={{ backgroundColor: '#f8f9fa' }}>
                <td style={{ padding: '6px', border: '1px solid #ced4da', textAlign: 'center' }}>Put</td>
                <td style={{ padding: '6px', border: '1px solid #ced4da', textAlign: 'center', fontWeight: 'bold' }}>
                  {metricsToRender.bid_ask_spread.put.bid_avg.toFixed(4)}
                </td>
                <td style={{ padding: '6px', border: '1px solid #ced4da', textAlign: 'center', fontWeight: 'bold' }}>
                  {metricsToRender.bid_ask_spread.put.ask_avg.toFixed(4)}
                </td>
              </tr>
            </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
    </div>
  );
};

export default MetricsPage;
