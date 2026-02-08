import { useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import AppShell from '../components/AppShell';
import DocumentViewer from '../components/DocumentViewer';
import ClassificationPanel from '../components/ClassificationPanel';

export default function DocumentDetailPage() {
  const { id } = useParams<{ id: string }>();
  const queryClient = useQueryClient();

  const { data: doc, isLoading: docLoading } = useQuery({
    queryKey: ['document', id],
    queryFn: () => api.get(`/documents/${id}`).then((r) => r.data),
  });

  const { data: classification, isLoading: classLoading } = useQuery({
    queryKey: ['classification', id],
    queryFn: () => api.get(`/classifications/${id}`).then((r) => r.data),
    retry: false,
  });

  const classify = useMutation({
    mutationFn: () =>
      api.post('/classifications', { document_id: id }).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['classification', id] });
      queryClient.invalidateQueries({ queryKey: ['document', id] });
    },
  });

  if (docLoading) {
    return (
      <AppShell>
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-slate-200 rounded w-1/4" />
          <div className="h-96 bg-slate-200 rounded" />
        </div>
      </AppShell>
    );
  }

  if (!doc) {
    return (
      <AppShell>
        <p className="text-slate-500">Document not found.</p>
      </AppShell>
    );
  }

  return (
    <AppShell>
      <div className="flex items-center gap-3 mb-6">
        <h2 className="text-xl font-semibold text-slate-800">{doc.tracking_id}</h2>
        <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded">
          {doc.status.replace(/_/g, ' ')}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left: Document Viewer (3/5) */}
        <div className="lg:col-span-3">
          <DocumentViewer
            extractedText={doc.extracted_text}
            filename={doc.original_filename}
            mimeType={doc.mime_type}
            fileUrl={`/api/documents/${doc.id}/file`}
          />
        </div>

        {/* Right: Classification Panel (2/5) */}
        <div className="lg:col-span-2">
          <ClassificationPanel
            classification={classification ?? null}
            isLoading={classLoading}
            onClassify={() => classify.mutate()}
            isClassifying={classify.isPending}
          />
        </div>
      </div>
    </AppShell>
  );
}
