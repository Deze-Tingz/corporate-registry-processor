import { Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../stores/auth';

const ROLE_LEVEL: Record<string, number> = {
  intake_clerk: 0,
  reviewer: 1,
  supervisor: 2,
  administrator: 3,
};

const NAV_ITEMS = [
  { to: '/', label: 'Dashboard', minRole: 0 },
  { to: '/intake', label: 'Intake', minRole: 0 },
  { to: '/review', label: 'Review Queue', minRole: 1 },
  { to: '/audit', label: 'Audit Log', minRole: 2 },
  { to: '/admin', label: 'Admin', minRole: 3 },
];

export default function AppShell({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuthStore();
  const location = useLocation();

  return (
    <div className="min-h-screen bg-slate-50">
      <nav className="bg-white border-b border-slate-200 px-6 py-3 flex items-center justify-between">
        <div className="flex items-center gap-8">
          <h1 className="text-lg font-semibold text-slate-800">CRDP</h1>
          <div className="flex gap-1">
            {NAV_ITEMS.filter((item) => (ROLE_LEVEL[user?.role ?? ''] ?? 0) >= item.minRole).map((item) => (
              <Link
                key={item.to}
                to={item.to}
                className={`px-3 py-1.5 rounded text-sm transition-colors ${
                  location.pathname === item.to
                    ? 'bg-blue-50 text-blue-700 font-medium'
                    : 'text-slate-600 hover:text-slate-800 hover:bg-slate-50'
                }`}
              >
                {item.label}
              </Link>
            ))}
          </div>
        </div>

        <div className="flex items-center gap-4">
          <span className="text-sm text-slate-600">
            {user?.full_name}{' '}
            <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded">
              {user?.role.replace(/_/g, ' ')}
            </span>
          </span>
          <button
            onClick={logout}
            className="text-sm text-red-600 hover:text-red-700"
          >
            Sign out
          </button>
        </div>
      </nav>

      <main className="max-w-7xl mx-auto px-6 py-8">{children}</main>
    </div>
  );
}
