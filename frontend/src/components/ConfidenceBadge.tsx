interface Props {
  score: number;
}

export default function ConfidenceBadge({ score }: Props) {
  const pct = Math.round(score * 100);
  let color = 'bg-red-100 text-red-700';
  if (pct >= 80) color = 'bg-green-100 text-green-700';
  else if (pct >= 50) color = 'bg-yellow-100 text-yellow-700';

  return (
    <span className={`inline-flex items-center gap-1 text-xs font-medium px-2 py-0.5 rounded ${color}`}>
      {pct}% confidence
    </span>
  );
}
