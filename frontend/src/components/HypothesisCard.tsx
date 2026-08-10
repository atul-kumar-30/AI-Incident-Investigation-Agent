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
        // Wait a second for graph to complete
        setTimeout(onVerificationUpdate, 2000);
      }
    } catch (error) {
      console.error("Verification failed", error);
      setVerifying(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch(status) {
      case 'SUPPORTED': return 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30';
      case 'WEAKENED': return 'bg-red-500/20 text-red-400 border-red-500/30';
      case 'INCONCLUSIVE': return 'bg-amber-500/20 text-amber-400 border-amber-500/30';
      default: return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
    }
  };

  return (
    <div className={cn(
      "rounded-xl border bg-zinc-900/50 shadow-sm overflow-hidden",
      hypothesis.rank === 1 ? "border-indigo-500/50" : "border-zinc-800"
    )}>
      {/* Header */}
      <div 
        className="p-5 flex items-start justify-between cursor-pointer hover:bg-zinc-800/30 transition-colors"
        onClick={() => setExpanded(!expanded)}
      >
        <div className="flex gap-4">
          <div className="flex flex-col items-center">
            <span className={cn(
              "text-lg font-bold flex items-center justify-center h-10 w-10 rounded-full border",
              hypothesis.rank === 1 ? "bg-indigo-500/20 text-indigo-400 border-indigo-500/30" : "bg-zinc-800 text-zinc-400 border-zinc-700"
            )}>
              #{hypothesis.rank || '-'}
            </span>
            <span className="text-[10px] uppercase font-bold text-zinc-500 mt-1">Rank</span>
          </div>
          
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-zinc-800 text-zinc-300 border border-zinc-700">
                {hypothesis.category}
              </span>
              <span className={cn("text-xs px-2 py-0.5 rounded-full border", getStatusColor(hypothesis.status))}>
                {hypothesis.status.replace('_', ' ')}
              </span>
            </div>
            <h3 className="text-lg font-medium text-zinc-100">{hypothesis.title}</h3>
            <p className="text-sm text-zinc-400 mt-1 line-clamp-2">{hypothesis.description}</p>
          </div>
        </div>
        
        <div className="flex items-center gap-6">
          <div className="flex flex-col items-end group relative">
            <div className="flex items-end gap-1">
              <span className="text-2xl font-bold text-indigo-400">{hypothesis.score ?? hypothesis.preliminary_score ?? '-'}</span>
              <span className="text-xs text-zinc-500 mb-1">/100</span>
            </div>
            <span className="text-[10px] uppercase font-bold text-zinc-500">Current Evidence Score</span>
            
            <div className="absolute top-full right-0 mt-2 w-64 bg-zinc-800 border border-zinc-700 p-2 rounded shadow-lg opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-10 pointer-events-none">
              <p className="text-xs text-zinc-300">
                Comparative support based on currently available verification evidence.
              </p>
            </div>
          </div>
          
          <button 
            onClick={handleVerify}
            disabled={verifying || latestVerification?.status === 'RUNNING'}
            className="flex items-center gap-1 bg-indigo-600 hover:bg-indigo-700 text-white px-3 py-1.5 rounded-md text-xs font-medium disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            {verifying || latestVerification?.status === 'RUNNING' ? (
              <span className="animate-pulse">Verifying...</span>
            ) : (
              <>
                <Play className="h-3 w-3" />
                Verify Hypothesis
              </>
            )}
          </button>
          
          <div className="text-zinc-500 bg-zinc-800/50 p-2 rounded-full hover:text-zinc-300 transition-colors">
            {expanded ? <ChevronUp className="h-5 w-5" /> : <ChevronDown className="h-5 w-5" />}
          </div>
        </div>
      </div>
      
      {/* Expanded Content */}
      {expanded && (
        <div className="p-5 border-t border-zinc-800 bg-zinc-900">
          
          {/* Verification Details */}
          {latestVerification && (
            <div className="mb-6 p-4 border border-indigo-900/50 bg-indigo-950/20 rounded-lg">
              <h4 className="text-xs font-semibold text-indigo-400 uppercase tracking-wider mb-2">Verification Outcome</h4>
              <p className="text-sm text-zinc-300 mb-3">{latestVerification.summary || 'No summary available.'}</p>
              
              <div className="grid grid-cols-3 gap-4 text-xs">
                <div className="bg-zinc-950 p-2 rounded border border-zinc-800">
                  <span className="block text-zinc-500 mb-1">Status</span>
                  <span className={cn("font-medium", 
                    latestVerification.status === 'COMPLETED' ? "text-emerald-400" :
                    latestVerification.status === 'FAILED' ? "text-red-400" : "text-amber-400"
                  )}>{latestVerification.status}</span>
                </div>
                <div className="bg-zinc-950 p-2 rounded border border-zinc-800">
                  <span className="block text-zinc-500 mb-1">Score Change</span>
                  <span className="font-medium text-zinc-300">
                    {latestVerification.initial_score ?? '-'} → {latestVerification.final_score ?? '-'}
                  </span>
                </div>
                <div className="bg-zinc-950 p-2 rounded border border-zinc-800">
                  <span className="block text-zinc-500 mb-1">Net Evidence Delta</span>
                  <span className={cn("font-medium", 
                    (latestVerification.support_delta - latestVerification.contradiction_delta) > 0 ? "text-emerald-400" :
                    (latestVerification.support_delta - latestVerification.contradiction_delta) < 0 ? "text-red-400" : "text-zinc-300"
                  )}>
                    {(latestVerification.support_delta - latestVerification.contradiction_delta).toFixed(1)}
                  </span>
                </div>
              </div>
              
              {/* Timeline */}
              {verificationSteps.length > 0 && (
                <div className="mt-4">
                  <h4 className="text-[10px] font-semibold text-zinc-500 uppercase tracking-wider mb-2">Verification Timeline</h4>
                  <div className="space-y-2 max-h-40 overflow-y-auto pr-2">
                    {verificationSteps.map(step => (
                      <div key={step.id} className="flex gap-2 text-xs text-zinc-400 bg-zinc-950/50 p-2 rounded border border-zinc-800/50">
                        <span className="text-indigo-400 min-w-16">[{step.tool_name || step.step_type}]</span>
                        <span className="truncate">{step.objective || 'Processing...'}</span>
                        <span className="ml-auto flex-shrink-0 font-mono text-[10px]">{step.status}</span>
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
              <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Why it is plausible</h4>
              <p className="text-sm text-zinc-300 bg-zinc-950 p-4 rounded-lg border border-zinc-800/50">
                {hypothesis.reasoning_summary}
              </p>
            </div>
          )}
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            {/* Supporting Evidence */}
            <div>
              <h4 className="text-xs font-semibold text-emerald-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <CheckCircle className="h-4 w-4" />
                Supporting Evidence ({supporting.length})
              </h4>
              <div className="space-y-3">
                {supporting.length > 0 ? supporting.map((m) => (
                  <EvidenceItem key={m.id} mapping={m} type="support" />
                )) : (
                  <div className="text-sm text-zinc-500 italic">No direct supporting evidence mapped.</div>
                )}
              </div>
            </div>
            
            {/* Contradicting Evidence */}
            <div>
              <h4 className="text-xs font-semibold text-red-400 uppercase tracking-wider mb-3 flex items-center gap-2">
                <AlertCircle className="h-4 w-4" />
                Contradicting Evidence ({contradicting.length})
              </h4>
              <div className="space-y-3">
                {contradicting.length > 0 ? contradicting.map((m) => (
                  <EvidenceItem key={m.id} mapping={m} type="contradict" />
                )) : (
                  <div className="text-sm text-zinc-500 italic">No contradicting evidence identified.</div>
                )}
              </div>
            </div>
          </div>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Verification Requirements */}
            <div>
              <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2 flex items-center gap-1">
                <HelpCircle className="h-3 w-3" />
                Verification Requirements
              </h4>
              {hypothesis.verification_requirements && hypothesis.verification_requirements.length > 0 ? (
                <ul className="list-disc pl-5 space-y-1 text-sm text-zinc-300">
                  {hypothesis.verification_requirements.map((req, idx) => (
                    <li key={idx}>{req}</li>
                  ))}
                </ul>
              ) : (
                <span className="text-sm text-zinc-500">None specified.</span>
              )}
            </div>
            
            {/* Missing Evidence */}
            <div>
              <h4 className="text-xs font-semibold text-zinc-400 uppercase tracking-wider mb-2">Missing Evidence</h4>
              {hypothesis.missing_evidence && hypothesis.missing_evidence.length > 0 ? (
                <ul className="space-y-2">
                  {hypothesis.missing_evidence.map((me, idx) => (
                    <li key={idx} className="text-sm text-zinc-300 bg-zinc-950 p-2 rounded border border-zinc-800/50 flex flex-col">
                      <span>{me.description}</span>
                      {me.preferred_source && (
                        <span className="text-[10px] text-zinc-500 mt-1 uppercase">Source: {me.preferred_source}</span>
                      )}
                    </li>
                  ))}
                </ul>
              ) : (
                <span className="text-sm text-zinc-500">None specified.</span>
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
      "rounded border p-3 bg-zinc-950 relative",
      type === 'support' ? "border-emerald-900/30" : "border-red-900/30"
    )}>
      {mapping.origin === 'VERIFICATION' && (
        <div className="absolute top-0 right-0 -mt-2 -mr-2 bg-indigo-500 text-white text-[9px] font-bold px-1.5 py-0.5 rounded shadow">
          NEW
        </div>
      )}
      <div className="flex justify-between items-start mb-2">
        <div className="flex items-center gap-2">
          <span className="text-[10px] font-bold text-zinc-300 bg-zinc-800 px-1.5 py-0.5 rounded">
            {mapping.evidence?.source_type || 'UNKNOWN'}
          </span>
          <span className={cn(
            "text-[10px] font-bold px-1.5 py-0.5 rounded",
            mapping.strength === 'HIGH' ? "bg-amber-500/20 text-amber-500" :
            mapping.strength === 'MEDIUM' ? "bg-blue-500/20 text-blue-400" :
            "bg-zinc-700 text-zinc-300"
          )}>
            {mapping.strength}
          </span>
        </div>
        <span className="text-[10px] text-zinc-500 font-mono">ID: {mapping.evidence_id.substring(0,8)}</span>
      </div>
      
      <p className="text-xs text-zinc-300 mb-2">{mapping.reason}</p>
      
      <div className="mt-2 flex items-center justify-between">
        <button 
          onClick={() => setShowDetails(!showDetails)}
          className="text-[10px] text-indigo-400 hover:text-indigo-300 flex items-center gap-1"
        >
          <FileText className="h-3 w-3" />
          {showDetails ? 'Hide Source' : 'View Source'}
        </button>
        {mapping.origin === 'VERIFICATION' && (
          <span className="text-[9px] text-indigo-400/70 border border-indigo-500/30 px-1 rounded">VERIFIED EVIDENCE</span>
        )}
      </div>
        
      {showDetails && mapping.evidence && (
        <div className="mt-2 text-[10px] bg-zinc-900 p-2 rounded border border-zinc-800 max-h-32 overflow-y-auto">
          <div className="font-semibold text-zinc-400 mb-1">{mapping.evidence.source_name}</div>
          <pre className="whitespace-pre-wrap font-mono text-zinc-500">{mapping.evidence.content}</pre>
        </div>
      )}
    </div>
  );
}
