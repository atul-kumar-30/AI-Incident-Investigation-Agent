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
    <div className="mt-8 space-y-6 border-t border-zinc-800 pt-8">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-semibold text-zinc-100 flex items-center gap-2">
          <Search className="h-5 w-5 text-indigo-400" />
          Investigation Run
        </h2>
        <div className="flex items-center gap-3 text-sm">
          {run.status === InvestigationRunStatus.COMPLETED && (
            <span className="flex items-center gap-1.5 text-emerald-400 bg-emerald-400/10 px-2.5 py-1 rounded-full border border-emerald-500/20">
              <CheckCircle className="h-4 w-4" />
              Completed
            </span>
          )}
          {run.status === InvestigationRunStatus.FAILED && (
            <span className="flex items-center gap-1.5 text-red-400 bg-red-400/10 px-2.5 py-1 rounded-full border border-red-500/20">
              <XCircle className="h-4 w-4" />
              Failed
            </span>
          )}
          {(run.status === InvestigationRunStatus.RUNNING || run.status === InvestigationRunStatus.PENDING) && (
            <span className="flex items-center gap-1.5 text-blue-400 bg-blue-400/10 px-2.5 py-1 rounded-full border border-blue-500/20">
              <Clock className="h-4 w-4 animate-spin" />
              Running
            </span>
          )}
        </div>
      </div>

      {run.summary && (
        <div className="bg-zinc-800/50 rounded-lg p-4 text-sm text-zinc-300 border border-zinc-700">
          <span className="font-medium text-zinc-100 block mb-1">Summary:</span>
          {run.summary}
        </div>
      )}
      
      {/* Hypotheses Section */}
      {(run.status === InvestigationRunStatus.COMPLETED || run.status === InvestigationRunStatus.RUNNING) && (
        <div className="space-y-4">
          <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider flex items-center gap-2">
            <Lightbulb className="h-4 w-4" />
            Hypotheses
          </h3>
          <HypothesisList investigationRunId={run.id} />
        </div>
      )}

      {loading ? (
        <div className="text-center py-8 text-zinc-500">Loading timeline...</div>
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 pt-8 border-t border-zinc-800">
          {/* Timeline */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider">Timeline</h3>
            <div className="relative border-l border-zinc-700 ml-3 space-y-6">
              {steps.map((step) => (
                <div key={step.id} className="relative pl-6">
                  <div className="absolute -left-[5px] top-1.5 h-2 w-2 rounded-full bg-zinc-600 border border-zinc-950" />
                  <div className="text-sm">
                    <span className="font-medium text-zinc-200 capitalize">
                      {step.node_name.replace('_', ' ')}
                    </span>
                    <span className="ml-2 text-xs text-zinc-500">
                      {new Date(step.created_at).toLocaleTimeString()}
                    </span>
                  </div>
                  {step.output_data?.update && (step.output_data.update as any).plan && (
                    <div className="mt-2 text-sm text-zinc-400 bg-zinc-900 rounded p-3 border border-zinc-800">
                      <span className="text-xs font-semibold text-indigo-400 uppercase tracking-wider block mb-1">Plan</span>
                      "{(step.output_data.update as any).plan}"
                    </div>
                  )}
                  {step.output_data?.update && (step.output_data.update as any).tool_results && ((step.output_data.update as any).tool_results as Array<Record<string, unknown>>).map((res, idx: number) => (
                    <div key={idx} className="mt-2 text-sm text-zinc-400 bg-zinc-900 rounded p-3 border border-zinc-800">
                      <span className="text-xs font-semibold text-emerald-400 uppercase tracking-wider block mb-1">Tool Executed: {String(res.tool_name)}</span>
                      Status: {String(res.status)}
                    </div>
                  ))}
                  {step.status === StepStatus.FAILED && (
                    <div className="mt-2 text-sm text-red-400">
                      Failed: {String(step.output_data?.error || "Unknown error")}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>

          {/* Evidence */}
          <div className="space-y-4">
            <h3 className="text-sm font-medium text-zinc-400 uppercase tracking-wider">Evidence Collected</h3>
            {evidence.length === 0 ? (
              <div className="text-sm text-zinc-500 italic">No evidence collected yet.</div>
            ) : (
              <div className="space-y-3">
                {evidence.map((ev) => (
                  <div key={ev.id} className="bg-zinc-900 border border-zinc-800 rounded-lg p-4">
                    <div className="flex items-center gap-2 mb-2 text-xs font-medium text-zinc-400">
                      <FileText className="h-3.5 w-3.5" />
                      {ev.source_type}: {ev.source_name}
                    </div>
                    {ev.source_type === 'LOG' && ev.metadata && ev.metadata.extracted_patterns ? (
                      <div className="space-y-2">
                        <div className="text-xs text-zinc-300">
                          Found <span className="font-bold text-white">{ev.metadata.total_matches}</span> matches for query: <span className="font-mono bg-zinc-800 px-1 rounded text-indigo-300">{JSON.stringify(ev.metadata.query_summary)}</span>
                        </div>
                        <div className="text-xs font-medium text-zinc-400 uppercase tracking-wider mt-2">Top Patterns:</div>
                        <div className="space-y-1">
                          {ev.metadata.extracted_patterns.map((p: any, idx: number) => (
                            <div key={idx} className="text-xs bg-zinc-950 p-2 rounded flex justify-between items-start border border-zinc-800/50">
                              <span className="font-mono text-zinc-300">{p.pattern}</span>
                              <span className="text-zinc-500 font-bold ml-2">x{p.count}</span>
                            </div>
                          ))}
                        </div>
                        <details className="mt-2 text-xs">
                          <summary className="cursor-pointer text-indigo-400 hover:text-indigo-300">View Raw JSON Summary</summary>
                          <pre className="mt-2 text-[10px] text-zinc-400 whitespace-pre-wrap font-mono bg-zinc-950 p-2 rounded max-h-32 overflow-y-auto">
                            {ev.content}
                          </pre>
                        </details>
                      </div>
                    ) : ev.source_type === 'CODE' && ev.metadata && ev.metadata.results ? (
                      <div className="space-y-2">
                        <div className="text-xs text-zinc-300">
                          Found <span className="font-bold text-white">{ev.metadata.total_matches}</span> code matches for query: <span className="font-mono bg-zinc-800 px-1 rounded text-indigo-300">{ev.metadata.query}</span>
                        </div>
                        <div className="space-y-2 mt-2">
                          {ev.metadata.results.map((res: any, idx: number) => (
                            <div key={idx} className="text-xs bg-zinc-950 p-3 rounded border border-zinc-800/50">
                              <div className="flex justify-between items-center mb-2">
                                <span className="font-mono text-indigo-400 font-semibold">{res.file_path}</span>
                                <span className="text-zinc-500">L{res.start_line}-L{res.end_line}</span>
                              </div>
                              <pre className="text-[10px] text-zinc-300 whitespace-pre-wrap font-mono bg-zinc-900 p-2 rounded max-h-48 overflow-y-auto border border-zinc-800">
                                {res.snippet}
                              </pre>
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : ev.source_type === 'GIT_CHANGE' && ev.metadata && ev.metadata.results ? (
                      <div className="space-y-2">
                        <div className="text-xs text-zinc-300">
                          Recent Git Commits found across repositories:
                        </div>
                        <div className="space-y-3 mt-2">
                          {ev.metadata.results.map((repo_res: any, repoIdx: number) => (
                            <div key={repoIdx}>
                              {repo_res.commits?.map((commit: any, cIdx: number) => (
                                <div key={cIdx} className="text-xs bg-zinc-950 p-3 rounded border border-zinc-800/50 mb-2">
                                  <div className="flex justify-between items-center mb-1">
                                    <span className="font-mono text-emerald-400 font-semibold">{commit.commit_hash.substring(0, 8)}</span>
                                    <span className="text-zinc-500">{new Date(commit.timestamp).toLocaleString()}</span>
                                  </div>
                                  <div className="text-zinc-300 font-medium mb-2">{commit.message}</div>
                                  <div className="text-zinc-500 mb-2">By {commit.author}</div>
                                  <div className="space-y-1">
                                    {commit.changed_files?.map((file: any, fIdx: number) => (
                                      <div key={fIdx}>
                                        <div className="flex gap-2 text-zinc-400">
                                          <span className={file.status === 'A' ? 'text-green-500' : file.status === 'D' ? 'text-red-500' : 'text-yellow-500'}>
                                            [{file.status}]
                                          </span>
                                          <span className="font-mono">{file.path}</span>
                                        </div>
                                        {file.diff_snippet && (
                                          <details className="mt-1 ml-6">
                                            <summary className="cursor-pointer text-indigo-400 hover:text-indigo-300 opacity-80 text-[10px]">Show Diff</summary>
                                            <pre className="mt-1 text-[10px] text-zinc-300 whitespace-pre-wrap font-mono bg-zinc-900 p-2 rounded max-h-32 overflow-y-auto border border-zinc-800">
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
                        <div className="text-xs text-zinc-300">
                          Found <span className="font-bold text-white">{ev.metadata.returned_count}</span> relevant document snippets for query: <span className="font-mono bg-zinc-800 px-1 rounded text-indigo-300">{ev.metadata.query}</span>
                        </div>
                        <div className="space-y-3 mt-2">
                          {ev.metadata.results.map((res: any, idx: number) => (
                            <div key={idx} className="text-xs bg-zinc-950 p-3 rounded border border-zinc-800/50 mb-2">
                              <div className="flex justify-between items-center mb-1">
                                <span className="font-mono text-emerald-400 font-semibold">{res.title}</span>
                                <span className="text-zinc-500 bg-zinc-800 px-1 rounded">{res.document_type}</span>
                              </div>
                              {(res.section_title || res.page_number) && (
                                <div className="text-zinc-400 mb-2 flex gap-3">
                                  {res.section_title && <span>Section: <span className="text-zinc-300">{res.section_title}</span></span>}
                                  {res.page_number && <span>Page: <span className="text-zinc-300">{res.page_number}</span></span>}
                                </div>
                              )}
                              <pre className="text-[11px] text-zinc-300 whitespace-pre-wrap font-mono bg-zinc-900 p-2 rounded max-h-48 overflow-y-auto border border-zinc-800">
                                {res.snippet}
                              </pre>
                              {res.match_reasons && res.match_reasons.length > 0 && (
                                <div className="mt-2 text-[10px] text-zinc-500 flex gap-2">
                                  <span>Matched via:</span>
                                  {res.match_reasons.map((r: string, rIdx: number) => (
                                    <span key={rIdx} className="bg-zinc-800/50 px-1 rounded">{r}</span>
                                  ))}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      </div>
                    ) : (
                      <pre className="text-xs text-zinc-300 whitespace-pre-wrap font-mono bg-zinc-950 p-3 rounded">
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
