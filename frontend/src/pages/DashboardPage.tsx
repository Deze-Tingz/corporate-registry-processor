import { useQuery } from '@tanstack/react-query';
import api from '../lib/api';
import AppShell from '../components/AppShell';

export default function DashboardPage() {
  const { data: docs } = useQuery({
    queryKey: ['documents', 'stats'],
    queryFn: () => api.get('/documents?limit=1').then((r) => r.data),
  });

  const total = docs?.total ?? '--';

  return (
    <AppShell>
      <h2 className="text-xl font-semibold text-slate-800 mb-6">Dashboard</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <p className="text-sm text-slate-500">Total Documents</p>
          <p className="text-3xl font-bold text-slate-800 mt-2">{total}</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <p className="text-sm text-slate-500">Awaiting Review</p>
          <p className="text-3xl font-bold text-slate-800 mt-2">--</p>
        </div>
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6">
          <p className="text-sm text-slate-500">Processed Today</p>
          <p className="text-3xl font-bold text-slate-800 mt-2">--</p>
        </div>
      </div>

      <p className="text-sm text-slate-400 mt-8">
        More statistics will be available after Phase 3 (AI classification).
      </p>
    </AppShell>
  );
}
