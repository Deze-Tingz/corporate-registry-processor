import { useState } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import api from '../lib/api';
import AppShell from '../components/AppShell';
import DocumentViewer from '../components/DocumentViewer';
import ClassificationPanel from '../components/ClassificationPanel';
import AiDisclosure from '../components/AiDisclosure';
import FieldEditor from '../components/FieldEditor';
import ReviewActions from '../components/ReviewActions';

export default function ReviewDetailPage() {
  const { id } = useParams<{ id: string }>();
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [editedFields, setEditedFields] = useState<Record<string, string>>({});
  const [correctedType, setCorrectedType] = useState<string>('');

  const { data: doc } = useQuery({
    queryKey: ['document', id],
    queryFn: () => api.get(`/documents/${id}`).then((r) => r.data),
  });

  const { data: classification, isLoading: classLoading } = useQuery({
    queryKey: ['classification', id],
    queryFn: () => api.get(`/classifications/${id}`).then((r) => r.data),
    retry: false,
  });

  const submitReview = useMutation({
    mutationFn: (body: Record<string, unknown>) =>
      api.post('/reviews', body).then((r) => r.data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['review-queue'] });
      queryClient.invalidateQueries({ queryKey: ['document', id] });
      navigate('/review');
    },
  });

  const hasEdits = Object.keys(editedFields).length > 0 || correctedType !== '';

  const handleApprove = () => {
    if (!classification) return;
    submitReview.mutate({
      document_id: id,
      classification_id: classification.id,
      decision: 'approved',
    });
  };

  const handleCorrect = (reason: string) => {
    if (!classification) return;
    submitReview.mutate({
      document_id: id,
      classification_id: classification.id,
      decision: 'corrected',
      corrected_document_type: correctedType || null,
      corrected_fields: Object.keys(editedFields).length ? editedFields : null,
      correction_reason: reason,
    });
  };

  const handleEscalate = (reason: string) => {
    if (!classification) return;
    submitReview.mutate({
      document_id: id,
      classification_id: classification.id,
      decision: 'escalated',
      escalation_reason: reason,
    });
  };

  if (!doc) {
    return (
      <AppShell>
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-slate-200 rounded w-1/4" />
          <div className="h-96 bg-slate-200 rounded" />
        </div>
      </AppShell>
    );
  }

  const DOCTYPE_OPTIONS = [
    'articles_of_incorporation',
    'amendment',
    'annual_return',
    'registered_agent_change',
    'dissolution_notice',
    'other',
  ];

  return (
    <AppShell>
      <div className="flex items-center gap-3 mb-6">
        <button
          onClick={() => navigate('/review')}
          className="text-sm text-blue-600 hover:text-blue-700"
        >
          &larr; Queue
        </button>
        <h2 className="text-xl font-semibold text-slate-800">{doc.tracking_id}</h2>
        <span className="text-xs bg-slate-100 text-slate-500 px-2 py-0.5 rounded">
          {doc.status.replace(/_/g, ' ')}
        </span>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-5 gap-6">
        {/* Left: Document Viewer */}
        <div className="lg:col-span-3">
          <DocumentViewer
            extractedText={doc.extracted_text}
            filename={doc.original_filename}
            mimeType={doc.mime_type}
            fileUrl={`/api/documents/${doc.id}/file`}
          />
        </div>

        {/* Right: Review Panel */}
        <div className="lg:col-span-2 space-y-4">
          <AiDisclosure />

          <ClassificationPanel
            classification={classification ?? null}
            isLoading={classLoading}
          />

          {classification && (
            <>
              {/* Document type correction */}
              <div className="bg-white rounded-lg border border-slate-200 p-4">
                <label className="block text-xs text-slate-500 mb-1">
                  Document Type (correct if needed)
                </label>
                <select
                  value={correctedType || classification.document_type}
                  onChange={(e) => setCorrectedType(e.target.value)}
                  className="w-full px-3 py-1.5 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  {DOCTYPE_OPTIONS.map((t) => (
                    <option key={t} value={t}>
                      {t.replace(/_/g, ' ')}
                    </option>
                  ))}
                </select>
              </div>

              {/* Field editor */}
              <div className="bg-white rounded-lg border border-slate-200 p-4">
                <h4 className="text-sm font-medium text-slate-800 mb-3">
                  Extracted Fields
                </h4>
                <FieldEditor
                  fields={classification.extracted_fields}
                  editedFields={editedFields}
                  onChange={(k, v) =>
                    setEditedFields((prev) => ({ ...prev, [k]: v }))
                  }
                />
              </div>

              {/* Review actions */}
              <div className="bg-white rounded-lg border border-slate-200 p-4">
                <ReviewActions
                  onApprove={handleApprove}
                  onCorrect={handleCorrect}
                  onEscalate={handleEscalate}
                  isSubmitting={submitReview.isPending}
                  hasEdits={hasEdits}
                />
              </div>
            </>
          )}
        </div>
      </div>
    </AppShell>
  );
}
