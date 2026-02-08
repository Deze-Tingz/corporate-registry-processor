import { Brain, Clock, FileText } from 'lucide-react';
import ConfidenceBadge from './ConfidenceBadge';
import StatusBanner from './StatusBanner';

interface Classification {
  id: string;
  document_type: string;
  confidence_score: number;
  reasoning: string;
  extracted_fields: Record<string, string | string[] | null>;
  limitations: string | null;
  model_version: string;
  prompt_version: string;
  ai_available: boolean;
  processing_time_ms: number | null;
  created_at: string;
}

interface Props {
  classification: Classification | null;
  isLoading: boolean;
  onClassify?: () => void;
  isClassifying?: boolean;
}

const TYPE_LABELS: Record<string, string> = {
  articles_of_incorporation: 'Articles of Incorporation',
  amendment: 'Amendment',
  annual_return: 'Annual Return',
  registered_agent_change: 'Registered Agent Change',
  dissolution_notice: 'Dissolution Notice',
  other: 'Other / Unclassified',
};

export default function ClassificationPanel({ classification, isLoading, onClassify, isClassifying }: Props) {
  if (isLoading) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-slate-200 rounded w-1/3" />
          <div className="h-4 bg-slate-200 rounded w-2/3" />
          <div className="h-4 bg-slate-200 rounded w-1/2" />
        </div>
      </div>
    );
  }

  if (!classification) {
    return (
      <div className="bg-white rounded-lg border border-slate-200 p-6 text-center">
        <Brain className="mx-auto h-8 w-8 text-slate-300 mb-3" />
        <p className="text-sm text-slate-500 mb-4">Not yet classified</p>
        {onClassify && (
          <button
            onClick={onClassify}
            disabled={isClassifying}
            className="bg-blue-600 text-white px-4 py-2 rounded-md text-sm hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {isClassifying ? 'Classifying...' : 'Run AI Classification'}
          </button>
        )}
      </div>
    );
  }

  const c = classification;

  return (
    <div className="space-y-4">
      <StatusBanner aiAvailable={c.ai_available} />

      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
            <Brain className="h-4 w-4" />
            AI Classification
          </h3>
          <ConfidenceBadge score={c.confidence_score} />
        </div>

        <div className="space-y-3">
          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wide">Document Type</p>
            <p className="text-sm font-medium text-slate-800 flex items-center gap-2 mt-0.5">
              <FileText className="h-4 w-4 text-slate-400" />
              {TYPE_LABELS[c.document_type] || c.document_type}
            </p>
          </div>

          <div>
            <p className="text-xs text-slate-500 uppercase tracking-wide">Reasoning</p>
            <p className="text-sm text-slate-700 mt-0.5">{c.reasoning}</p>
          </div>

          {c.limitations && (
            <div>
              <p className="text-xs text-slate-500 uppercase tracking-wide">Limitations</p>
              <p className="text-sm text-amber-700 mt-0.5">{c.limitations}</p>
            </div>
          )}
        </div>
      </div>

      {/* Extracted Fields */}
      <div className="bg-white rounded-lg border border-slate-200 p-6">
        <h3 className="text-sm font-semibold text-slate-800 mb-3">Extracted Fields</h3>
        <dl className="space-y-2">
          {Object.entries(c.extracted_fields).map(([key, value]) => (
            <div key={key} className="flex justify-between text-sm">
              <dt className="text-slate-500">{key.replace(/_/g, ' ')}</dt>
              <dd className="text-slate-800 font-medium text-right max-w-[60%]">
                {value === null ? (
                  <span className="text-slate-300">--</span>
                ) : Array.isArray(value) ? (
                  value.join(', ')
                ) : (
                  String(value)
                )}
              </dd>
            </div>
          ))}
        </dl>
      </div>

      {/* Metadata */}
      <div className="text-xs text-slate-400 flex items-center gap-4">
        <span>Model: {c.model_version}</span>
        <span>Prompt: v{c.prompt_version}</span>
        {c.processing_time_ms && (
          <span className="flex items-center gap-1">
            <Clock className="h-3 w-3" />
            {c.processing_time_ms}ms
          </span>
        )}
      </div>
    </div>
  );
}
