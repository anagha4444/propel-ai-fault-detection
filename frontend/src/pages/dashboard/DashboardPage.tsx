import { MapContainer, Marker, Popup, TileLayer } from 'react-leaflet'

const telemetry = [
  { id: 1, device_id: 'dev-001', pole_id: 1, event_type: 'heartbeat' },
  { id: 2, device_id: 'dev-002', pole_id: 2, event_type: 'power_lost' },
]

export function DashboardPage() {
  return (
    <div style={{ padding: 24, display: 'grid', gap: 16 }}>
      <h1>Propel Fault Dashboard</h1>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, minmax(0,1fr))', gap: 12 }}>
        <StatCard label="Active Incidents" value="3" />
        <StatCard label="Open Tickets" value="5" />
        <StatCard label="Online Devices" value="97%" />
        <StatCard label="Telemetry Rate" value="1.2s" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: 16 }}>
        <div style={{ height: 420, borderRadius: 12, overflow: 'hidden' }}>
          <MapContainer center={[40.7128, -74.006]} zoom={12} style={{ height: '100%', width: '100%' }}>
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" />
            <Marker position={[40.7128, -74.006]}>
              <Popup>Primary outage cluster</Popup>
            </Marker>
          </MapContainer>
        </div>
        <div>
          <h3>Incident List</h3>
          <ul>
            <li>Span fault on Pole 14</li>
            <li>Feeder fault on Feeder 2</li>
            <li>Device failure on Pole 9</li>
          </ul>
          <h3>Telemetry Monitor</h3>
          <ul>
            {telemetry.map((item) => (
              <li key={item.id}>{item.device_id} - {item.event_type}</li>
            ))}
          </ul>
        </div>
      </div>

      <div>
        <h3>Simulator Controls</h3>
        <button>Span Fault</button>
        <button>DT Fault</button>
        <button>Feeder Fault</button>
        <button>Repair</button>
      </div>
    </div>
  )
}

function StatCard({ label, value }: { label: string; value: string }) {
  return (
    <div style={{ background: '#1e293b', padding: 16, borderRadius: 12 }}>
      <div style={{ color: '#94a3b8' }}>{label}</div>
      <div style={{ fontSize: 24, fontWeight: 700 }}>{value}</div>
    </div>
  )
}
