import React, { useState } from 'react';

const TrainData = ({ metadata, activeTrains }) => {
  const [searchTerm, setSearchTerm] = useState("");

  if (!metadata || metadata.length === 0) {
    return (
      <div className="page-content glass-panel" style={{ margin: '2rem', padding: '2rem', height: 'calc(100vh - 4rem)' }}>
        <p>Loading dataset...</p>
      </div>
    );
  }

  // Filter trains based on search term
  const filteredTrains = metadata.filter(train => {
    const term = searchTerm.toLowerCase();
    return (
      train.trip_id?.toLowerCase().includes(term) ||
      train.route_short_name?.toLowerCase().includes(term) ||
      train.trip_headsign?.toLowerCase().includes(term) ||
      train.stop_name?.toLowerCase().includes(term)
    );
  });

  return (
    <div className="page-content glass-panel" style={{ margin: '2rem', padding: '2rem', height: 'calc(100vh - 4rem)', display: 'flex', flexDirection: 'column' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h1 style={{ margin: 0 }}>Train Master Dataset</h1>
        <div style={{ width: '300px' }}>
          <input 
            type="text" 
            placeholder="Search dataset..." 
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="search-input"
            style={{ width: '100%', padding: '10px 16px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.2)', background: 'rgba(0,0,0,0.3)', color: 'white' }}
          />
        </div>
      </div>

      <div style={{ flexGrow: 1, overflow: 'auto', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.1)' }}>
        <table className="train-table" style={{ width: '100%', borderCollapse: 'collapse', whiteSpace: 'nowrap' }}>
          <thead>
            <tr>
              <th style={{ position: 'sticky', top: 0, left: 0, zIndex: 2, background: 'rgba(30, 41, 59, 1)' }}>Status</th>
              <th style={{ position: 'sticky', top: 0 }}>Trip ID</th>
              <th style={{ position: 'sticky', top: 0 }}>Route</th>
              <th style={{ position: 'sticky', top: 0 }}>Destination</th>
              <th style={{ position: 'sticky', top: 0 }}>Start Station</th>
              <th style={{ position: 'sticky', top: 0 }}>Start Lat</th>
              <th style={{ position: 'sticky', top: 0 }}>Start Lon</th>
              <th style={{ position: 'sticky', top: 0 }}>Dep. Time</th>
              <th style={{ position: 'sticky', top: 0 }}>Weight (t)</th>
              <th style={{ position: 'sticky', top: 0 }}>Carriages</th>
              <th style={{ position: 'sticky', top: 0 }}>Max Speed (km/h)</th>
              <th style={{ position: 'sticky', top: 0 }}>Power</th>
              <th style={{ position: 'sticky', top: 0 }}>Gauge</th>
              <th style={{ position: 'sticky', top: 0 }}>Weekdays</th>
            </tr>
          </thead>
          <tbody>
            {filteredTrains.map(train => {
              const activeInfo = activeTrains.find(t => t.trip_id === train.trip_id);
              const isMoving = activeInfo && activeInfo.speed > 0;

              return (
                <tr key={train.trip_id} className="table-row">
                  <td style={{ position: 'sticky', left: 0, background: 'rgba(15, 23, 42, 0.95)', borderRight: '1px solid rgba(255,255,255,0.1)' }}>
                    {activeInfo ? (
                      <span className={`status-dot ${isMoving ? 'moving' : 'stopped'}`} title={isMoving ? 'Moving' : 'Stopped'}></span>
                    ) : (
                      <span className="status-dot inactive" title="Not Dispatched"></span>
                    )}
                  </td>
                  <td>{train.trip_id}</td>
                  <td><strong>{train.route_short_name}</strong></td>
                  <td>{train.trip_headsign}</td>
                  <td>{train.stop_name}</td>
                  <td>{train.stop_lat}</td>
                  <td>{train.stop_lon}</td>
                  <td>{train.departure_time}</td>
                  <td>{train.weight_tons}</td>
                  <td>{train.carriages}</td>
                  <td>{train.max_speed_kmh}</td>
                  <td>{train.power_supply}</td>
                  <td>{train.gauge}</td>
                  <td>{train.weekdays}</td>
                </tr>
              );
            })}
            {filteredTrains.length === 0 && (
              <tr>
                <td colSpan="14" style={{ textAlign: 'center', padding: '2rem' }}>No trains match your search.</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TrainData;
