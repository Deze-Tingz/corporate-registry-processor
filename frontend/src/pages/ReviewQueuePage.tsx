import { useNavigate } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { FileText } from 'lucide-react';
import api from '../lib/api';
import AppShell from '../components/AppShell';
import ConfidenceBadge from '../components/ConfidenceBadge';

interface QueueItem {
  document_id: string;
  tracking_id: string;
  original_filename: string;
  document_type: string;
  confidence_score: number;
  ai_available: boolean;
  status: string;
  created_at: string;
}

const TYPE_LABELS: Record<string, string> = {
  articles_of_incorporation: 'Articles of Incorp.',
  amendment: 'Amendment',
  annual_return: 'Annual Return',
  registered_agent_change: 'Agent Change',
  dissolution_notice: 'Dissolution',
  other: 'Other',
};

export default function ReviewQueuePage() {
  const navigate = useNavigate();

  const { data, isLoading } = useQuery({
    queryKey: ['review-queue'],
    queryFn: () => api.get('/reviews/queue').then((r) => r.data),
    refetchInterval: 15000,
  });

  return (
    <AppShell>
      <div className="flex items-center justify-between mb-6">
        <h2 className="text-xl font-semibold text-slate-800">Review Queue</h2>
        {data && (
          <span className="text-sm text-slate-500">{data.total} document(s) pending</span>
        )}
      </div>

      {isLoading ? (
        <div className="space-y-3">
          {[1, 2, 3].map((i) => (
            <div key={i} className="h-16 bg-slate-200 rounded animate-pulse" />
          ))}
        </div>
      ) : data?.items?.length ? (
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Tracking ID</th>
                <th className="text-left px-4 py-3 font-medium">Filename</th>
                <th className="text-left px-4 py-3 font-medium">Type</th>
                <th className="text-left px-4 py-3 font-medium">Confidence</th>
                <th className="text-left px-4 py-3 font-medium">Status</th>
                <th className="text-left px-4 py-3 font-medium">Received</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((item: QueueItem) => (
                <tr
                  key={item.document_id}
                  className="hover:bg-slate-50 cursor-pointer"
                  onClick={() => navigate(`/review/${item.document_id}`)}
                >
                  <td className="px-4 py-3 font-mono text-xs">{item.tracking_id}</td>
                  <td className="px-4 py-3 flex items-center gap-2">
                    <FileText className="h-4 w-4 text-slate-400" />
                    {item.original_filename}
                  </td>
                  <td className="px-4 py-3 text-slate-700">
                    {TYPE_LABELS[item.document_type] || item.document_type}
                  </td>
                  <td className="px-4 py-3">
                    <ConfidenceBadge score={item.confidence_score} />
                  </td>
                  <td className="px-4 py-3">
                    <span className={`text-xs px-2 py-0.5 rounded ${
                      item.status === 'escalated'
                        ? 'bg-red-100 text-red-700'
                        : 'bg-blue-100 text-blue-700'
                    }`}>
                      {item.status.replace(/_/g, ' ')}
                    </span>
                  </td>
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(item.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <div className="bg-white rounded-lg border border-slate-200 p-12 text-center">
          <FileText className="mx-auto h-10 w-10 text-slate-300 mb-3" />
          <p className="text-slate-500">No documents awaiting review.</p>
        </div>
      )}
    </AppShell>
  );
}
