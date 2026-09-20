import React from 'react';

const About = () => {
  return (
    <div className="page-content glass-panel" style={{ margin: '2rem', padding: '2rem', height: 'calc(100vh - 4rem)', overflowY: 'auto' }}>
      <h1>About ARTEMIS</h1>
      <p style={{ color: '#bae6fd', fontSize: '1.1rem', marginBottom: '2rem' }}>
        Powered by Stable Baselines3 and PPO
      </p>
      
      <div style={{ color: '#f1f5f9', lineHeight: 1.8, maxWidth: '800px' }}>
        <h2>The Challenge</h2>
        <p>
          Managing a massive railway network like the Swiss Federal Railways (SBB) involves coordinating thousands of trains simultaneously.
          Traditional dispatching algorithms struggle to adapt in real-time to cascading delays and unexpected network contention.
        </p>
        
        <h2>The AI Solution</h2>
        <p>
          ARTEMIS uses a Proximal Policy Optimization (PPO) reinforcement learning agent. The agent observes the current positions, speeds, 
          and delays of all trains across the network. By interacting with our custom Gymnasium environment, the agent learns to issue 
          continuous acceleration and braking commands to minimize network-wide delays while strictly avoiding collisions.
        </p>
        
        <h2>Technology Stack</h2>
        <ul>
          <li><strong>Backend:</strong> Python, FastAPI, Gymnasium, Stable Baselines3, Pandas</li>
          <li><strong>Frontend:</strong> React, Vite, React Router, Google Maps Platform (@vis.gl/react-google-maps)</li>
        </ul>
      </div>
    </div>
  );
};

export default About;
