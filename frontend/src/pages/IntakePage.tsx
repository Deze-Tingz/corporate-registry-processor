import { useCallback, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { Upload, FileText, CheckCircle, AlertCircle } from 'lucide-react';
import api from '../lib/api';
import AppShell from '../components/AppShell';

interface DocumentItem {
  id: string;
  tracking_id: string;
  original_filename: string;
  file_size_bytes: number;
  mime_type: string;
  status: string;
  created_at: string;
}

export default function IntakePage() {
  const [dragOver, setDragOver] = useState(false);
  const queryClient = useQueryClient();
  const navigate = useNavigate();

  const { data } = useQuery({
    queryKey: ['documents', 'recent'],
    queryFn: () => api.get('/documents?limit=10').then((r) => r.data),
  });

  const upload = useMutation({
    mutationFn: async (file: File) => {
      const form = new FormData();
      form.append('file', file);
      return api.post('/documents', form).then((r) => r.data);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['documents'] });
    },
  });

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setDragOver(false);
      const files = Array.from(e.dataTransfer.files);
      files.forEach((file) => upload.mutate(file));
    },
    [upload]
  );

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = Array.from(e.target.files || []);
    files.forEach((file) => upload.mutate(file));
    e.target.value = '';
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1048576) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / 1048576).toFixed(1)} MB`;
  };

  const statusBadge = (s: string) => {
    const colors: Record<string, string> = {
      pending_classification: 'bg-yellow-100 text-yellow-700',
      classified: 'bg-blue-100 text-blue-700',
      under_review: 'bg-purple-100 text-purple-700',
      approved: 'bg-green-100 text-green-700',
      corrected: 'bg-teal-100 text-teal-700',
      escalated: 'bg-red-100 text-red-700',
    };
    return (
      <span className={`text-xs px-2 py-0.5 rounded ${colors[s] || 'bg-slate-100 text-slate-600'}`}>
        {s.replace(/_/g, ' ')}
      </span>
    );
  };

  return (
    <AppShell>
      <h2 className="text-xl font-semibold text-slate-800 mb-6">Document Intake</h2>

      {/* Upload zone */}
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        className={`border-2 border-dashed rounded-lg p-12 text-center transition-colors ${
          dragOver ? 'border-blue-500 bg-blue-50' : 'border-slate-300 bg-white'
        }`}
      >
        <Upload className="mx-auto h-10 w-10 text-slate-400 mb-3" />
        <p className="text-slate-600 mb-2">
          Drag and drop files here, or{' '}
          <label className="text-blue-600 hover:text-blue-700 cursor-pointer underline">
            browse
            <input type="file" className="hidden" accept=".pdf,.png,.jpg,.jpeg,.tiff,.tif" multiple onChange={handleFileSelect} />
          </label>
        </p>
        <p className="text-xs text-slate-400">PDF, PNG, JPEG, TIFF — up to 50 MB</p>
      </div>

      {upload.isPending && (
        <div className="mt-4 flex items-center gap-2 text-sm text-blue-600">
          <div className="h-4 w-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
          Uploading...
        </div>
      )}

      {upload.isError && (
        <div className="mt-4 flex items-center gap-2 text-sm text-red-600">
          <AlertCircle className="h-4 w-4" />
          Upload failed: {(upload.error as Error).message}
        </div>
      )}

      {upload.isSuccess && (
        <div className="mt-4 flex items-center gap-2 text-sm text-green-600">
          <CheckCircle className="h-4 w-4" />
          Uploaded successfully — {upload.data.tracking_id}
        </div>
      )}

      {/* Recent documents */}
      <h3 className="text-lg font-medium text-slate-800 mt-10 mb-4">Recent Documents</h3>

      {data?.items?.length ? (
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 overflow-hidden">
          <table className="w-full text-sm">
            <thead className="bg-slate-50 text-slate-600">
              <tr>
                <th className="text-left px-4 py-3 font-medium">Tracking ID</th>
                <th className="text-left px-4 py-3 font-medium">Filename</th>
                <th className="text-left px-4 py-3 font-medium">Size</th>
                <th className="text-left px-4 py-3 font-medium">Status</th>
                <th className="text-left px-4 py-3 font-medium">Uploaded</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data.items.map((doc: DocumentItem) => (
                <tr key={doc.id} className="hover:bg-slate-50 cursor-pointer" onClick={() => navigate(`/documents/${doc.id}`)}>
                  <td className="px-4 py-3 font-mono text-xs">{doc.tracking_id}</td>
                  <td className="px-4 py-3 flex items-center gap-2">
                    <FileText className="h-4 w-4 text-slate-400" />
                    {doc.original_filename}
                  </td>
                  <td className="px-4 py-3 text-slate-500">{formatSize(doc.file_size_bytes)}</td>
                  <td className="px-4 py-3">{statusBadge(doc.status)}</td>
                  <td className="px-4 py-3 text-slate-500">
                    {new Date(doc.created_at).toLocaleDateString()}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      ) : (
        <p className="text-sm text-slate-400">No documents uploaded yet.</p>
      )}
    </AppShell>
  );
}
