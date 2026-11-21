import { useRef, useState } from 'react';
import {
  AlertCircle,
  BookOpen,
  Check,
  CheckCircle2,
  ChevronDown,
  FileText,
  FileUp,
  Loader2,
  RefreshCw,
  Trash2
} from 'lucide-react';

export default function KnowledgeBase({
  apiUrl,
  documents,
  onRefresh,
  selectedDocumentIds,
  onSelectedDocumentIdsChange,
  useRag,
  onToggleRag
}) {
  const fileInputRef = useRef(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState('');
  const [expandedDocIds, setExpandedDocIds] = useState(new Set());

  const readyDocuments = documents.filter((document) => document.status === 'ready');

  const handleUpload = async (event) => {
    const file = event.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setMessage('');

    const formData = new FormData();
    formData.append('file', file);

    try {
      const response = await fetch(`${apiUrl}/documents`, {
        method: 'POST',
        body: formData
      });
      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Upload failed');
      }

      await onRefresh();
      if (data.document?.status === 'ready') {
        onSelectedDocumentIdsChange((current) => [...new Set([...current, data.document.id])]);
        onToggleRag(true);
        setMessage(`${data.document.filename} is ready.`);
      } else {
        setMessage(data.document?.error || `${file.name} was uploaded but indexing failed.`);
      }
    } catch (error) {
      setMessage(error.message || 'Upload failed.');
    } finally {
      setUploading(false);
      event.target.value = '';
    }
  };

  const deleteDocument = async (documentId) => {
    try {
      await fetch(`${apiUrl}/documents/${documentId}`, {
        method: 'DELETE'
      });
      onSelectedDocumentIdsChange((current) => {
        const next = current.filter((id) => id !== documentId);
        if (next.length === 0) {
          onToggleRag(false);
        }
        return next;
      });
      await onRefresh();
    } catch (error) {
      setMessage('Failed to delete document.');
    }
  };

  const toggleExpanded = (documentId) => {
    setExpandedDocIds((current) => {
      const next = new Set(current);
      if (next.has(documentId)) {
        next.delete(documentId);
      } else {
        next.add(documentId);
      }
      return next;
    });
  };

  const toggleDocument = (documentId) => {
    onSelectedDocumentIdsChange((current) => {
      const next = current.includes(documentId)
        ? current.filter((id) => id !== documentId)
        : [...current, documentId];
      onToggleRag(next.length > 0);
      return next;
    });
  };

  return (
    <main className="h-full overflow-y-auto px-8 py-7">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-[#28ead8]/20 bg-[#20dcca]/10 px-3 py-1.5 text-xs text-[#8ffcf0]">
              <BookOpen className="h-3.5 w-3.5" />
              Local knowledge base
            </div>
            <h2 className="text-4xl font-semibold tracking-[-0.03em] text-white">Knowledge</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[#8da19c]">
              Upload PDF or TXT files and select the documents available to chat retrieval.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3">
            <button
              onClick={onRefresh}
              className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/[0.08] bg-white/[0.035] px-4 py-3 text-sm font-semibold text-[#cbdad6] transition hover:border-[#28ead8]/25 hover:text-[#8ffcf0]"
            >
              <RefreshCw className="h-4 w-4" />
              Refresh
            </button>
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
              className="inline-flex items-center justify-center gap-2 rounded-2xl bg-[#20dcca] px-4 py-3 text-sm font-semibold text-[#06211e] shadow-[0_18px_45px_rgba(32,220,202,0.18)] transition hover:bg-[#68f8ea] disabled:opacity-60"
            >
              {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <FileUp className="h-4 w-4" />}
              {uploading ? 'Indexing' : 'Upload document'}
            </button>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pdf,.txt,application/pdf,text/plain"
              onChange={handleUpload}
              className="hidden"
            />
          </div>
        </div>

        <div className="mb-6 grid gap-4 md:grid-cols-3">
          <StatCard icon={FileText} label="Documents" value={documents.length} />
          <StatCard icon={CheckCircle2} label="Ready" value={readyDocuments.length} />
          <StatCard icon={BookOpen} label="Selected" value={selectedDocumentIds.length} />
        </div>

        <div className="mb-5 flex items-center justify-between gap-4 rounded-3xl border border-white/[0.08] bg-[#07100f]/70 p-4 backdrop-blur-xl">
          <div>
            <div className="text-sm font-semibold text-white">Use selected documents in chat</div>
            <div className="mt-1 text-xs text-[#819690]">{selectedDocumentIds.length} selected</div>
          </div>
          <button
            onClick={() => onToggleRag(!useRag)}
            disabled={selectedDocumentIds.length === 0}
            className={`relative h-8 w-14 rounded-full transition disabled:cursor-not-allowed disabled:opacity-50 ${
              useRag ? 'bg-[#20dcca]' : 'bg-white/[0.12]'
            }`}
            title="Toggle knowledge retrieval"
          >
            <span
              className={`absolute top-1 h-6 w-6 rounded-full bg-white transition ${
                useRag ? 'left-7' : 'left-1'
              }`}
            />
          </button>
        </div>

        {message && (
          <div className="mb-5 flex items-start gap-3 rounded-2xl border border-[#28ead8]/14 bg-[#20dcca]/8 p-4 text-sm text-[#c8fffa]">
            <AlertCircle className="mt-0.5 h-4 w-4 flex-shrink-0" />
            <span>{message}</span>
          </div>
        )}

        {documents.length === 0 ? (
          <div className="rounded-3xl border border-white/[0.08] bg-[#07100f]/70 p-12 text-center">
            <FileText className="mx-auto mb-4 h-12 w-12 text-[#526862]" />
            <h3 className="text-lg font-semibold text-white">No documents yet</h3>
            <p className="mt-2 text-sm text-[#8da19c]">
              The first upload will create searchable chunks and embeddings locally.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 xl:grid-cols-2">
            {documents.map((document) => {
              const isReady = document.status === 'ready';
              const isSelected = selectedDocumentIds.includes(document.id);
              const isExpanded = expandedDocIds.has(document.id);
              const isPending = document.status === 'pending';
              const isIndexing = document.status === 'indexing';

              return (
                <article
                  key={document.id}
                  className={`rounded-3xl border bg-[#07100f]/72 shadow-[0_24px_70px_rgba(0,0,0,0.18)] backdrop-blur-xl transition ${
                    isSelected ? 'border-[#28ead8]/35' : 'border-white/[0.08]'
                  }`}
                >
                  <div className="p-5">
                    <div className="mb-5 flex items-start justify-between gap-4">
                      <div className="flex min-w-0 items-start gap-4">
                        <div className="grid h-12 w-12 flex-shrink-0 place-items-center rounded-2xl border border-[#28ead8]/18 bg-[#20dcca]/10 text-[#7ffff0]">
                          <FileText className="h-5 w-5" />
                        </div>
                        <div className="min-w-0">
                          <h3 className="truncate text-lg font-semibold text-white">{document.filename}</h3>
                          <div className="mt-1 flex flex-wrap items-center gap-2">
                            <span className={statusClass(document.status)}>{document.status}</span>
                            {isReady && (
                              <span className="rounded-full bg-white/[0.06] px-2 py-1 text-xs text-[#9fb1ad]">
                                {document.chunk_count} chunks
                              </span>
                            )}
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => deleteDocument(document.id)}
                        className="rounded-xl border border-white/[0.08] bg-white/[0.035] p-2 text-[#8da19c] transition hover:border-rose-400/25 hover:bg-rose-400/10 hover:text-rose-300"
                        title="Delete document"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>

                    {!isReady && !isPending && (
                      <ProcessingSteps status={document.status} chunkCount={document.chunk_count} />
                    )}

                    {document.error && (
                      <div className="mb-4 rounded-2xl border border-rose-400/20 bg-rose-400/8 p-3 text-sm text-rose-100">
                        {document.error}
                      </div>
                    )}

                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div className="text-xs text-[#667b76]">
                        Updated {formatDate(document.updated_at)}
                      </div>
                      <div className="flex items-center gap-2">
                        {isReady && (
                          <button
                            onClick={() => toggleExpanded(document.id)}
                            className="rounded-xl border border-white/[0.08] bg-white/[0.035] p-2 text-[#8da19c] transition hover:border-[#28ead8]/25 hover:bg-[#20dcca]/10 hover:text-[#8ffcf0]"
                            title="Toggle details"
                          >
                            <ChevronDown className={`h-4 w-4 transition ${isExpanded ? 'rotate-180' : ''}`} />
                          </button>
                        )}
                        <button
                          onClick={() => toggleDocument(document.id)}
                          disabled={!isReady}
                          className={`inline-flex items-center justify-center gap-2 rounded-2xl px-4 py-2.5 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${
                            isSelected
                              ? 'bg-[#20dcca] text-[#06211e]'
                              : 'border border-white/[0.08] bg-white/[0.035] text-[#cbdad6] hover:border-[#28ead8]/25 hover:text-[#8ffcf0]'
                          }`}
                        >
                          {isSelected && <Check className="h-4 w-4" />}
                          {isSelected ? 'Selected' : 'Select'}
                        </button>
                      </div>
                    </div>

                    {isExpanded && isReady && (
                      <div className="mt-4 space-y-3 rounded-2xl border border-white/[0.06] bg-white/[0.02] p-3">
                        <div>
                          <div className="text-xs text-[#667b76] mb-1">Chunk Count</div>
                          <div className="text-sm font-semibold text-[#dce9e5]">{document.chunk_count}</div>
                        </div>
                        <div>
                          <div className="text-xs text-[#667b76] mb-1">File Type</div>
                          <div className="text-sm font-semibold text-[#dce9e5]">{document.content_type}</div>
                        </div>
                        <div>
                          <div className="text-xs text-[#667b76] mb-1">Created</div>
                          <div className="text-sm font-semibold text-[#dce9e5]">{formatDate(document.created_at)}</div>
                        </div>
                      </div>
                    )}
                  </div>
                </article>
              );
            })}
          </div>
        )}
      </div>
    </main>
  );
}

function StatCard({ icon: Icon, label, value }) {
  return (
    <div className="rounded-3xl border border-white/[0.08] bg-[#07100f]/70 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.16)] backdrop-blur-xl">
      <div className="mb-4 grid h-10 w-10 place-items-center rounded-2xl bg-[#20dcca]/10 text-[#7ffff0]">
        <Icon className="h-5 w-5" />
      </div>
      <div className="text-3xl font-semibold text-white">{value}</div>
      <div className="mt-1 text-sm text-[#819690]">{label}</div>
    </div>
  );
}

function ProcessingSteps({ status, chunkCount }) {
  const steps = [
    { label: 'Extracting', key: 'extracting', icon: '📄' },
    { label: 'Chunking', key: 'chunking', icon: '✂️' },
    { label: 'Embedding', key: 'embedding', icon: '🔢' }
  ];

  const isComplete = status === 'ready' || status === 'failed';
  const isIndexing = status === 'indexing';

  return (
    <div className="mb-4 space-y-2">
      <div className="text-xs font-semibold text-[#667b76] uppercase tracking-[0.1em]">Processing Steps</div>
      <div className="space-y-1.5">
        {steps.map((step, idx) => (
          <div key={step.key} className="flex items-center gap-2">
            <div
              className={`flex-shrink-0 h-5 w-5 rounded-full flex items-center justify-center text-xs ${
                isIndexing
                  ? 'bg-amber-400/20 text-amber-300'
                  : isComplete
                  ? 'bg-emerald-400/20 text-emerald-300'
                  : 'bg-white/[0.06] text-[#667b76]'
              }`}
            >
              {isIndexing && idx === 0 ? (
                <Loader2 className="h-3 w-3 animate-spin" />
              ) : isComplete || (isIndexing && idx < 2) ? (
                '✓'
              ) : (
                '-'
              )}
            </div>
            <span className="text-xs text-[#9fb1ad]">{step.label}</span>
          </div>
        ))}
      </div>
      {isIndexing && chunkCount && (
        <div className="mt-2 text-xs text-[#667b76]">Created {chunkCount} chunks</div>
      )}
    </div>
  );
}

function statusClass(status) {
  if (status === 'ready') {
    return 'rounded-full bg-emerald-400/10 px-2 py-1 text-xs text-emerald-200';
  }
  if (status === 'failed') {
    return 'rounded-full bg-rose-400/10 px-2 py-1 text-xs text-rose-200';
  }
  return 'rounded-full bg-amber-300/10 px-2 py-1 text-xs text-amber-100';
}

function formatDate(dateString) {
  if (!dateString) return 'Unknown';
  return new Date(dateString).toLocaleString();
}
