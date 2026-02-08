import { AlertCircle } from 'lucide-react';

interface Props {
  aiAvailable: boolean;
}

export default function StatusBanner({ aiAvailable }: Props) {
  if (aiAvailable) return null;

  return (
    <div className="bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 flex items-center gap-3 mb-4">
      <AlertCircle className="h-5 w-5 text-amber-600 shrink-0" />
      <div>
        <p className="text-sm font-medium text-amber-800">AI Classification Unavailable</p>
        <p className="text-xs text-amber-600">
          The document was queued for manual classification. A reviewer must classify it manually.
        </p>
      </div>
    </div>
  );
}
