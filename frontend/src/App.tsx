import { Navigate, Route, Routes } from 'react-router-dom'
import type { ReactNode } from 'react'
import { AppShell } from './components/layout/AppShell'
import { AuthProvider, useAuth } from './hooks/useAuth'
import { DiscoverPage } from './pages/DiscoverPage'
import { EvolutionPage } from './pages/EvolutionPage'
import { HomePage } from './pages/HomePage'
import { LandingPage } from './pages/LandingPage'
import { NetworkPage } from './pages/NetworkPage'
import { PatternsPage } from './pages/PatternsPage'
import { RecommendationsPage } from './pages/RecommendationsPage'
import { SettingsPage } from './pages/SettingsPage'
import { TastePage } from './pages/TastePage'

function Guard({ children }: { children: ReactNode }) {
  const { loading, me } = useAuth()
  if (loading) {
    return (
      <div className="min-h-screen bg-paper flex items-center justify-center text-muted">
        Opening your library…
      </div>
    )
  }
  if (!me?.authenticated) return <LandingPage />
  return <>{children}</>
}

function AppRoutes() {
  return (
    <Routes>
      <Route
        element={
          <Guard>
            <AppShell />
          </Guard>
        }
      >
        <Route path="/" element={<HomePage />} />
        <Route path="/evolution" element={<EvolutionPage />} />
        <Route path="/network" element={<NetworkPage />} />
        <Route path="/patterns" element={<PatternsPage />} />
        <Route path="/taste" element={<TastePage />} />
        <Route path="/discover" element={<DiscoverPage />} />
        <Route path="/recommendations" element={<RecommendationsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

export default function App() {
  return (
    <AuthProvider>
      <AppRoutes />
    </AuthProvider>
  )
}
