import { NavLink, Outlet } from 'react-router-dom'
import { useAuth } from '../../hooks/useAuth'

const links = [
  { to: '/', label: 'Home', caption: 'Decoded' },
  { to: '/evolution', label: 'Evolution', caption: 'Over time' },
  { to: '/network', label: 'Network', caption: 'Connections' },
  { to: '/patterns', label: 'Patterns', caption: 'When' },
  { to: '/taste', label: 'Taste', caption: 'Profile' },
  { to: '/discover', label: 'Discover', caption: 'Bridge' },
  { to: '/recommendations', label: 'Revisit', caption: 'Return to' },
  { to: '/settings', label: 'Settings', caption: 'Data' },
]

export function AppShell() {
  const { me } = useAuth()
  const demo = me?.user?.is_demo

  return (
    <div className="min-h-screen bg-paper text-ink">
      <nav className="md:hidden sticky top-0 z-20 bg-paper/90 backdrop-blur px-5 pt-4 pb-2 flex items-end justify-between">
        <div>
          <p className="text-[10px] tracking-[0.18em] uppercase text-muted">Listening graph</p>
        </div>
        <div className="flex gap-4 text-[12px]">
          <NavLink to="/discover" className={({ isActive }) => (isActive ? 'text-accent' : 'text-muted')}>
            Discover
          </NavLink>
          <NavLink to="/settings" className={({ isActive }) => (isActive ? 'text-accent' : 'text-muted')}>
            Settings
          </NavLink>
        </div>
      </nav>
      <header className="hidden md:flex items-end justify-between px-10 lg:px-16 pt-8 pb-4">
        <div>
          <p className="text-[11px] tracking-[0.22em] uppercase text-muted">Personal listening graph</p>
          <h1 className="font-medium text-[22px] tracking-tight mt-1">Listening, decoded</h1>
        </div>
        <nav className="flex gap-6 text-[13px]">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `pb-1 border-b ${isActive ? 'border-accent text-ink' : 'border-transparent text-muted hover:text-ink'}`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </header>
      {demo ? (
        <div className="mx-6 md:mx-10 lg:mx-16 mb-2 rounded-full bg-[#ece4f5] text-[#5c5270] text-[12px] px-4 py-2">
          You are viewing a labeled synthetic demo library — not a live Spotify history.
        </div>
      ) : null}
      <main className="px-5 md:px-10 lg:px-16 pb-24 md:pb-16 pt-4">
        <Outlet />
      </main>
      <nav className="md:hidden fixed bottom-0 inset-x-0 bg-card/95 backdrop-blur border-t border-line px-2 py-2 grid grid-cols-5 text-[10px] text-center z-20">
        {links.slice(0, 5).map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `py-2 rounded-xl ${isActive ? 'text-accent' : 'text-muted'}`
            }
          >
            <div className="font-medium">{link.label}</div>
          </NavLink>
        ))}
      </nav>
    </div>
  )
}
