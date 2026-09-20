import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom';
import { APIProvider } from '@vis.gl/react-google-maps';

import Home from './pages/Home';
import About from './pages/About';
import Visualization from './pages/Visualization';
import TrainData from './pages/TrainData';

import './index.css';

const API_KEY = import.meta.env.VITE_GOOGLE_MAPS_API_KEY;

// A simple navigation bar component
const NavBar = () => {
  const location = useLocation();
  const path = location.pathname;

  return (
    <nav className="navbar glass-panel">
      <div className="nav-brand">ARTEMIS Dashboard</div>
      <div className="nav-links">
        <Link to="/" className={`nav-link ${path === '/' ? 'active' : ''}`}>Home</Link>
        <Link to="/about" className={`nav-link ${path === '/about' ? 'active' : ''}`}>About</Link>
        <Link to="/visualization" className={`nav-link ${path === '/visualization' ? 'active' : ''}`}>Visualization</Link>
        <Link to="/data" className={`nav-link ${path === '/data' ? 'active' : ''}`}>Train Data</Link>
      </div>
    </nav>
  );
};

function App() {
  const [trains, setTrains] = useState([]);
  const [metadata, setMetadata] = useState([]);

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
      console.log('Connected to simulation stream');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.trains) {
          setTrains(data.trains);
        }
      } catch (err) {
        console.error('Error parsing WebSocket message', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket Error:', error);
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <APIProvider apiKey={API_KEY}>
      <BrowserRouter>
        <div className="app-container">
          <NavBar />
          <div className="main-content">
            <Routes>
              <Route path="/" element={<Home activeTrains={trains} metadata={metadata} />} />
              <Route path="/about" element={<About />} />
              <Route path="/visualization" element={<Visualization trains={trains} metadata={metadata} />} />
              <Route path="/data" element={<TrainData activeTrains={trains} metadata={metadata} />} />
            </Routes>
          </div>
        </div>
      </BrowserRouter>
    </APIProvider>
  );
}

export default App;
