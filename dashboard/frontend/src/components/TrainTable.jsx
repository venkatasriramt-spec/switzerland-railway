import React, { useState } from 'react';

const TrainTable = ({ metadata, activeTrains, onClose }) => {
  const [searchTerm, setSearchTerm] = useState("");

  if (!metadata || metadata.length === 0) {
    return (
      <div className="registry-panel glass-panel">
        <div className="panel-header">
          <h2>Train Registry</h2>
          <button onClick={onClose} className="close-btn">&times;</button>
        </div>
        <div className="panel-body">
          <p>Loading metadata...</p>
        </div>
      </div>
    );
  }

  // Filter trains based on search term
  const filteredTrains = metadata.filter(train => {
    const term = searchTerm.toLowerCase();
    return (
      train.trip_id.toLowerCase().includes(term) ||
      train.route_short_name.toLowerCase().includes(term) ||
      train.trip_headsign.toLowerCase().includes(term)
    );
  });

  return (
    <div className="registry-panel glass-panel">
      <div className="panel-header">
        <h2>Train Registry</h2>
        <button onClick={onClose} className="close-btn">&times;</button>
      </div>
      
      <div className="panel-search">
        <input 
          type="text" 
          placeholder="Search by ID, Route, or Destination..." 
          value={searchTerm}
          onChange={(e) => setSearchTerm(e.target.value)}
          className="search-input"
        />
      </div>

      <div className="panel-body table-container">
        <table className="train-table">
          <thead>
            <tr>
              <th>Status</th>
              <th>Route</th>
              <th>Destination</th>
              <th>Carriages</th>
              <th>Max Speed (km/h)</th>
            </tr>
          </thead>
          <tbody>
            {filteredTrains.map(train => {
              // Check if train is currently active in the simulation
              const activeInfo = activeTrains.find(t => t.trip_id === train.trip_id);
              const isMoving = activeInfo && activeInfo.speed > 0;
              const isStopped = activeInfo && activeInfo.speed === 0;

              return (
                <tr key={train.trip_id}>
                  <td>
                    {activeInfo ? (
                      <span className={`status-dot ${isMoving ? 'moving' : 'stopped'}`} title={isMoving ? 'Moving' : 'Stopped'}></span>
                    ) : (
                      <span className="status-dot inactive" title="Not Dispatched"></span>
                    )}
                  </td>
                  <td><strong>{train.route_short_name}</strong></td>
                  <td>{train.trip_headsign}</td>
                  <td>{train.carriages}</td>
                  <td>{train.max_speed_kmh}</td>
                </tr>
              );
            })}
            {filteredTrains.length === 0 && (
              <tr>
                <td colSpan="5" className="no-results">No trains match your search.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TrainTable;
