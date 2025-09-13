import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import './App.css';

function Auth() {
  const [role, setRole] = useState<string | null>(null);
  const [authCode, setAuthCode] = useState<string>('');
  const [message, setMessage] = useState<string>('');
  const navigate = useNavigate();

  const handleRoleSelection = async (selectedRole: string) => {
    setRole(selectedRole);
    setMessage('Fetching login URL...');
    try {
      const response = await fetch('/api/auth/login_url');
      if (!response.ok) {
        throw new Error('Failed to fetch login URL.');
      }
      const data = await response.json();
      window.open(data.auth_url, '_blank');
      setMessage('Login URL opened in a new tab. Please log in and paste the auth code below.');
    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'An unknown error occurred.');
    }
  };

  const handleTokenSubmit = async () => {
    if (!authCode || !role) {
      setMessage('Please select a role and provide the auth code.');
      return;
    }
    setMessage('Exchanging code for token...');
    try {
      const response = await fetch('/api/auth/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ code: authCode, role }),
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to exchange code for token.');
      }
      const data = await response.json();
      setMessage(data.message || 'Success!');
      setAuthCode('');
      
      // Redirect to the option chain page
      navigate('/option-chain');

    } catch (error) {
      setMessage(error instanceof Error ? error.message : 'An unknown error occurred.');
    }
  };

  return (
    <div className="App-header">
      <h1>Authentication</h1>
      {!role ? (
        <div>
          <h2>Select Your Role:</h2>
          <button onClick={() => handleRoleSelection('Emperor')}>Emperor</button>
          <button onClick={() => handleRoleSelection('King')}>King</button>
        </div>
      ) : (
        <div>
          <h2>Welcome, {role}</h2>
          <p>Paste the authentication code from Upstox below:</p>
          <input
            type="text"
            value={authCode}
            onChange={(e) => setAuthCode(e.target.value)}
            placeholder="Enter Auth Code"
            style={{ padding: '10px', width: '300px' }}
          />
          <button onClick={handleTokenSubmit}>Submit Code</button>
          <button onClick={() => setRole(null)}>Back to Role Selection</button>
        </div>
      )}
      {message && <p style={{ marginTop: '20px' }}>{message}</p>}
    </div>
  );
}

export default Auth;