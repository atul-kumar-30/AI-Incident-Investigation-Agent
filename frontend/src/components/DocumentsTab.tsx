import React, { useState, useEffect } from 'react';
import { Upload, CheckCircle, XCircle, FileText, Plus, RefreshCw, File, ChevronDown, ChevronUp, BookOpen } from 'lucide-react';
import type { Document, Incident } from '../types';

interface DocumentsTabProps {
  incident: Incident;
  apiBaseUrl: string;
}

export const DocumentsTab: React.FC<DocumentsTabProps> = ({ incident, apiBaseUrl }) => {
  const [allDocs, setAllDocs] = useState<Document[]>([]);
  const [incidentDocs, setIncidentDocs] = useState<Document[]>([]);
  const [loading, setLoading] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [expandedDocId, setExpandedDocId] = useState<string | null>(null);
  const [docDetails, setDocDetails] = useState<Record<string, any>>({});
  const [loadingDocId, setLoadingDocId] = useState<string | null>(null);

  const fetchDocs = async () => {
    setLoading(true);
    try {
      const [allRes, incRes] = await Promise.all([
        fetch(`${apiBaseUrl}/documents`),
        fetch(`${apiBaseUrl}/incidents/${incident.id}/documents`)
      ]);
      if (allRes.ok) setAllDocs(await allRes.json());
      if (incRes.ok) setIncidentDocs(await incRes.json());
    } catch (err) {
      console.error(err);
    }
    setLoading(false);
  };

  const toggleDoc = async (docId: string) => {
    if (expandedDocId === docId) {
      setExpandedDocId(null);
      return;
    }
    setExpandedDocId(docId);
    if (!docDetails[docId]) {
      setLoadingDocId(docId);
      try {
        const res = await fetch(`${apiBaseUrl}/documents/${docId}`);
        if (res.ok) {
          const data = await res.json();
          setDocDetails(prev => ({ ...prev, [docId]: data }));
        }
      } catch (err) {
        console.error('Failed to fetch document details', err);
      }
      setLoadingDocId(null);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, [incident.id]);

  const handleFileUpload = async (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    formData.append('document_type', 'GENERAL');

    try {
      const res = await fetch(`${apiBaseUrl}/documents`, {
        method: 'POST',
        body: formData,
      });
      if (res.ok) {
        const newDoc = await res.json();
        await handleAssign(newDoc.id);
        fetchDocs();
      }
    } catch (err) {
      console.error(err);
    }
    setUploading(false);
  };

  const handleAssign = async (docId: string) => {
    try {
      await fetch(`${apiBaseUrl}/incidents/${incident.id}/documents/${docId}`, {
        method: 'POST'
      });
      fetchDocs();
    } catch (err) {
      console.error(err);
    }
  };

  const seedDemo = async () => {
    try {
      await fetch(`${apiBaseUrl}/documents/demo`, { method: 'POST' });
      fetchDocs();
    } catch (err) {
      console.error(err);
    }
  };

  const incidentDocIds = new Set(incidentDocs.map(d => d.id));
  const availableDocs = allDocs.filter(d => !incidentDocIds.has(d.id));

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-xl font-bold text-slate-100 flex items-center gap-2.5 font-mono">
          <div className="p-1.5 rounded-lg bg-emerald-500/10 border border-emerald-500/30">
            <FileText className="h-4 w-4 text-emerald-400" />
          </div>
          Runbooks & Fix Guides
        </h2>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchDocs}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono text-slate-300 hover:text-white bg-matrix-surface hover:bg-matrix-cardHover rounded-lg transition-colors border border-matrix-border"
          >
            <RefreshCw className="h-3.5 w-3.5" />
            Refresh
          </button>
          <button
            onClick={seedDemo}
            className="flex items-center gap-2 px-3 py-1.5 text-xs font-mono text-emerald-300 hover:text-white bg-emerald-950/30 hover:bg-emerald-900/40 rounded-lg transition-colors border border-emerald-500/30 shadow-matrix-glow-sm"
          >
            Seed Demo Docs
          </button>
          <label className="flex items-center gap-2 px-4 py-2 text-xs font-semibold font-mono text-black bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-400 hover:to-teal-400 rounded-lg transition-all cursor-pointer shadow-matrix-glow disabled:opacity-50">
            {uploading ? <RefreshCw className="h-3.5 w-3.5 animate-spin" /> : <Upload className="h-3.5 w-3.5" />}
            Upload Document
            <input type="file" hidden accept=".txt,.md,.pdf" onChange={handleFileUpload} disabled={uploading} />
          </label>
        </div>
      </div>

      {loading ? (
        <div className="flex h-48 items-center justify-center">
          <div className="h-6 w-6 animate-spin rounded-full border-2 border-emerald-500/20 border-t-emerald-400"></div>
        </div>
      ) : (
        <div className="space-y-6">
          <div className="rounded-2xl border border-matrix-border bg-matrix-card/90 overflow-hidden shadow-sm backdrop-blur">
            <div className="px-6 py-4 border-b border-matrix-border bg-matrix-surface/80 flex items-center justify-between">
              <h3 className="text-xs font-mono font-medium text-emerald-400 uppercase tracking-wider flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
                Attached to Incident ({incidentDocs.length})
              </h3>
            </div>
            <div className="divide-y divide-matrix-border">
              {incidentDocs.length === 0 ? (
                <div className="p-8 text-center text-xs font-mono text-slate-500 italic">
                  No documents attached to this incident. Attach or upload runbooks, architecture specs, or architecture diagrams.
                </div>
              ) : (
                incidentDocs.map((doc) => (
                  <div key={doc.id} className="transition-colors border-b last:border-b-0 border-matrix-border">
                    <div 
                      onClick={() => toggleDoc(doc.id)}
                      className="p-4 flex items-center justify-between hover:bg-matrix-surface/60 cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-matrix-surface border border-matrix-border">
                          <File className="h-4 w-4 text-emerald-400" />
                        </div>
                        <div>
                          <div className="font-semibold text-sm text-slate-200 flex items-center gap-2">
                            {doc.title}
                            <span className="text-[10px] font-mono text-emerald-400/80 bg-emerald-500/10 px-1.5 py-0.5 rounded border border-emerald-500/20">
                              Click to view content
                            </span>
                          </div>
                          <div className="text-[11px] font-mono text-slate-500 mt-0.5">ID: {doc.id}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-3 font-mono text-xs">
                        <span className="px-2 py-0.5 bg-matrix-surface rounded border border-matrix-border text-slate-400 text-[10px]">
                          {doc.type}
                        </span>
                        {doc.status === 'READY' ? (
                          <span className="flex items-center gap-1.5 px-2.5 py-0.5 bg-emerald-500/15 text-emerald-400 rounded-full border border-emerald-500/30 text-[10px] font-semibold">
                            <CheckCircle className="h-3 w-3" />
                            Ready
                          </span>
                        ) : doc.status === 'FAILED' ? (
                          <span className="flex items-center gap-1.5 px-2.5 py-0.5 bg-rose-500/15 text-rose-400 rounded-full border border-rose-500/30 text-[10px] font-semibold">
                            <XCircle className="h-3 w-3" />
                            Failed
                          </span>
                        ) : (
                          <span className="flex items-center gap-1.5 px-2.5 py-0.5 bg-cyan-500/15 text-cyan-400 rounded-full border border-cyan-500/30 text-[10px] font-semibold">
                            <RefreshCw className="h-3 w-3 animate-spin" />
                            {doc.status}
                          </span>
                        )}
                        <div className="p-1 text-slate-400 hover:text-white">
                          {expandedDocId === doc.id ? (
                            <ChevronUp className="h-4 w-4 text-emerald-400" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </div>
                      </div>
                    </div>

                    {expandedDocId === doc.id && (
                      <div className="p-5 bg-matrix-surface/80 border-t border-matrix-border/80 text-xs animate-in fade-in duration-200">
                        {loadingDocId === doc.id ? (
                          <div className="flex items-center gap-2 text-slate-400 py-6 justify-center font-mono">
                            <RefreshCw className="h-4 w-4 animate-spin text-emerald-400" />
                            <span>Loading document content & runbook instructions...</span>
                          </div>
                        ) : docDetails[doc.id]?.chunks?.length ? (
                          <div className="space-y-4">
                            <div className="flex items-center justify-between pb-2.5 border-b border-matrix-border/60 text-[11px] font-mono text-slate-400">
                              <span className="flex items-center gap-2 text-emerald-400 font-semibold">
                                <BookOpen className="h-4 w-4" />
                                {docDetails[doc.id].chunks.length} Document Section(s) Indexed
                              </span>
                              <span className="text-[10px] text-slate-500 bg-matrix-card px-2 py-0.5 rounded border border-matrix-border">
                                Semantic pgvector (768-dim) Ready
                              </span>
                            </div>
                            {docDetails[doc.id].chunks.map((chunk: any) => (
                              <div key={chunk.id} className="p-4 rounded-xl bg-matrix-card/90 border border-matrix-border/80 space-y-2.5 shadow-sm">
                                {chunk.section_title && (
                                  <div className="font-semibold text-slate-100 text-xs font-mono flex items-center gap-2 border-b border-matrix-border/40 pb-2">
                                    <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-500/50"></span>
                                    <span>{chunk.section_title}</span>
                                    {chunk.page_number && (
                                      <span className="text-[10px] text-slate-500 font-normal ml-auto">Page {chunk.page_number}</span>
                                    )}
                                  </div>
                                )}
                                <pre className="text-xs text-slate-200 font-mono whitespace-pre-wrap leading-relaxed bg-black/40 p-3 rounded-lg border border-matrix-border/40 selection:bg-emerald-500/20">
                                  {chunk.content}
                                </pre>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-slate-500 italic py-4 text-center font-mono">No readable content found for this document.</div>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="rounded-2xl border border-matrix-border bg-matrix-card/90 overflow-hidden shadow-sm backdrop-blur">
            <div className="px-6 py-4 border-b border-matrix-border bg-matrix-surface/80 flex items-center justify-between">
              <h3 className="text-xs font-mono font-medium text-slate-400 uppercase tracking-wider flex items-center gap-2">
                <span className="w-1.5 h-1.5 rounded-full bg-cyan-400"></span>
                Available Runbooks & Fix Guides ({availableDocs.length})
              </h3>
            </div>
            <div className="divide-y divide-matrix-border max-h-96 overflow-y-auto">
              {availableDocs.length === 0 ? (
                <div className="p-8 text-center text-xs font-mono text-slate-500 italic">
                  No additional runbooks or fix guides available. Click "Seed Demo Docs" or "Upload Document" above.
                </div>
              ) : (
                availableDocs.map((doc) => (
                  <div key={doc.id} className="transition-colors border-b last:border-b-0 border-matrix-border">
                    <div 
                      onClick={() => toggleDoc(doc.id)}
                      className="p-4 flex items-center justify-between hover:bg-matrix-surface/60 cursor-pointer transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        <div className="p-2 rounded-lg bg-matrix-surface border border-matrix-border">
                          <File className="h-4 w-4 text-slate-500" />
                        </div>
                        <div>
                          <div className="font-semibold text-sm text-slate-300 flex items-center gap-2">
                            {doc.title}
                            <span className="text-[10px] font-mono text-slate-500 bg-matrix-surface px-1.5 py-0.5 rounded border border-matrix-border">
                              Click to preview
                            </span>
                          </div>
                          <div className="text-[11px] font-mono text-slate-600 mt-0.5">ID: {doc.id}</div>
                        </div>
                      </div>
                      <div className="flex items-center gap-4 font-mono text-xs">
                        <div className="flex items-center gap-2">
                          <span className="px-2 py-0.5 bg-matrix-surface rounded border border-matrix-border text-slate-500 text-[10px]">
                            {doc.type}
                          </span>
                          {doc.status === 'READY' ? (
                            <span className="flex items-center text-emerald-400">
                              <CheckCircle className="h-3.5 w-3.5" />
                            </span>
                          ) : doc.status === 'FAILED' ? (
                            <span className="flex items-center text-rose-400">
                              <XCircle className="h-3.5 w-3.5" />
                            </span>
                          ) : (
                            <span className="flex items-center text-cyan-400">
                              <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                            </span>
                          )}
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleAssign(doc.id);
                          }}
                          disabled={doc.status !== 'READY'}
                          className="p-1.5 text-slate-400 hover:text-emerald-400 hover:bg-emerald-500/10 rounded-lg border border-matrix-border hover:border-emerald-500/30 transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                          title="Attach to Incident"
                        >
                          <Plus className="h-4 w-4" />
                        </button>
                        <div className="p-1 text-slate-500 hover:text-white">
                          {expandedDocId === doc.id ? (
                            <ChevronUp className="h-4 w-4 text-emerald-400" />
                          ) : (
                            <ChevronDown className="h-4 w-4" />
                          )}
                        </div>
                      </div>
                    </div>

                    {expandedDocId === doc.id && (
                      <div className="p-5 bg-matrix-surface/80 border-t border-matrix-border/80 text-xs animate-in fade-in duration-200">
                        {loadingDocId === doc.id ? (
                          <div className="flex items-center gap-2 text-slate-400 py-6 justify-center font-mono">
                            <RefreshCw className="h-4 w-4 animate-spin text-emerald-400" />
                            <span>Loading preview...</span>
                          </div>
                        ) : docDetails[doc.id]?.chunks?.length ? (
                          <div className="space-y-4">
                            <div className="flex items-center justify-between pb-2.5 border-b border-matrix-border/60 text-[11px] font-mono text-slate-400">
                              <span className="flex items-center gap-2 text-emerald-400 font-semibold">
                                <BookOpen className="h-4 w-4" />
                                {docDetails[doc.id].chunks.length} Document Section(s) Indexed
                              </span>
                              <span className="text-[10px] text-slate-500 bg-matrix-card px-2 py-0.5 rounded border border-matrix-border">
                                Semantic pgvector (768-dim) Ready
                              </span>
                            </div>
                            {docDetails[doc.id].chunks.map((chunk: any) => (
                              <div key={chunk.id} className="p-4 rounded-xl bg-matrix-card/90 border border-matrix-border/80 space-y-2.5 shadow-sm">
                                {chunk.section_title && (
                                  <div className="font-semibold text-slate-100 text-xs font-mono flex items-center gap-2 border-b border-matrix-border/40 pb-2">
                                    <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-500/50"></span>
                                    <span>{chunk.section_title}</span>
                                    {chunk.page_number && (
                                      <span className="text-[10px] text-slate-500 font-normal ml-auto">Page {chunk.page_number}</span>
                                    )}
                                  </div>
                                )}
                                <pre className="text-xs text-slate-200 font-mono whitespace-pre-wrap leading-relaxed bg-black/40 p-3 rounded-lg border border-matrix-border/40 selection:bg-emerald-500/20">
                                  {chunk.content}
                                </pre>
                              </div>
                            ))}
                          </div>
                        ) : (
                          <div className="text-slate-500 italic py-4 text-center font-mono">No readable content found for this document.</div>
                        )}
                      </div>
                    )}
                  </div>
                ))
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
