import React from 'react';
import { Map, AdvancedMarker, Pin } from '@vis.gl/react-google-maps';

const ArtemisMap = ({ trains }) => {
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
            title={`Train ${train.id} - Trip: ${train.trip_id} | Speed: ${train.speed.toFixed(1)}m/s | Delay: ${train.delay.toFixed(1)}s`}
          >
            <Pin
              background={train.speed > 0 ? '#10b981' : '#f59e0b'}
              borderColor={train.speed > 0 ? '#047857' : '#b45309'}
              glyphColor={'#ffffff'}
              scale={0.8}
            />
          </AdvancedMarker>
        ))}
      </Map>
    </div>
  );
};

export default ArtemisMap;
