import React from 'react';

const Home = ({ activeTrains, metadata }) => {
  return (
    <div className="page-content glass-panel" style={{ margin: '2rem', padding: '2rem', height: 'calc(100vh - 4rem)', overflowY: 'auto' }}>
      <h1>ARTEMIS Dashboard</h1>
      <p style={{ color: '#bae6fd', fontSize: '1.2rem', marginBottom: '2rem' }}>
        Advanced Railway Timetable Emulator & Machine Intelligence Simulator
      </p>
      
      <div style={{ display: 'flex', gap: '2rem', flexWrap: 'wrap' }}>
        <div className="stat-card" style={{ background: 'rgba(255,255,255,0.05)', padding: '1.5rem', borderRadius: '12px', minWidth: '250px' }}>
          <h3 style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>Total Trains in System</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#38bdf8' }}>
            {metadata ? metadata.length : 0}
          </div>
        </div>
        
        <div className="stat-card" style={{ background: 'rgba(255,255,255,0.05)', padding: '1.5rem', borderRadius: '12px', minWidth: '250px' }}>
          <h3 style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>Active Trains Moving</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#10b981' }}>
            {activeTrains.filter(t => t.speed > 0).length}
          </div>
        </div>
        
        <div className="stat-card" style={{ background: 'rgba(255,255,255,0.05)', padding: '1.5rem', borderRadius: '12px', minWidth: '250px' }}>
          <h3 style={{ color: '#94a3b8', margin: '0 0 0.5rem 0' }}>Trains Stopped</h3>
          <div style={{ fontSize: '2.5rem', fontWeight: 'bold', color: '#f59e0b' }}>
            {activeTrains.filter(t => t.speed === 0).length}
          </div>
        </div>
      </div>
      
      <div style={{ marginTop: '3rem' }}>
        <h2>Welcome to the Next-Gen Dispatcher</h2>
        <p style={{ color: '#f1f5f9', lineHeight: 1.6, maxWidth: '800px' }}>
          This dashboard provides a live, AI-driven overview of the Swiss Railway Network. 
          Use the navigation bar above to explore the interactive map, view the comprehensive dataset, 
          and learn more about the reinforcement learning algorithms powering the simulation.
        </p>
      </div>
    </div>
  );
};

export default Home;
