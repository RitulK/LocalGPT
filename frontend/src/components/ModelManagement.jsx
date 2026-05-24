import { useMemo, useState } from 'react';
import {
  CheckCircle2,
  Cpu,
  Database,
  HardDrive,
  RefreshCw,
  Search,
  Sparkles,
  Terminal
} from 'lucide-react';

export default function ModelManagement({ models, onRefresh, selectedModel, onSelectModel }) {
  const [refreshing, setRefreshing] = useState(false);
  const [query, setQuery] = useState('');

  const totalSize = useMemo(
    () => models.reduce((acc, model) => acc + (model.size || 0), 0),
    [models]
  );

  const filteredModels = models.filter((model) =>
    model.name.toLowerCase().includes(query.toLowerCase())
  );

  const handleRefresh = async () => {
    setRefreshing(true);
    await onRefresh();
    setTimeout(() => setRefreshing(false), 500);
  };

  const formatBytes = (bytes) => {
    if (!bytes) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return `${Math.round((bytes / Math.pow(k, i)) * 100) / 100} ${sizes[i]}`;
  };

  const formatDate = (dateString) => {
    if (!dateString) return 'Unknown';
    return new Date(dateString).toLocaleString();
  };

  const getModelType = (name) => {
    const lower = name.toLowerCase();
    if (lower.includes('coder') || lower.includes('code')) return 'Coding';
    if (lower.includes('embed')) return 'Embedding';
    if (lower.includes('llava') || lower.includes('vision')) return 'Vision';
    return 'Chat';
  };

  return (
    <main className="h-full overflow-y-auto px-8 py-7">
      <div className="mx-auto max-w-7xl">
        <div className="mb-8 flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
          <div>
            <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-[#28ead8]/20 bg-[#20dcca]/10 px-3 py-1.5 text-xs text-[#8ffcf0]">
              <Database className="h-3.5 w-3.5" />
              Ollama model catalogue
            </div>
            <h2 className="text-4xl font-semibold tracking-[-0.03em] text-white">Models</h2>
            <p className="mt-2 max-w-2xl text-sm leading-6 text-[#8da19c]">
              Browse installed local models, inspect storage usage, and choose a default model for manual chat.
            </p>
          </div>
          <button
            onClick={handleRefresh}
            disabled={refreshing}
            className="inline-flex items-center justify-center gap-2 rounded-2xl bg-[#20dcca] px-4 py-3 text-sm font-semibold text-[#06211e] shadow-[0_18px_45px_rgba(32,220,202,0.18)] transition hover:bg-[#68f8ea] disabled:opacity-60"
          >
            <RefreshCw className={`h-4 w-4 ${refreshing ? 'animate-spin' : ''}`} />
            Refresh catalogue
          </button>
        </div>

        <div className="mb-6 grid gap-4 md:grid-cols-3">
          <StatCard icon={Database} label="Installed models" value={models.length} />
          <StatCard icon={HardDrive} label="Local storage" value={formatBytes(totalSize)} />
          <StatCard icon={Sparkles} label="Selected" value={selectedModel === 'auto' ? 'Auto router' : selectedModel || 'None'} compact />
        </div>

        <div className="mb-5 flex flex-col gap-3 rounded-3xl border border-white/[0.08] bg-[#07100f]/70 p-4 backdrop-blur-xl md:flex-row md:items-center md:justify-between">
          <div className="relative flex-1">
            <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-[#6f8580]" />
            <input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search models..."
              className="h-11 w-full rounded-2xl border border-white/[0.08] bg-[#0b1716] pl-10 pr-4 text-sm text-white outline-none transition placeholder:text-[#60756f] focus:border-[#28ead8]/35"
            />
          </div>
          <div className="flex items-center gap-2 rounded-2xl border border-white/[0.08] bg-white/[0.035] px-3 py-2 text-xs text-[#8da19c]">
            <Terminal className="h-4 w-4 text-[#55f3df]" />
            ollama list
          </div>
        </div>

        {filteredModels.length === 0 ? (
          <div className="rounded-3xl border border-white/[0.08] bg-[#07100f]/70 p-12 text-center">
            <Database className="mx-auto mb-4 h-12 w-12 text-[#526862]" />
            <h3 className="text-lg font-semibold text-white">No models found</h3>
            <p className="mt-2 text-sm text-[#8da19c]">
              Install one with <code className="rounded bg-black/35 px-2 py-1 text-[#8ffcf0]">ollama pull llama3.2</code>.
            </p>
          </div>
        ) : (
          <div className="grid gap-4 xl:grid-cols-2">
            {filteredModels.map((model) => {
              const isSelected = selectedModel === model.name;
              const type = getModelType(model.name);

              return (
                <article
                  key={model.name}
                  className={`group rounded-3xl border bg-[#07100f]/72 p-5 shadow-[0_24px_70px_rgba(0,0,0,0.18)] backdrop-blur-xl transition hover:-translate-y-0.5 hover:border-[#28ead8]/24 ${
                    isSelected ? 'border-[#28ead8]/35' : 'border-white/[0.08]'
                  }`}
                >
                  <div className="mb-5 flex items-start justify-between gap-4">
                    <div className="flex items-start gap-4">
                      <div className="grid h-12 w-12 place-items-center rounded-2xl border border-[#28ead8]/18 bg-[#20dcca]/10 text-[#7ffff0]">
                        <Cpu className="h-5 w-5" />
                      </div>
                      <div>
                        <h3 className="text-lg font-semibold text-white">{model.name}</h3>
                        <div className="mt-1 flex flex-wrap items-center gap-2">
                          <span className="rounded-full bg-white/[0.06] px-2 py-1 text-xs text-[#9fb1ad]">{type}</span>
                          <span className="rounded-full bg-emerald-400/10 px-2 py-1 text-xs text-emerald-200">Available</span>
                          {isSelected && (
                            <span className="rounded-full bg-[#20dcca]/12 px-2 py-1 text-xs text-[#8ffcf0]">Selected</span>
                          )}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => onSelectModel(model.name)}
                      className={`rounded-xl px-3 py-2 text-xs font-semibold transition ${
                        isSelected
                          ? 'bg-[#20dcca] text-[#06211e]'
                          : 'border border-white/[0.08] bg-white/[0.035] text-[#9fb1ad] hover:border-[#28ead8]/28 hover:text-[#8ffcf0]'
                      }`}
                    >
                      {isSelected ? 'In use' : 'Use model'}
                    </button>
                  </div>

                  <div className="grid gap-3 sm:grid-cols-3">
                    <Metric label="Size" value={formatBytes(model.size)} />
                    <Metric label="Modified" value={formatDate(model.modified_at)} />
                    <Metric label="Digest" value={model.digest ? `${model.digest.slice(0, 12)}...` : 'Unknown'} mono />
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

function StatCard({ icon: Icon, label, value, compact = false }) {
  return (
    <div className="rounded-3xl border border-white/[0.08] bg-[#07100f]/70 p-5 shadow-[0_20px_60px_rgba(0,0,0,0.16)] backdrop-blur-xl">
      <div className="mb-4 grid h-10 w-10 place-items-center rounded-2xl bg-[#20dcca]/10 text-[#7ffff0]">
        <Icon className="h-5 w-5" />
      </div>
      <div className={`font-semibold text-white ${compact ? 'truncate text-xl' : 'text-3xl'}`}>{value}</div>
      <div className="mt-1 text-sm text-[#819690]">{label}</div>
    </div>
  );
}

function Metric({ label, value, mono = false }) {
  return (
    <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] p-3">
      <div className="text-xs text-[#667b76]">{label}</div>
      <div className={`mt-1 truncate text-sm text-[#dce9e5] ${mono ? 'font-mono' : 'font-medium'}`}>{value}</div>
    </div>
  );
}
