import { useState, useEffect } from 'react';
import type { Hypothesis } from '../types';
import { hypothesisService } from '../services/hypothesisService';
import HypothesisCard from './HypothesisCard';
import { Lightbulb } from 'lucide-react';

interface HypothesisListProps {
  investigationRunId: string;
}

export default function HypothesisList({ investigationRunId }: HypothesisListProps) {
  const [hypotheses, setHypotheses] = useState<Hypothesis[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const loadHypotheses = async () => {
    try {
      setLoading(true);
      const data = await hypothesisService.getInvestigationHypotheses(investigationRunId);
      setHypotheses(data);
      setError(null);
    } catch (err: any) {
      setError(err.message || "Failed to load hypotheses");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHypotheses();
    const interval = setInterval(loadHypotheses, 5000);
    return () => clearInterval(interval);
  }, [investigationRunId]);

  if (loading && hypotheses.length === 0) {
    return (
      <div className="flex justify-center p-8">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-500/20 border-t-emerald-400"></div>
      </div>
    );
  }

  if (error) {
    return <div className="text-xs font-mono text-rose-400 bg-rose-950/20 border border-rose-500/30 p-3 rounded-xl">{error}</div>;
  }

  if (hypotheses.length === 0) {
    return (
      <div className="text-center p-8 text-slate-500 bg-matrix-card/80 rounded-xl border border-matrix-border">
        <Lightbulb className="h-8 w-8 mx-auto mb-2 text-slate-700" />
        <p className="text-sm font-semibold text-slate-300">No candidate hypotheses yet.</p>
        <p className="text-xs font-mono text-slate-500 mt-1">Hypotheses will appear here once evidence collection and synthesis is complete.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {hypotheses.map(h => (
        <HypothesisCard key={h.id} hypothesis={h} onVerificationUpdate={loadHypotheses} />
      ))}
    </div>
  );
}
