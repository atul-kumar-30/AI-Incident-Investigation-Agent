import { useState, useEffect } from 'react';
import { CheckCircle, XCircle, Clock, Search, FileText, Lightbulb } from 'lucide-react';
import type { InvestigationRun, InvestigationStep, Evidence } from '../types';
import { InvestigationRunStatus, StepStatus } from '../types';
import { investigationService } from '../services/investigationService';
import HypothesisList from './HypothesisList';

interface InvestigationPanelProps {
  run: InvestigationRun;
}

export default function InvestigationPanel({ run }: InvestigationPanelProps) {
  const [steps, setSteps] = useState<InvestigationStep[]>([]);
  const [evidence, setEvidence] = useState<Evidence[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    
    const loadDetails = async () => {
      try {
        const [stepsData, evidenceData] = await Promise.all([
          investigationService.getInvestigationSteps(run.id),
          investigationService.getInvestigationEvidence(run.id)
        ]);
        if (mounted) {
          setSteps(stepsData);
          setEvidence(evidenceData);
        }
      } catch (err) {
        console.error("Failed to load investigation details:", err);
      } finally {
        if (mounted) setLoading(false);
      }
    };
    
    loadDetails();
    
    // Poll if still running
    let interval: ReturnType<typeof setInterval>;
    if (run.status === InvestigationRunStatus.PENDING || run.status === InvestigationRunStatus.RUNNING) {
      interval = setInterval(loadDetails, 2000);
    }
    
    return () => {
      mounted = false;
      if (interval) clearInterval(interval);
    };
  }, [run.id, run.status]);

  return (
    <div className="mt-8 space-y-6 border-t border-matrix-border pt-8">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2.5">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
            <Search className="h-4 w-4 text-emerald-400" />
          </div>
          Investigation Run
        </h2>
        <div className="flex items-center gap-3 text-xs font-mono">
          {run.status === InvestigationRunStatus.COMPLETED && (
            <span className="flex items-center gap-1.5 text-emerald-400 bg-emerald-500/15 px-3 py-1 rounded-full border border-emerald-500/30 shadow-matrix-glow-sm">
              <CheckCircle className="h-3.5 w-3.5" />
              COMPLETED
            </span>
          )}
          {run.status === InvestigationRunStatus.FAILED && (
            <span className="flex items-center gap-1.5 text-rose-400 bg-rose-500/15 px-3 py-1 rounded-full border border-rose-500/30">
              <XCircle className="h-3.5 w-3.5" />
              FAILED
            </span>
          )}
          {(run.status === InvestigationRunStatus.RUNNING || run.status === InvestigationRunStatus.PENDING) && (
            <span className="flex items-center gap-1.5 text-amber-400 bg-amber-500/15 px-3 py-1 rounded-full border border-amber-500/30 animate-pulse">
              <Clock className="h-3.5 w-3.5 animate-spin" />
              RUNNING
            </span>
          )}
        </div>
      </div>

      {run.summary && (
        <div className="bg-matrix-surface rounded-xl p-4 text-xs font-mono text-slate-300 border border-matrix-border shadow-sm">
          <span className="font-semibold text-emerald-400 block mb-1 uppercase tracking-wider">Executive Summary:</span>
          {run.summary}
        </div>
      )}
      
      {/* Hypotheses Section */}
      {(run.status === InvestigationRunStatus.COMPLETED || run.status === InvestigationRunStatus.RUNNING) && (
        <div className="space-y-4">
          <h3 className="text-xs font-mono font-medium text-emerald-400 uppercase tracking-wider flex items-center gap-2">
            <Lightbulb className="h-4 w-4 text-emerald-400" />
            Generated Hypotheses & Active Verifications
          </h3>
          <HypothesisList investigationRunId={run.id} />
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-slate-500 font-mono text-xs">Loading telemetry & evidence timeline...</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 pt-8 border-t border-matrix-border">
          {/* Timeline */}
          <div className="space-y-4">
            <h3 className="text-xs font-mono font-medium text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
              Execution Steps
            </h3>
            <div className="relative border-l border-emerald-500/30 ml-3 space-y-6">
              {steps.map((step) => (
                <div key={step.id} className="relative pl-6">
                  <div className="absolute -left-[5.5px] top-1.5 h-2.5 w-2.5 rounded-full bg-emerald-400 border-2 border-matrix-bg shadow-matrix-glow-sm" />
                  <div className="text-sm">
                    <span className="font-semibold text-slate-200 capitalize font-mono text-xs">
                      {step.node_name.replace('_', ' ')}
                    </span>
                    <span className="ml-2 text-[11px] font-mono text-slate-500">
                      {new Date(step.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  {step.output_data?.update && (step.output_data.update as any).plan && (
                    <div className="mt-2 text-xs font-mono text-slate-300 bg-matrix-surface rounded-lg p-3 border border-matrix-border">
                      <span className="text-[10px] font-semibold text-emerald-400 uppercase tracking-wider block mb-1">Plan</span>
                      "{(step.output_data.update as any).plan}"
                    </div>
                  )}
                  {step.output_data?.update && (step.output_data.update as any).tool_results && ((step.output_data.update as any).tool_results as Array<Record<string, unknown>>).map((res, idx: number) => (
                    <div key={idx} className="mt-2 text-xs font-mono text-slate-300 bg-matrix-surface rounded-lg p-3 border border-matrix-border">
                      <span className="text-[10px] font-semibold text-teal-400 uppercase tracking-wider block mb-1">Tool Executed: {String(res.tool_name)}</span>
                      Status: {String(res.status)}
                    </div>
                  ))}
                  {step.status === StepStatus.FAILED && (
                    <div className="mt-2 text-xs font-mono text-rose-400 bg-rose-950/20 p-2.5 rounded border border-rose-500/30">
                      Failed: {String(step.output_data?.error || "Unknown error")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Evidence */}
          <div className="space-y-4">
            <h3 className="text-xs font-mono font-medium text-slate-400 uppercase tracking-wider flex items-center gap-2">
              <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
              Synthesized Evidence ({evidence.length})
            </h3>
            {evidence.length === 0 ? (
              <div className="text-xs font-mono text-slate-500 italic p-4 bg-matrix-surface rounded-xl border border-matrix-border">
                No evidence collected yet.
              </div>
            ) : (
              <div className="space-y-3">
                {evidence.map((ev) => (
                  <div key={ev.id} className="bg-matrix-card border border-matrix-border rounded-xl p-4 shadow-sm hover:border-emerald-500/30 transition-all">
                    <div className="flex items-center gap-2 mb-2 text-xs font-mono font-medium text-emerald-400">
                      <FileText className="h-3.5 w-3.5" />
                      <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/30">{ev.source_type}</span>
                      <span className="text-slate-400">{ev.source_name}</span>
                    </div>
                    {ev.source_type === 'LOG' && ev.metadata && ev.metadata.extracted_patterns ? (
                      <div className="space-y-2">
                        <div className="text-xs font-mono text-slate-300">
                          Found <span className="font-bold text-emerald-400">{ev.metadata.total_matches}</span> matches for query: <span className="bg-matrix-surface px-1.5 py-0.5 rounded text-cyan-300 border border-matrix-border">{JSON.stringify(ev.metadata.query_summary)}</span>
                        </div>
                        <div className="text-[10px] font-mono text-slate-400 uppercase tracking-wider mt-2">Top Patterns:</div>
                        <div className="space-y-1">
                          {ev.metadata.extracted_patterns.map((p: any, idx: number) => (
                            <div key={idx} className="text-xs font-mono bg-matrix-surface p-2 rounded flex justify-between items-start border border-matrix-border">
                              <span className="text-slate-300">{p.pattern}</span>
                              <span className="text-emerald-400 font-bold ml-2">x{p.count}</span>
                            </div>
                          ))}
                        </div>
                        <details className="mt-2 text-xs font-mono">
                          <summary className="cursor-pointer text-emerald-400 hover:text-emerald-300">View Raw JSON</summary>
                          <pre className="mt-2 text-[10px] text-slate-400 whitespace-pre-wrap font-mono bg-matrix-bg p-2.5 rounded-lg max-h-32 overflow-y-auto border border-matrix-border">
                            {ev.content}
                          </pre>
                        </details>
                      </div>
                    ) : ev.source_type === 'CODE' && ev.metadata && ev.metadata.results ? (
                      <div className="space-y-2">
                        <div className="text-xs font-mono text-slate-300">
                          Found <span className="font-bold text-emerald-400">{ev.metadata.total_matches}</span> code matches for query: <span className="bg-matrix-surface px-1.5 py-0.5 rounded text-cyan-300 border border-matrix-border">{ev.metadata.query}</span>
                        </div>
                        <div className="space-y-2 mt-2">
                          {ev.metadata.results.map((res: any, idx: number) => (
                            <div key={idx} className="text-xs bg-matrix-surface p-3 rounded-lg border border-matrix-border">
                              <div className="flex justify-between items-center mb-2 font-mono text-xs">
                                <span className="text-emerald-400 font-semibold">{res.file_path}</span>
                                <span className="text-slate-500">L{res.start_line}-L{res.end_line}</span>
                              </div>
                              <pre className="text-[11px] text-slate-300 whitespace-pre-wrap font-mono bg-matrix-bg p-2 rounded border border-matrix-border max-h-48 overflow-y-auto">
                                {res.snippet}
                              </pre>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : ev.source_type === 'GIT_CHANGE' && ev.metadata && ev.metadata.results ? (
                      <div className="space-y-2">
                        <div className="text-xs font-mono text-slate-300">
                          Recent Git Commits found across repositories:
                        </div>
                        <div className="space-y-3 mt-2">
                          {ev.metadata.results.map((repo_res: any, repoIdx: number) => (
                            <div key={repoIdx}>
                              {repo_res.commits?.map((commit: any, cIdx: number) => (
                                <div key={cIdx} className="text-xs bg-matrix-surface p-3 rounded-lg border border-matrix-border mb-2 font-mono">
                                  <div className="flex justify-between items-center mb-1">
                                    <span className="text-emerald-400 font-semibold">{commit.commit_hash.substring(0, 8)}</span>
                                    <span className="text-slate-500 text-[10px]">{new Date(commit.timestamp).toLocaleString()}</span>
                                  </div>
                                  <div className="text-slate-200 font-medium mb-1 font-sans">{commit.message}</div>
                                  <div className="text-slate-500 mb-2 text-[11px]">By {commit.author}</div>
                                  <div className="space-y-1">
                                    {commit.changed_files?.map((file: any, fIdx: number) => (
                                      <div key={fIdx}>
                                        <div className="flex gap-2 text-slate-400 text-xs">
                                          <span className={file.status === 'A' ? 'text-emerald-400' : file.status === 'D' ? 'text-rose-400' : 'text-amber-400'}>
                                            [{file.status}]
                                          </span>
                                          <span className="font-mono">{file.path}</span>
                                        </div>
                                        {file.diff_snippet && (
                                          <details className="mt-1 ml-4">
                                            <summary className="cursor-pointer text-emerald-400 hover:text-emerald-300 text-[10px]">Show Diff</summary>
                                            <pre className="mt-1 text-[10px] text-slate-300 whitespace-pre-wrap font-mono bg-matrix-bg p-2 rounded max-h-32 overflow-y-auto border border-matrix-border">
                                              {file.diff_snippet}
                                            </pre>
                                          </details>
                                        )}
                                      </div>
                                    ))}
                                  </div>
                                </div>
                              ))}
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : ev.source_type === 'DOCUMENT' && ev.metadata && ev.metadata.results ? (
                      <div className="space-y-2">
                        <div className="text-xs font-mono text-slate-300">
                          Found <span className="font-bold text-emerald-400">{ev.metadata.returned_count}</span> relevant document snippets for query: <span className="bg-matrix-surface px-1.5 py-0.5 rounded text-cyan-300 border border-matrix-border">{ev.metadata.query}</span>
                        </div>
                        <div className="space-y-3 mt-2">
                          {ev.metadata.results.map((res: any, idx: number) => (
                            <div key={idx} className="text-xs bg-matrix-surface p-3 rounded-lg border border-matrix-border mb-2 font-mono">
                              <div className="flex justify-between items-center mb-1">
                                <span className="text-emerald-400 font-semibold">{res.title}</span>
                                <span className="text-slate-400 bg-matrix-bg px-1.5 py-0.5 rounded text-[10px] border border-matrix-border">{res.document_type}</span>
                              </div>
                              <pre className="text-[11px] text-slate-300 whitespace-pre-wrap font-mono bg-matrix-bg p-2 rounded max-h-48 overflow-y-auto border border-matrix-border">
                                {res.snippet}
                              </pre>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <pre className="text-xs text-slate-300 whitespace-pre-wrap font-mono bg-matrix-bg p-3 rounded-lg border border-matrix-border">
                        {ev.content}
                      </pre>
                    )}
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
