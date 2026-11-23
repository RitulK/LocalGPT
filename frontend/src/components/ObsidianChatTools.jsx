import { useEffect, useRef, useState } from 'react';
import {
  ExternalLink,
  FilePlus2,
  FolderOpen,
  PencilLine,
  Search,
  Trash2,
  X
} from 'lucide-react';

export const OBSIDIAN_TOOLS = [
  { id: 'new_note', label: 'Add a new note', icon: FilePlus2 },
  { id: 'search', label: 'Search vault', icon: Search },
  { id: 'read', label: 'Read/open note', icon: FolderOpen },
  { id: 'append', label: 'Append to note', icon: PencilLine },
  { id: 'edit', label: 'Edit note section', icon: PencilLine },
  { id: 'replace', label: 'Replace note', icon: FolderOpen },
  { id: 'delete', label: 'Delete note', icon: Trash2 }
];

export function ObsidianToolMenu({ open, onClose, onSelect }) {
  const ref = useRef(null);

  useEffect(() => {
    const close = (event) => {
      if (ref.current && !ref.current.contains(event.target)) onClose();
    };
    document.addEventListener('pointerdown', close);
    return () => document.removeEventListener('pointerdown', close);
  }, [onClose]);

  if (!open) return null;
  return (
    <div ref={ref} className="absolute bottom-[calc(100%+10px)] left-0 z-50 w-[280px] rounded-2xl border border-[#28ead8]/20 bg-[#07100f] p-1.5 shadow-2xl">
      {OBSIDIAN_TOOLS.map(({ id, label, icon: Icon }) => (
        <button
          key={id}
          type="button"
          onClick={() => onSelect(id)}
          className="flex w-full items-center gap-3 rounded-xl px-3 py-2.5 text-left text-sm text-[#c8d8d4] transition hover:bg-[#20dcca]/10 hover:text-[#8ffcf0]"
        >
          <Icon className="h-4 w-4 text-[#71fff1]" />
          {label}
        </button>
      ))}
    </div>
  );
}

export function ObsidianDraftCard({ draft, onChangeDraft, onConfirm, onCancel, busy }) {
  const [editing, setEditing] = useState(false);
  if (!draft) return null;

  const updateContent = (content) => onChangeDraft({ ...draft, content });
  return (
    <div className="mb-3 rounded-2xl border border-amber-300/20 bg-amber-300/[0.06] p-4">
      <div className="mb-2 flex items-start justify-between gap-3">
        <div>
          <div className="text-sm font-semibold text-amber-100">
            {draft.action === 'delete' ? 'Confirm note deletion' : 'Review generated Obsidian change'}
          </div>
          <div className="mt-1 font-mono text-xs text-[#aabcb7]">{draft.path}</div>
          {draft.section && <div className="mt-1 text-xs text-[#aabcb7]">Section: {draft.section}</div>}
        </div>
        <button type="button" onClick={onCancel} className="rounded-lg p-1 text-[#91a49f] hover:bg-white/[0.06]">
          <X className="h-4 w-4" />
        </button>
      </div>

      {editing ? (
        <textarea
          value={draft.content || ''}
          onChange={(event) => updateContent(event.target.value)}
          rows={10}
          className="mt-3 w-full resize-y rounded-xl border border-white/[0.08] bg-[#07100f] px-3 py-3 font-mono text-xs text-[#e3eeeb] outline-none focus:border-[#28ead8]/30"
        />
      ) : (
        draft.content && (
          <pre className="mt-3 max-h-64 overflow-auto whitespace-pre-wrap rounded-xl bg-black/25 p-3 font-mono text-xs text-[#dce9e5]">
            {draft.content}
          </pre>
        )
      )}

      <div className="mt-4 flex flex-wrap gap-2">
        {draft.action !== 'delete' && (
          <button
            type="button"
            onClick={() => setEditing((value) => !value)}
            className="rounded-xl border border-white/[0.08] px-3 py-2 text-sm text-[#b9c9c5]"
          >
            {editing ? 'Preview' : 'Edit draft'}
          </button>
        )}
        <button
          type="button"
          onClick={onConfirm}
          disabled={busy}
          className="rounded-xl bg-[#20dcca] px-3 py-2 text-sm font-semibold text-[#06211e] disabled:opacity-50"
        >
          {draft.action === 'delete' ? 'Confirm delete' : 'Confirm'}
        </button>
        <button type="button" onClick={onCancel} className="rounded-xl border border-white/[0.08] px-3 py-2 text-sm text-[#b9c9c5]">
          Cancel
        </button>
      </div>
    </div>
  );
}

export function OpenInObsidianButton({ apiUrl, path, onError }) {
  const open = async () => {
    try {
      const response = await fetch(`${apiUrl}/obsidian/execute`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: 'open', path })
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) throw new Error(data.detail || 'Could not open in Obsidian');
    } catch (error) {
      onError?.(error.message);
    }
  };
  return (
    <button type="button" onClick={open} className="mt-3 inline-flex items-center gap-2 rounded-xl border border-[#28ead8]/20 bg-[#20dcca]/10 px-3 py-2 text-xs font-semibold text-[#8ffcf0]">
      <ExternalLink className="h-3.5 w-3.5" />
      Open in Obsidian
    </button>
  );
}
