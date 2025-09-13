import React from 'react';
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import Auth from './Auth';
import OptionChain from './OptionChain';
import MetricsPage from './MetricsPage';
import './App.css';

function App() {
  return (
    <Router>
      <div className="App">
        <nav>
          <ul>
            <li>
              <Link to="/">Authentication</Link>
            </li>
            <li>
              <Link to="/option-chain">Option Chain</Link>
            </li>
            <li>
              <Link to="/metrics">Metrics</Link>
            </li>
          </ul>
        </nav>
        <main>
          <Routes>
            <Route path="/" element={<Auth />} />
            <Route path="/option-chain" element={<OptionChain />} />
            <Route path="/metrics" element={<MetricsPage />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
