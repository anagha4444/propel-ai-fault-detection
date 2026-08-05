import { create } from 'zustand'

interface DashboardState {
  incidents: number
  tickets: number
  telemetryRate: string
}

export const useDashboardStore = create<DashboardState>(() => ({
  incidents: 3,
  tickets: 5,
  telemetryRate: '1.2s',
}))
