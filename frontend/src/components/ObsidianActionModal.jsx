import { useEffect, useState } from 'react';
import { Check, ExternalLink, FilePlus2, FolderOpen, PencilLine, Search, Trash2, X } from 'lucide-react';

const actions = [
  { id: 'search', label: 'Search', icon: Search },
  { id: 'open', label: 'Open', icon: ExternalLink },
  { id: 'create', label: 'Create', icon: FilePlus2 },
  { id: 'append', label: 'Append', icon: FolderOpen },
  { id: 'edit', label: 'Edit section', icon: PencilLine },
  { id: 'replace', label: 'Replace', icon: PencilLine },
  { id: 'delete', label: 'Delete', icon: Trash2 }
];

export default function ObsidianActionModal({ apiUrl, initialContent = '', onClose, onComplete }) {
  const [action, setAction] = useState('search');
  const [query, setQuery] = useState('');
  const [path, setPath] = useState('');
  const [section, setSection] = useState('');
  const [content, setContent] = useState(initialContent);
  const [proposal, setProposal] = useState(null);
  const [results, setResults] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');

  useEffect(() => {
    setContent(initialContent);
  }, [initialContent]);

  const plan = async () => {
    setBusy(true);
    setError('');
    setProposal(null);
    setResults(null);
    try {
      const body = { action, query: query || undefined, path: path || undefined, section: section || undefined, content: content || undefined };
      const response = await fetch(`${apiUrl}/obsidian/plan`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Could not create an action proposal');

      if (action === 'search') {
        const executeResponse = await fetch(`${apiUrl}/obsidian/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data.proposal)
        });
        const executeData = await executeResponse.json();
        if (!executeResponse.ok) throw new Error(executeData.detail || 'Search failed');
        setResults(executeData.results || []);
      } else if (action === 'open') {
        const executeResponse = await fetch(`${apiUrl}/obsidian/execute`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data.proposal)
        });
        const executeData = await executeResponse.json();
        if (!executeResponse.ok) throw new Error(executeData.detail || 'Could not open the note');
        onComplete(`Opened **${executeData.path}** in Obsidian.`);
      } else {
        setProposal(data.proposal);
      }
    } catch (planError) {
      setError(planError.message);
    } finally {
      setBusy(false);
    }
  };

  const confirm = async () => {
    if (!proposal) return;
    setBusy(true);
    setError('');
    try {
      const response = await fetch(`${apiUrl}/obsidian/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(proposal)
      });
      const data = await response.json();
      if (!response.ok) throw new Error(data.detail || 'Obsidian action failed');
      onComplete(`Obsidian ${proposal.action} completed for **${proposal.path}**.`);
    } catch (executeError) {
      setError(executeError.message);
    } finally {
      setBusy(false);
    }
  };

  const openNote = async (notePath) => {
    try {
      const response = await fetch(`${apiUrl}/obsidian/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'open', path: notePath })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data.detail || 'Could not open the note in Obsidian');
      }
    } catch (openError) {
      setError(openError.message);
    }
  };

  return (
    <div className="fixed inset-0 z-[100] grid place-items-center bg-black/60 p-4 backdrop-blur-sm" role="dialog" aria-modal="true">
      <div className="w-full max-w-2xl rounded-3xl border border-[#28ead8]/18 bg-[#07100f] shadow-[0_30px_100px_rgba(0,0,0,0.65)]">
        <div className="flex items-center justify-between border-b border-white/[0.07] px-5 py-4">
          <div>
            <h3 className="font-semibold text-white">Obsidian action</h3>
            <p className="mt-1 text-xs text-[#819690]">Actions are reviewed before writes and deletes.</p>
          </div>
          <button onClick={onClose} className="rounded-xl p-2 text-[#8da19c] hover:bg-white/[0.06] hover:text-white" aria-label="Close">
            <X className="h-4 w-4" />
          </button>
        </div>

        <div className="max-h-[70vh] overflow-y-auto p-5">
          <div className="mb-5 flex flex-wrap gap-2">
            {actions.map(({ id, label, icon: Icon }) => (
              <button
                key={id}
                onClick={() => { setAction(id); setProposal(null); setResults(null); setError(''); }}
                className={`inline-flex items-center gap-2 rounded-xl border px-3 py-2 text-sm ${
                  action === id
                    ? 'border-[#28ead8]/25 bg-[#20dcca]/12 text-[#8ffcf0]'
                    : 'border-white/[0.08] bg-white/[0.03] text-[#a9bbb6]'
                }`}
              >
                <Icon className="h-3.5 w-3.5" />
                {label}
              </button>
            ))}
          </div>

          {action === 'search' ? (
            <label className="block text-sm text-[#b9c9c5]">
              Search query
              <input
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="mt-2 w-full rounded-xl border border-white/[0.08] bg-[#0b1716] px-3 py-2.5 text-white outline-none focus:border-[#28ead8]/35"
                placeholder="SQLite"
              />
            </label>
          ) : (
            <div className="space-y-4">
              <label className="block text-sm text-[#b9c9c5]">
                Note path
                <input
                  value={path}
                  onChange={(e) => setPath(e.target.value)}
                  className="mt-2 w-full rounded-xl border border-white/[0.08] bg-[#0b1716] px-3 py-2.5 text-white outline-none focus:border-[#28ead8]/35"
                  placeholder="BuddyAI/Meeting Notes.md"
                />
              </label>
              {['append', 'edit'].includes(action) && (
                <label className="block text-sm text-[#b9c9c5]">
                  Heading section (for edit/section append)
                  <input
                    value={section}
                    onChange={(e) => setSection(e.target.value)}
                    className="mt-2 w-full rounded-xl border border-white/[0.08] bg-[#0b1716] px-3 py-2.5 text-white outline-none focus:border-[#28ead8]/35"
                    placeholder="Decisions"
                  />
                </label>
              )}
              {action !== 'open' && action !== 'delete' && (
                <label className="block text-sm text-[#b9c9c5]">
                  {action === 'replace' ? 'Complete replacement Markdown' : 'Markdown content'}
                  <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    rows={8}
                    className="mt-2 w-full resize-y rounded-xl border border-white/[0.08] bg-[#0b1716] px-3 py-3 text-sm text-white outline-none focus:border-[#28ead8]/35"
                  />
                </label>
              )}
            </div>
          )}

          {error && <div className="mt-4 rounded-xl border border-rose-400/20 bg-rose-400/8 px-3 py-2.5 text-sm text-rose-200">{error}</div>}

          {results && (
            <div className="mt-5 space-y-2">
              {results.length === 0 && <div className="text-sm text-[#819690]">No matching notes found.</div>}
              {results.map((result, index) => {
                const filename = typeof result === 'string' ? result : result.filename || result.path;
                const snippet = typeof result === 'object' ? result.matches?.[0]?.context || result.snippet : '';
                return (
                  <div key={`${filename}-${index}`} className="rounded-xl border border-white/[0.07] bg-[#0b1716] p-3">
                    <div className="flex items-center justify-between gap-3">
                      <div className="min-w-0">
                        <div className="truncate text-sm font-medium text-white">{filename}</div>
                        {snippet && <div className="mt-1 line-clamp-2 text-xs text-[#91a49f]">{snippet}</div>}
                      </div>
                      <button onClick={() => openNote(filename)} className="shrink-0 rounded-lg border border-[#28ead8]/20 px-2.5 py-1.5 text-xs text-[#8ffcf0]">
                        Open
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          {proposal && (
            <div className="mt-5 rounded-2xl border border-amber-300/20 bg-amber-300/[0.06] p-4">
              <div className="mb-3 text-sm font-semibold text-amber-100">
                {proposal.action === 'delete' ? 'Confirm deletion' : 'Review proposed change'}
              </div>
              <div className="space-y-1 font-mono text-xs text-[#cddbd7]">
                <div>Action: {proposal.action}</div>
                <div>Path: {proposal.path}</div>
                {proposal.section && <div>Section: {proposal.section}</div>}
              </div>
              {proposal.content && (
                <pre className="mt-3 max-h-52 overflow-auto whitespace-pre-wrap rounded-xl bg-black/25 p-3 text-xs text-[#dce9e5]">{proposal.content}</pre>
              )}
              <div className="mt-4 flex gap-2">
                <button
                  onClick={confirm}
                  disabled={busy}
                  className="inline-flex items-center gap-2 rounded-xl bg-[#20dcca] px-3 py-2 text-sm font-semibold text-[#06211e] disabled:opacity-50"
                >
                  <Check className="h-4 w-4" />
                  {proposal.action === 'delete' ? 'Confirm delete' : 'Confirm'}
                </button>
                <button onClick={() => setProposal(null)} className="rounded-xl border border-white/[0.08] px-3 py-2 text-sm text-[#b9c9c5]">Edit proposal</button>
                <button onClick={onClose} className="rounded-xl border border-white/[0.08] px-3 py-2 text-sm text-[#b9c9c5]">Cancel</button>
              </div>
            </div>
          )}
        </div>

        {!proposal && !results && (
          <div className="flex justify-end border-t border-white/[0.07] px-5 py-4">
            <button
              onClick={plan}
              disabled={busy || (action === 'search' && !query.trim())}
              className="rounded-xl bg-[#20dcca] px-4 py-2.5 text-sm font-semibold text-[#06211e] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {action === 'search' ? 'Search vault' : action === 'open' ? 'Open in Obsidian' : 'Create review'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
