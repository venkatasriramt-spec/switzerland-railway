import React, { useState } from 'react';
import { Map, AdvancedMarker, Pin, InfoWindow } from '@vis.gl/react-google-maps';

const ArtemisMap = ({ trains, metadata }) => {
  const [hoveredTrain, setHoveredTrain] = useState(null);

  // Center roughly over Switzerland
  const defaultCenter = { lat: 46.8182, lng: 8.2275 };

  return (
    <div style={{ width: '100%', height: '100%' }}>
      <Map
        defaultZoom={8}
        defaultCenter={defaultCenter}
        mapId="DEMO_MAP_ID"
        disableDefaultUI={true}
        gestureHandling={'greedy'}
        internalUsageAttributionIds={["gmp_git_agentskills_v1"]}
      >
        {trains.map((train) => (
          <AdvancedMarker
            key={train.id}
            position={{ lat: train.lat, lng: train.lon }}
            onMouseEnter={() => setHoveredTrain(train)}
            onMouseLeave={() => setHoveredTrain(null)}
          >
            <Pin
              background={train.speed > 0 ? '#10b981' : '#f59e0b'}
              borderColor={train.speed > 0 ? '#047857' : '#b45309'}
              glyphColor={'#ffffff'}
              scale={0.8}
            />
          </AdvancedMarker>
        ))}

        {hoveredTrain && (
          <InfoWindow
            position={{ lat: hoveredTrain.lat, lng: hoveredTrain.lon }}
            onCloseClick={() => setHoveredTrain(null)}
            options={{ pixelOffset: new window.google.maps.Size(0, -30) }}
          >
            <div style={{ color: '#1e293b', padding: '8px', minWidth: '150px' }}>
              {(() => {
                const meta = metadata?.find(m => m.trip_id === hoveredTrain.trip_id);
                return (
                  <>
                    <h3 style={{ margin: '0 0 8px 0', fontSize: '1rem', borderBottom: '1px solid #cbd5e1', paddingBottom: '4px' }}>
                      {meta ? `${meta.route_short_name} (${meta.trip_headsign})` : 'Unknown Route'}
                    </h3>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '8px', fontSize: '0.85rem' }}>
                      <div><strong>Train No:</strong></div>
                      <div>{hoveredTrain.id}</div>
                      <div><strong>Speed:</strong></div>
                      <div>{hoveredTrain.speed.toFixed(1)} m/s</div>
                      <div><strong>Delay:</strong></div>
                      <div>{hoveredTrain.delay.toFixed(1)} s</div>
                    </div>
                  </>
                );
              })()}
            </div>
          </InfoWindow>
        )}
      </Map>
    </div>
  );
};

export default ArtemisMap;
