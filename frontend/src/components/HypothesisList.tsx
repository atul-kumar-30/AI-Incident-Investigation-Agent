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

  useEffect(() => {
    let mounted = true;
    
    const loadHypotheses = async () => {
      try {
        setLoading(true);
        const data = await hypothesisService.getInvestigationHypotheses(investigationRunId);
        if (mounted) {
          setHypotheses(data);
          setError(null);
        }
      } catch (err: any) {
        if (mounted) setError(err.message || "Failed to load hypotheses");
      } finally {
        if (mounted) setLoading(false);
      }
    };
    
    loadHypotheses();
    
    // Auto refresh periodically if there's an ongoing investigation run
    // But since the parent component handles run status, we'll just fetch once here
    // or rely on parent updates to re-mount/trigger this.
    // For now, a simple interval to pick up new hypotheses if they are generated
    const interval = setInterval(loadHypotheses, 5000);
    
    return () => {
      mounted = false;
      clearInterval(interval);
    };
  }, [investigationRunId]);

  if (loading && hypotheses.length === 0) {
    return (
      <div className="flex justify-center p-8">
        <div className="h-6 w-6 animate-spin rounded-full border-2 border-indigo-500 border-t-transparent"></div>
      </div>
    );
  }

  if (error) {
    return <div className="text-sm text-red-500 bg-red-500/10 p-3 rounded">{error}</div>;
  }

  if (hypotheses.length === 0) {
    return (
      <div className="text-center p-8 text-zinc-500 bg-zinc-900/50 rounded-lg border border-zinc-800">
        <Lightbulb className="h-8 w-8 mx-auto mb-2 text-zinc-700" />
        <p>No hypotheses have been generated yet.</p>
        <p className="text-xs mt-1">Hypotheses will appear here once evidence collection and synthesis is complete.</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {hypotheses.map(h => (
        <HypothesisCard key={h.id} hypothesis={h} />
      ))}
    </div>
  );
}
