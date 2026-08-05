export async function fetchTelemetry() {
  const response = await fetch('/api/telemetry')
  return response.json()
}
