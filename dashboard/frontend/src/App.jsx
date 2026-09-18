import React, { useState, useEffect } from 'react';
import { APIProvider } from '@vis.gl/react-google-maps';
import ArtemisMap from './components/Map';
import TrainTable from './components/TrainTable';
import './index.css';

const API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

function App() {
  const [trains, setTrains] = useState([]);
  const [metadata, setMetadata] = useState([]);
  const [currentTime, setCurrentTime] = useState(0);
  const [isConnected, setIsConnected] = useState(false);
  const [isRegistryOpen, setIsRegistryOpen] = useState(false);

  useEffect(() => {
    // Fetch static metadata
    fetch('http://localhost:8000/api/trains/metadata')
      .then(res => res.json())
      .then(data => {
        if (data.metadata) setMetadata(data.metadata);
      })
      .catch(err => console.error("Failed to fetch metadata:", err));

    // Connect to FastAPI WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws/simulation');
    
    ws.onopen = () => {
      console.log('Connected to simulation server');
      setIsConnected(true);
    };
    
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setCurrentTime(data.time);
      setTrains(data.trains);
    };
    
    ws.onclose = () => {
      console.log('Disconnected from simulation server');
      setIsConnected(false);
    };
    
    return () => {
      ws.close();
    };
  }, []);

  // Calculate some basic metrics
  const activeTrains = trains.filter(t => t.speed > 0).length;
  const avgSpeed = trains.length > 0 
    ? (trains.reduce((sum, t) => sum + t.speed, 0) / trains.length).toFixed(1) 
    : 0;
  
  // Format simulated time (sim starts at 0, max 86400s)
  const formatTime = (seconds) => {
    const h = Math.floor(seconds / 3600).toString().padStart(2, '0');
    const m = Math.floor((seconds % 3600) / 60).toString().padStart(2, '0');
    const s = Math.floor(seconds % 60).toString().padStart(2, '0');
    return `${h}:${m}:${s}`;
  };

  return (
    <APIProvider apiKey={API_KEY}>
      <div className="dashboard-container">
        
        {/* Left Sidebar */}
        <div className="sidebar glass-panel">
          <h1>ARTEMIS Dashboard</h1>
          <div className="status-badge">
            <span className={`indicator ${isConnected ? 'live' : 'offline'}`}></span>
            {isConnected ? 'LIVE SIMULATION' : 'OFFLINE'}
          </div>
          
          <div className="metrics-grid">
            <div className="metric-card">
              <span className="label">Sim Time</span>
              <span className="value">{formatTime(currentTime)}</span>
            </div>
            <div className="metric-card">
              <span className="label">Active Trains</span>
              <span className="value">{activeTrains} / {trains.length}</span>
            </div>
            <div className="metric-card">
              <span className="label">Avg Speed</span>
              <span className="value">{avgSpeed} m/s</span>
            </div>
          </div>
          
          <div className="info-panel">
            <h3>AI Dispatcher</h3>
            <p>The PPO reinforcement learning agent is currently controlling all {metadata.length > 0 ? metadata.length : 5643} trains on the Swiss Railway Network, scheduling them to prevent collisions and minimize delays.</p>
            <button className="btn-primary" onClick={() => setIsRegistryOpen(!isRegistryOpen)}>
              {isRegistryOpen ? 'Hide Train Registry' : 'View Train Registry'}
            </button>
          </div>
        </div>

        {/* Main Map View */}
        <div className="map-container">
          <ArtemisMap trains={trains} />
          {isRegistryOpen && (
            <TrainTable 
              metadata={metadata} 
              activeTrains={trains} 
              onClose={() => setIsRegistryOpen(false)} 
            />
          )}
        </div>
        
      </div>
    </APIProvider>
  );
}

export default App;
