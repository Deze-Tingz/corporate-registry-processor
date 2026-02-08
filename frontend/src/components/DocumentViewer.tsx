import { FileText } from 'lucide-react';

interface Props {
  extractedText: string | null;
  filename: string;
  mimeType: string;
  fileUrl: string;
}

export default function DocumentViewer({ extractedText, filename, mimeType, fileUrl }: Props) {
  return (
    <div className="bg-white rounded-lg border border-slate-200 flex flex-col h-full">
      <div className="flex items-center justify-between px-4 py-3 border-b border-slate-200">
        <h3 className="text-sm font-semibold text-slate-800 flex items-center gap-2">
          <FileText className="h-4 w-4" />
          {filename}
        </h3>
        <a
          href={fileUrl}
          target="_blank"
          rel="noopener noreferrer"
          className="text-xs text-blue-600 hover:text-blue-700"
        >
          Open original
        </a>
      </div>

      <div className="flex-1 overflow-auto p-4">
        {mimeType === 'application/pdf' ? (
          <iframe
            src={fileUrl}
            title={filename}
            className="w-full h-full min-h-[500px] border-0"
          />
        ) : mimeType.startsWith('image/') ? (
          <img src={fileUrl} alt={filename} className="max-w-full h-auto" />
        ) : null}
      </div>

      {extractedText && (
        <div className="border-t border-slate-200">
          <details className="group">
            <summary className="px-4 py-2 text-xs text-slate-500 cursor-pointer hover:text-slate-700">
              Extracted Text ({extractedText.length} chars)
            </summary>
            <pre className="px-4 pb-4 text-xs text-slate-600 whitespace-pre-wrap max-h-64 overflow-auto font-mono">
              {extractedText}
            </pre>
          </details>
        </div>
      )}
    </div>
  );
}
