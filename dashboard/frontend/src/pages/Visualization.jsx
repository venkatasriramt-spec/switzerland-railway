import React from 'react';
import ArtemisMap from '../components/Map';

const Visualization = ({ trains, metadata }) => {
  return (
    <div className="visualization-page" style={{ position: 'relative', width: '100%', height: 'calc(100vh - 60px)' }}>
      {/* Simulation Info Overlay */}
      <div className="overlay-panel" style={{ position: 'absolute', top: '20px', left: '20px', zIndex: 10, width: '300px' }}>
        <div className="glass-panel" style={{ padding: '20px', borderRadius: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', marginBottom: '16px' }}>
            <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981', marginRight: '8px', boxShadow: '0 0 8px #10b981' }}></div>
            <span style={{ fontSize: '0.75rem', fontWeight: 'bold', letterSpacing: '1px', color: '#10b981' }}>LIVE SIMULATION</span>
          </div>
          
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px', marginBottom: '20px' }}>
            <div className="stat-box" style={{ background: 'rgba(0,0,0,0.4)', padding: '12px', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.65rem', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>Active Trains</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#f8fafc' }}>
                {trains.length} <span style={{ fontSize: '0.9rem', color: '#64748b' }}>/ {metadata ? metadata.length : 5643}</span>
              </div>
            </div>
            
            <div className="stat-box" style={{ background: 'rgba(0,0,0,0.4)', padding: '12px', borderRadius: '8px' }}>
              <div style={{ fontSize: '0.65rem', color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>Avg Speed</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 'bold', color: '#f8fafc' }}>
                {trains.length > 0 
                  ? (trains.reduce((acc, t) => acc + t.speed, 0) / trains.length).toFixed(1)
                  : "0.0"} <span style={{ fontSize: '0.9rem', color: '#64748b' }}>m/s</span>
              </div>
            </div>
          </div>
          
          <div style={{ background: 'rgba(0,0,0,0.4)', padding: '12px', borderRadius: '8px' }}>
            <h3 style={{ margin: '0 0 8px 0', fontSize: '0.9rem', color: '#e2e8f0' }}>Map Legend</h3>
            <div style={{ display: 'flex', alignItems: 'center', marginBottom: '4px', fontSize: '0.8rem', color: '#94a3b8' }}>
              <span className="status-dot moving" style={{ marginRight: '8px' }}></span> Train Moving
            </div>
            <div style={{ display: 'flex', alignItems: 'center', fontSize: '0.8rem', color: '#94a3b8' }}>
              <span className="status-dot stopped" style={{ marginRight: '8px' }}></span> Train Stopped
            </div>
            <div style={{ marginTop: '12px', fontSize: '0.75rem', color: '#64748b', fontStyle: 'italic' }}>
              Hover over any train marker to see details.
            </div>
          </div>
        </div>
      </div>
      
      {/* Map */}
      <ArtemisMap trains={trains} metadata={metadata} />
    </div>
  );
};

export default Visualization;
