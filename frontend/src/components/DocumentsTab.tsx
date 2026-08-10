import React, { useState, useEffect } from 'react';
import { Upload, CheckCircle, XCircle, FileText, Plus, RefreshCw, File } from 'lucide-react';
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
        <h2 className="text-xl font-semibold text-zinc-100 flex items-center gap-2">
          <FileText className="h-5 w-5 text-indigo-400" />
          Documents
        </h2>
        <div className="flex items-center gap-3">
          <button
            onClick={fetchDocs}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-zinc-300 hover:text-white bg-zinc-800 hover:bg-zinc-700 rounded-md transition-colors border border-zinc-700"
          >
            <RefreshCw className="h-4 w-4" />
            Refresh
          </button>
          <button
            onClick={seedDemo}
            className="flex items-center gap-2 px-3 py-1.5 text-sm font-medium text-indigo-300 hover:text-white bg-indigo-900/30 hover:bg-indigo-800/50 rounded-md transition-colors border border-indigo-700/50"
          >
            Seed Demo Docs
          </button>
          <label className="flex items-center gap-2 px-4 py-1.5 text-sm font-medium text-white bg-indigo-600 hover:bg-indigo-700 rounded-md transition-colors cursor-pointer disabled:opacity-50">
            {uploading ? <RefreshCw className="h-4 w-4 animate-spin" /> : <Upload className="h-4 w-4" />}
            Upload Document
            <input type="file" hidden accept=".txt,.md,.pdf" onChange={handleFileUpload} disabled={uploading} />
          </label>
        </div>
      </div>

      {loading ? (
        <div className="text-center py-8 text-zinc-500">Loading documents...</div>
      ) : (
        <div className="space-y-6">
          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-zinc-800 bg-zinc-900/80">
              <h3 className="text-sm font-medium text-zinc-100 uppercase tracking-wider">Attached to Incident</h3>
            </div>
            <div className="divide-y divide-zinc-800">
              {incidentDocs.length === 0 ? (
                <div className="p-6 text-center text-sm text-zinc-500 italic">
                  No documents attached to this incident.
                </div>
              ) : (
                incidentDocs.map((doc) => (
                  <div key={doc.id} className="p-4 flex items-center justify-between hover:bg-zinc-800/30 transition-colors">
                    <div className="flex items-center gap-3">
                      <File className="h-5 w-5 text-indigo-400" />
                      <div>
                        <div className="font-medium text-zinc-200">{doc.title}</div>
                        <div className="text-xs text-zinc-500 mt-1">ID: {doc.id}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-3">
                      <span className="text-xs font-medium px-2 py-1 bg-zinc-800 rounded border border-zinc-700 text-zinc-400">
                        {doc.type}
                      </span>
                      {doc.status === 'READY' ? (
                        <span className="flex items-center gap-1 text-xs font-medium px-2 py-1 bg-emerald-500/10 text-emerald-400 rounded border border-emerald-500/20">
                          <CheckCircle className="h-3.5 w-3.5" />
                          Ready
                        </span>
                      ) : doc.status === 'FAILED' ? (
                        <span className="flex items-center gap-1 text-xs font-medium px-2 py-1 bg-red-500/10 text-red-400 rounded border border-red-500/20">
                          <XCircle className="h-3.5 w-3.5" />
                          Failed
                        </span>
                      ) : (
                        <span className="flex items-center gap-1 text-xs font-medium px-2 py-1 bg-blue-500/10 text-blue-400 rounded border border-blue-500/20">
                          <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                          {doc.status}
                        </span>
                      )}
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          <div className="rounded-xl border border-zinc-800 bg-zinc-900/50 overflow-hidden shadow-sm">
            <div className="px-6 py-4 border-b border-zinc-800 bg-zinc-900/80">
              <h3 className="text-sm font-medium text-zinc-100 uppercase tracking-wider">Available Documents</h3>
            </div>
            <div className="divide-y divide-zinc-800 max-h-96 overflow-y-auto">
              {availableDocs.length === 0 ? (
                <div className="p-6 text-center text-sm text-zinc-500 italic">
                  No available documents to attach.
                </div>
              ) : (
                availableDocs.map((doc) => (
                  <div key={doc.id} className="p-4 flex items-center justify-between hover:bg-zinc-800/30 transition-colors">
                    <div className="flex items-center gap-3">
                      <File className="h-5 w-5 text-zinc-500" />
                      <div>
                        <div className="font-medium text-zinc-300">{doc.title}</div>
                        <div className="text-xs text-zinc-600 mt-1">ID: {doc.id}</div>
                      </div>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-medium px-2 py-1 bg-zinc-800 rounded border border-zinc-700 text-zinc-500">
                          {doc.type}
                        </span>
                        {doc.status === 'READY' ? (
                          <span className="flex items-center gap-1 text-xs font-medium px-2 py-1 text-emerald-500/70">
                            <CheckCircle className="h-3.5 w-3.5" />
                          </span>
                        ) : doc.status === 'FAILED' ? (
                          <span className="flex items-center gap-1 text-xs font-medium px-2 py-1 text-red-500/70">
                            <XCircle className="h-3.5 w-3.5" />
                          </span>
                        ) : (
                          <span className="flex items-center gap-1 text-xs font-medium px-2 py-1 text-blue-500/70">
                            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                          </span>
                        )}
                      </div>
                      <button
                        onClick={() => handleAssign(doc.id)}
                        disabled={doc.status !== 'READY'}
                        className="p-1.5 text-zinc-400 hover:text-indigo-400 hover:bg-indigo-500/10 rounded-md transition-colors disabled:opacity-30 disabled:cursor-not-allowed"
                        title="Attach to Incident"
                      >
                        <Plus className="h-5 w-5" />
                      </button>
                    </div>
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
