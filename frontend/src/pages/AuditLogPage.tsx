import { useState } from 'react';
import { useMutation, useQuery } from '@tanstack/react-query';
import { CheckCircle, Download, XCircle, Shield } from 'lucide-react';
import api from '../lib/api';
import AppShell from '../components/AppShell';

interface AuditEntry {
  id: number;
  timestamp: string;
  user_id: string | null;
  action: string;
  resource_type: string;
  resource_id: string | null;
  details: Record<string, unknown>;
  entry_hash: string;
}

export default function AuditLogPage() {
  const [actionFilter, setActionFilter] = useState('');
  const [resourceFilter, setResourceFilter] = useState('');

  const params = new URLSearchParams();
  if (actionFilter) params.set('action', actionFilter);
  if (resourceFilter) params.set('resource_type', resourceFilter);

  const { data, isLoading } = useQuery({
    queryKey: ['audit', actionFilter, resourceFilter],
    queryFn: () => api.get(`/audit?${params.toString()}`).then((r) => r.data),
  });

  const verify = useMutation({
    mutationFn: () => api.get('/audit/verify').then((r) => r.data),
  });

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-slate-800">Audit Log</h2>
        <div className="flex gap-2">
          <button
            onClick={() => verify.mutate()}
            disabled={verify.isPending}
            className="flex items-center gap-2 px-3 py-1.5 text-sm border border-slate-300 rounded-md hover:bg-slate-50 transition-colors disabled:opacity-50"
          >
            <Shield className="h-4 w-4" />
            {verify.isPending ? 'Verifying...' : 'Verify Chain'}
          </button>
          <a
            href="/api/audit/export/csv"
            className="flex items-center gap-2 px-3 py-1.5 text-sm border border-slate-300 rounded-md hover:bg-slate-50 transition-colors"
          >
            <Download className="h-4 w-4" />
            CSV
          </a>
          <a
            href="/api/audit/export/json"
            className="flex items-center gap-2 px-3 py-1.5 text-sm border border-slate-300 rounded-md hover:bg-slate-50 transition-colors"
          >
            <Download className="h-4 w-4" />
            JSON
          </a>
        </div>
      </div>

      {verify.isSuccess && (
        <div className={`mb-4 px-4 py-3 rounded-lg flex items-center gap-3 ${
          verify.data.valid
            ? 'bg-green-50 border border-green-200'
            : 'bg-red-50 border border-red-200'
        }`}>
          {verify.data.valid ? (
            <>
              <CheckCircle className="h-5 w-5 text-green-600" />
              <span className="text-sm text-green-700">
                Chain verified — {verify.data.checked} entries, all valid.
              </span>
            </>
          ) : (
            <>
              <XCircle className="h-5 w-5 text-red-600" />
              <span className="text-sm text-red-700">
                Chain broken at entry #{verify.data.broken_at}. Tamper detected.
              </span>
            </>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="flex gap-3 mb-4">
        <input
          type="text"
          placeholder="Filter by action..."
          value={actionFilter}
          onChange={(e) => setActionFilter(e.target.value)}
          className="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        <input
          type="text"
          placeholder="Filter by resource type..."
          value={resourceFilter}
          onChange={(e) => setResourceFilter(e.target.value)}
          className="px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        />
        {data && (
          <span className="text-sm text-slate-500 self-center">{data.total} entries</span>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-2">
          {[1, 2, 3, 4, 5].map((i) => (
            <div key={i} className="h-12 bg-slate-200 rounded animate-pulse" />
          ))}
        </div>
      ) : data?.items?.length ? (
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="text-left px-4 py-3 font-medium w-12">#</th>
                <th className="text-left px-4 py-3 font-medium">Timestamp</th>
                <th className="text-left px-4 py-3 font-medium">Action</th>
                <th className="text-left px-4 py-3 font-medium">Resource</th>
                <th className="text-left px-4 py-3 font-medium">Details</th>
                <th className="text-left px-4 py-3 font-medium">Hash</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((entry: AuditEntry) => (
                <tr key={entry.id} className="hover:bg-slate-50">
                  <td className="px-4 py-3 text-slate-400 text-xs">{entry.id}</td>
                  <td className="px-4 py-3 text-xs">
                    {new Date(entry.timestamp).toLocaleString()}
                  </td>
                  <td className="px-4 py-3">
                    <span className="text-xs bg-slate-100 px-2 py-0.5 rounded font-mono">
                      {entry.action}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-600">
                    {entry.resource_type}
                    {entry.resource_id && (
                      <span className="text-slate-400 ml-1">
                        {entry.resource_id.slice(0, 8)}...
                      </span>
                    )}
                  </td>
                  <td className="px-4 py-3 text-xs text-slate-500 max-w-[200px] truncate">
                    {JSON.stringify(entry.details)}
                  </td>
                  <td className="px-4 py-3 font-mono text-xs text-slate-400">
                    {entry.entry_hash.slice(0, 12)}...
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-sm text-slate-400">No audit entries found.</p>
      )}
    </AppShell>
  );
}
