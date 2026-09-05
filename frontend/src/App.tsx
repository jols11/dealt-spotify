import { AuthProvider } from './hooks/useAuth'
import { TablePage } from './pages/TablePage'

export default function App() {
  return (
    <AuthProvider>
      <TablePage />
    </AuthProvider>
  )
}
