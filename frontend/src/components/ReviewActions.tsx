import { useState } from 'react';
import { CheckCircle, Edit3, ArrowUpCircle } from 'lucide-react';

interface Props {
  onApprove: () => void;
  onCorrect: (reason: string) => void;
  onEscalate: (reason: string) => void;
  isSubmitting: boolean;
  hasEdits: boolean;
}

export default function ReviewActions({ onApprove, onCorrect, onEscalate, isSubmitting, hasEdits }: Props) {
  const [mode, setMode] = useState<'idle' | 'correct' | 'escalate'>('idle');
  const [reason, setReason] = useState('');

  if (mode === 'correct') {
    return (
      <div className="space-y-3">
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Reason for correction..."
          className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[80px]"
        />
        <div className="flex gap-2">
          <button
            onClick={() => { onCorrect(reason); setMode('idle'); setReason(''); }}
            disabled={!reason.trim() || isSubmitting}
            className="flex-1 bg-amber-600 text-white px-4 py-2 rounded-md text-sm hover:bg-amber-700 disabled:opacity-50 transition-colors"
          >
            Submit Correction
          </button>
          <button
            onClick={() => { setMode('idle'); setReason(''); }}
            className="px-4 py-2 rounded-md text-sm border border-slate-300 hover:bg-slate-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  if (mode === 'escalate') {
    return (
      <div className="space-y-3">
        <textarea
          value={reason}
          onChange={(e) => setReason(e.target.value)}
          placeholder="Reason for escalation..."
          className="w-full px-3 py-2 border border-slate-300 rounded-md text-sm focus:outline-none focus:ring-2 focus:ring-blue-500 min-h-[80px]"
        />
        <div className="flex gap-2">
          <button
            onClick={() => { onEscalate(reason); setMode('idle'); setReason(''); }}
            disabled={!reason.trim() || isSubmitting}
            className="flex-1 bg-red-600 text-white px-4 py-2 rounded-md text-sm hover:bg-red-700 disabled:opacity-50 transition-colors"
          >
            Escalate to Supervisor
          </button>
          <button
            onClick={() => { setMode('idle'); setReason(''); }}
            className="px-4 py-2 rounded-md text-sm border border-slate-300 hover:bg-slate-50 transition-colors"
          >
            Cancel
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="flex gap-2">
      <button
        onClick={onApprove}
        disabled={isSubmitting}
        className="flex-1 flex items-center justify-center gap-2 bg-green-600 text-white px-4 py-2 rounded-md text-sm hover:bg-green-700 disabled:opacity-50 transition-colors"
      >
        <CheckCircle className="h-4 w-4" />
        Approve
      </button>
      <button
        onClick={() => setMode('correct')}
        disabled={isSubmitting}
        className="flex-1 flex items-center justify-center gap-2 bg-amber-600 text-white px-4 py-2 rounded-md text-sm hover:bg-amber-700 disabled:opacity-50 transition-colors"
      >
        <Edit3 className="h-4 w-4" />
        {hasEdits ? 'Correct' : 'Edit & Correct'}
      </button>
      <button
        onClick={() => setMode('escalate')}
        disabled={isSubmitting}
        className="flex-1 flex items-center justify-center gap-2 bg-red-600 text-white px-4 py-2 rounded-md text-sm hover:bg-red-700 disabled:opacity-50 transition-colors"
      >
        <ArrowUpCircle className="h-4 w-4" />
        Escalate
      </button>
    </div>
  );
}
