import { useState, useEffect } from 'react';
import type { Hypothesis, HypothesisEvidenceMapping } from '../types';
import { ChevronDown, ChevronUp, AlertCircle, FileText, HelpCircle, CheckCircle, Play } from 'lucide-react';
import { cn } from '../utils';
import { hypothesisService } from '../services/hypothesisService';

interface HypothesisCardProps {
  hypothesis: Hypothesis;
  onVerificationUpdate?: () => void;
}

export default function HypothesisCard({ hypothesis, onVerificationUpdate }: HypothesisCardProps) {
  const [expanded, setExpanded] = useState(false);
  const [verifying, setVerifying] = useState(false);
  const [verificationSteps, setVerificationSteps] = useState<any[]>([]);
  
  const supporting = hypothesis.evidence_mappings?.filter(m => m.relationship === 'SUPPORTS') || [];
  const contradicting = hypothesis.evidence_mappings?.filter(m => m.relationship === 'CONTRADICTS') || [];
  
  const latestVerification = hypothesis.verifications && hypothesis.verifications.length > 0 
    ? hypothesis.verifications[0] 
    : null;

  useEffect(() => {
    if (expanded && latestVerification) {
      hypothesisService.getVerificationSteps(latestVerification.id)
        .then(setVerificationSteps)
        .catch(console.error);
    }
  }, [expanded, latestVerification]);

  const handleVerify = async (e: React.MouseEvent) => {
    e.stopPropagation();
    if (verifying) return;
    
    setVerifying(true);
    try {
      await hypothesisService.verifyHypothesis(hypothesis.id);
      if (onVerificationUpdate) {
        await onVerificationUpdate();
      }
    } catch (error) {
      console.error("Verification failed", error);
    } finally {
      setVerifying(false);
      if (onVerificationUpdate) {
        setTimeout(onVerificationUpdate, 1500);
      }
    }
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'SUPPORTED': return 'bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-matrix-glow-sm';
      case 'WEAKENED': return 'bg-rose-500/20 text-rose-300 border-rose-500/40';
      case 'INCONCLUSIVE': return 'bg-amber-500/20 text-amber-300 border-amber-500/40';
      default: return 'bg-cyan-500/15 text-cyan-300 border-cyan-500/30';
    }
  };

  return (
    <div className={cn(
      "rounded-2xl border bg-matrix-card/90 shadow-sm overflow-hidden backdrop-blur transition-all duration-300",
      hypothesis.rank === 1 ? "border-emerald-500/40 shadow-matrix-glow-sm" : "border-matrix-border hover:border-emerald-500/25"
    )}>
      {/* Header */}
      <div 
        className="p-5 flex items-start justify-between cursor-pointer hover:bg-matrix-surface/50 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex gap-4">
          <div className="flex flex-col items-center">
            <span className={cn(
              "text-base font-bold font-mono flex items-center justify-center h-10 w-10 rounded-xl border",
              hypothesis.rank === 1 
                ? "bg-emerald-500/20 text-emerald-300 border-emerald-500/40 shadow-matrix-glow-sm" 
                : "bg-matrix-surface text-slate-400 border-matrix-border"
            )}>
              #{hypothesis.rank || '-'}
            </span>
            <span className="text-[10px] uppercase font-mono tracking-wider text-slate-500 mt-1">Rank</span>
          </div>
          
          <div>
            <div className="flex items-center gap-2 mb-1.5 font-mono">
              <span className="text-xs px-2 py-0.5 rounded-md bg-matrix-surface text-slate-300 border border-matrix-border">
                {hypothesis.category}
              </span>
              <span className={cn("text-xs px-2.5 py-0.5 rounded-full border font-medium", getStatusColor(hypothesis.status))}>
                {hypothesis.status.replace('_', ' ')}
              </span>
            </div>
            <h3 className="text-lg font-bold text-slate-100">{hypothesis.title}</h3>
            <p className="text-sm text-slate-400 mt-1 line-clamp-2">{hypothesis.description}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="flex flex-col items-end group relative">
            <div className="flex items-end gap-1">
              <span className="text-2xl font-extrabold font-mono text-emerald-400">
                {hypothesis.score ?? hypothesis.preliminary_score ?? '-'}
              </span>
              <span className="text-xs font-mono text-slate-500 mb-1">/100</span>
            </div>
            <span className="text-[10px] uppercase font-mono tracking-wider text-slate-500">Evidence Score</span>
          </div>
          
          <button 
            onClick={handleVerify}
            disabled={verifying || latestVerification?.status === 'RUNNING'}
            className="flex items-center gap-1.5 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 text-black px-3.5 py-2 rounded-lg text-xs font-semibold shadow-matrix-glow disabled:opacity-50 disabled:cursor-not-allowed transition-all"
          >
            {verifying || latestVerification?.status === 'RUNNING' ? (
              <span className="animate-pulse font-mono">Verifying...</span>
            ) : (
              <>
                <Play className="h-3.5 w-3.5 fill-black" />
                <span>Verify</span>
              </>
            )}
          </button>
          
          <div className="text-slate-400 bg-matrix-surface p-2 rounded-lg border border-matrix-border hover:text-slate-200 transition-colors">
            {expanded ? <ChevronUp className="h-4 w-4" /> : <ChevronDown className="h-4 w-4" />}
          </div>
        </div>
      </div>
      
      {/* Expanded Content */}
      {expanded && (
        <div className="p-6 border-t border-matrix-border bg-matrix-bg/60">
          
          {/* Verification Details */}
          {latestVerification && (
            <div className="mb-6 p-5 border border-emerald-500/30 bg-emerald-950/20 rounded-xl shadow-matrix-glow-sm">
              <h4 className="text-xs font-mono font-semibold text-emerald-400 uppercase tracking-wider mb-2">
                Active Verification Outcome
              </h4>
              <p className="text-sm text-slate-200 mb-4 leading-relaxed font-sans">
                {latestVerification.summary || 'No summary available.'}
              </p>
              
              <div className="grid grid-cols-3 gap-4 text-xs font-mono">
                <div className="bg-matrix-card p-3 rounded-lg border border-matrix-border">
                  <span className="block text-slate-500 mb-1">Status</span>
                  <span className={cn("font-semibold", 
                    latestVerification.status === 'COMPLETED' ? "text-emerald-400" :
                    latestVerification.status === 'FAILED' ? "text-rose-400" : "text-amber-400"
                  )}>{latestVerification.status}</span>
                </div>
                <div className="bg-matrix-card p-3 rounded-lg border border-matrix-border">
                  <span className="block text-slate-500 mb-1">Score Drift</span>
                  <span className="font-semibold text-slate-200">
                    {latestVerification.initial_score ?? '-'} → {latestVerification.final_score ?? '-'}
                  </span>
                </div>
                <div className="bg-matrix-card p-3 rounded-lg border border-matrix-border">
                  <span className="block text-slate-500 mb-1">Net Delta</span>
                  <span className={cn("font-semibold", 
                    (latestVerification.support_delta - latestVerification.contradiction_delta) > 0 ? "text-emerald-400" :
                    (latestVerification.support_delta - latestVerification.contradiction_delta) < 0 ? "text-rose-400" : "text-slate-300"
                  )}>
                    {(latestVerification.support_delta - latestVerification.contradiction_delta).toFixed(1)}
                  </span>
                </div>
              </div>
              
              {/* Timeline */}
              {verificationSteps.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-[10px] font-mono font-semibold text-slate-400 uppercase tracking-wider mb-2">Verification Steps</h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto pr-2">
                    {verificationSteps.map(step => (
                      <div key={step.id} className="flex gap-2 text-xs font-mono text-slate-300 bg-matrix-card p-2.5 rounded-lg border border-matrix-border">
                        <span className="text-emerald-400 font-semibold min-w-16">[{step.tool_name || step.step_type}]</span>
                        <span className="truncate text-slate-300">{step.objective || 'Processing...'}</span>
                        <span className="ml-auto flex-shrink-0 text-slate-500 text-[10px]">{step.status}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Reasoning */}
          {hypothesis.reasoning_summary && (
            <div className="mb-6">
              <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider mb-2">Agent Plausibility Rationale</h4>
              <p className="text-sm text-slate-300 bg-matrix-card p-4 rounded-xl border border-matrix-border leading-relaxed">
                {hypothesis.reasoning_summary}
              </p>
            </div>
          )}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Supporting Evidence */}
            <div>
              <h4 className="text-xs font-mono font-semibold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <CheckCircle className="h-4 w-4" />
                Supporting Evidence ({supporting.length})
              </h4>
              <div className="space-y-3">
                {supporting.length > 0 ? supporting.map((m) => (
                  <EvidenceItem key={m.id} mapping={m} type="support" />
                )) : (
                  <div className="text-xs font-mono text-slate-500 italic p-3 bg-matrix-card rounded-xl border border-matrix-border">
                    No direct supporting evidence mapped.
                  </div>
                )}
              </div>
            </div>
            
            {/* Contradicting Evidence */}
            <div>
              <h4 className="text-xs font-mono font-semibold text-rose-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Contradicting Evidence ({contradicting.length})
              </h4>
              <div className="space-y-3">
                {contradicting.length > 0 ? contradicting.map((m) => (
                  <EvidenceItem key={m.id} mapping={m} type="contradict" />
                )) : (
                  <div className="text-xs font-mono text-slate-500 italic p-3 bg-matrix-card rounded-xl border border-matrix-border">
                    No contradicting evidence identified.
                  </div>
                )}
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Verification Requirements */}
            <div>
              <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider mb-2 flex items-center gap-1.5">
                <HelpCircle className="h-3.5 w-3.5 text-cyan-400" />
                Verification Requirements
              </h4>
              {hypothesis.verification_requirements && hypothesis.verification_requirements.length > 0 ? (
                <ul className="list-disc pl-5 space-y-1.5 text-xs font-mono text-slate-300">
                  {hypothesis.verification_requirements.map((req, idx) => (
                    <li key={idx}>{req}</li>
                  ))}
                </ul>
              ) : (
                <span className="text-xs font-mono text-slate-500">None specified.</span>
              )}
            </div>
            
            {/* Missing Evidence */}
            <div>
              <h4 className="text-xs font-mono font-semibold text-slate-400 uppercase tracking-wider mb-2">Missing Evidence</h4>
              {hypothesis.missing_evidence && hypothesis.missing_evidence.length > 0 ? (
                <ul className="space-y-2">
                  {hypothesis.missing_evidence.map((me, idx) => (
                    <li key={idx} className="text-xs font-mono text-slate-300 bg-matrix-card p-3 rounded-lg border border-matrix-border flex flex-col">
                      <span>{me.description}</span>
                      {me.preferred_source && (
                        <span className="text-[10px] text-emerald-400/80 mt-1 uppercase">Preferred Source: {me.preferred_source}</span>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <span className="text-xs font-mono text-slate-500">None specified.</span>
              )}
            </div>
          </div>
          
        </div>
      )}
    </div>
  );
}

function EvidenceItem({ mapping, type }: { mapping: HypothesisEvidenceMapping, type: 'support' | 'contradict' }) {
  const [showDetails, setShowDetails] = useState(false);
  
  return (
    <div className={cn(
      "rounded-xl border p-4 bg-matrix-card relative shadow-sm",
      type === 'support' ? "border-emerald-500/25 hover:border-emerald-500/40" : "border-rose-500/25 hover:border-rose-500/40"
    )}>
      {mapping.origin === 'VERIFICATION' && (
        <div className="absolute top-0 right-0 -mt-2 -mr-2 bg-emerald-400 text-black text-[9px] font-bold font-mono px-2 py-0.5 rounded shadow-matrix-glow-sm">
          VERIFIED
        </div>
      )}
      <div className="flex justify-between items-start mb-2 font-mono">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold text-slate-200 bg-matrix-surface border border-matrix-border px-1.5 py-0.5 rounded">
            {mapping.evidence?.source_type || 'UNKNOWN'}
          </span>
          <span className={cn(
            "text-[10px] font-bold px-1.5 py-0.5 rounded border",
            mapping.strength === 'HIGH' ? "bg-amber-500/20 text-amber-400 border-amber-500/30" :
            mapping.strength === 'MEDIUM' ? "bg-cyan-500/20 text-cyan-400 border-cyan-500/30" :
            "bg-slate-700/50 text-slate-300 border-slate-600"
          )}>
            {mapping.strength}
          </span>
        </div>
        <span className="text-[10px] text-slate-500 font-mono">ID: {mapping.evidence_id.substring(0,8)}</span>
      </div>
      
      <p className="text-xs text-slate-300 mb-2 leading-relaxed">{mapping.reason}</p>
      
      <div className="mt-2 flex items-center justify-between">
        <button 
          onClick={() => setShowDetails(!showDetails)}
          className="text-xs font-mono text-emerald-400 hover:text-emerald-300 flex items-center gap-1 transition-colors"
        >
          <FileText className="h-3 w-3" />
          {showDetails ? 'Hide Source' : 'View Source'}
        </button>
        {mapping.origin === 'VERIFICATION' && (
          <span className="text-[9px] font-mono text-emerald-400/80 border border-emerald-500/30 px-1.5 py-0.5 rounded">VERIFIED EVIDENCE</span>
        )}
      </div>
        
      {showDetails && mapping.evidence && (
        <div className="mt-3 text-[10px] bg-matrix-bg p-3 rounded-lg border border-matrix-border max-h-36 overflow-y-auto font-mono">
          <div className="font-semibold text-slate-300 mb-1">{mapping.evidence.source_name}</div>
          <pre className="whitespace-pre-wrap text-slate-400">{mapping.evidence.content}</pre>
        </div>
      )}
    </div>
  );
}
