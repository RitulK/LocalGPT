import { useEffect, useState } from 'react';
import { Brain, Code2, MessageCircle, RotateCcw, Route, Save, SlidersHorizontal } from 'lucide-react';

const defaults = {
  default_general_model: '',
  default_coding_model: '',
  default_reasoning_model: '',
  router_enabled: true
};

export default function SettingsPanel({ settings, onUpdateSettings, models, apiUrl }) {
  const [localSettings, setLocalSettings] = useState({ ...defaults, ...settings });
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    setLocalSettings({ ...defaults, ...settings });
  }, [settings]);

  const handleSave = async () => {
    try {
      const response = await fetch(`${apiUrl}/settings`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(localSettings)
      });

      if (response.ok) {
        const data = await response.json();
        onUpdateSettings(data.settings || localSettings);
        setSaved(true);
        setTimeout(() => setSaved(false), 1800);
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
    }
  };

  const handleReset = () => {
    const firstModel = models[0]?.name || '';
    setLocalSettings({
      default_general_model: firstModel,
      default_coding_model: models.find((model) => model.name.toLowerCase().includes('coder'))?.name || firstModel,
      default_reasoning_model: firstModel,
      router_enabled: true
    });
  };

  return (
    <main className="h-full overflow-y-auto px-8 py-7">
      <div className="mx-auto max-w-5xl">
        <div className="mb-8">
          <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-[#28ead8]/20 bg-[#20dcca]/10 px-3 py-1.5 text-xs text-[#8ffcf0]">
            <SlidersHorizontal className="h-3.5 w-3.5" />
            Workspace preferences
          </div>
          <h2 className="text-4xl font-semibold tracking-[-0.03em] text-white">Settings</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-[#8da19c]">
            Configure routing behavior and default model roles. These settings are now stored in SQLite.
          </p>
        </div>

        <div className="grid gap-5 lg:grid-cols-[1fr_360px]">
          <section className="space-y-5">
            <div className="rounded-3xl border border-white/[0.08] bg-[#07100f]/72 p-6 shadow-[0_24px_70px_rgba(0,0,0,0.18)] backdrop-blur-xl">
              <div className="mb-5 flex items-center justify-between gap-4">
                <div>
                  <h3 className="text-lg font-semibold text-white">Smart router</h3>
                  <p className="mt-1 text-sm text-[#819690]">Let LocalGPT pick a model based on the prompt type.</p>
                </div>
                <button
                  onClick={() => setLocalSettings({
                    ...localSettings,
                    router_enabled: !localSettings.router_enabled
                  })}
                  className={`relative h-8 w-14 rounded-full transition ${
                    localSettings.router_enabled ? 'bg-[#20dcca]' : 'bg-white/[0.12]'
                  }`}
                  title="Toggle router"
                >
                  <span
                    className={`absolute top-1 h-6 w-6 rounded-full bg-white transition ${
                      localSettings.router_enabled ? 'left-7' : 'left-1'
                    }`}
                  />
                </button>
              </div>
              <div className="grid gap-3 md:grid-cols-3">
                <Role icon={Code2} label="Coding" text="Debugging and implementation prompts." />
                <Role icon={Brain} label="Reasoning" text="Analysis, planning, and explanations." />
                <Role icon={MessageCircle} label="General" text="Everyday chat and lightweight tasks." />
              </div>
            </div>

            <div className="rounded-3xl border border-white/[0.08] bg-[#07100f]/72 p-6 shadow-[0_24px_70px_rgba(0,0,0,0.18)] backdrop-blur-xl">
              <h3 className="text-lg font-semibold text-white">Default model roles</h3>
              <p className="mt-1 text-sm text-[#819690]">Choose which installed models should be preferred by each route.</p>

              <div className="mt-5 grid gap-4">
                <ModelSelect
                  label="General conversations"
                  value={localSettings.default_general_model || ''}
                  models={models}
                  onChange={(value) => setLocalSettings({ ...localSettings, default_general_model: value })}
                />
                <ModelSelect
                  label="Coding and debugging"
                  value={localSettings.default_coding_model || ''}
                  models={models}
                  onChange={(value) => setLocalSettings({ ...localSettings, default_coding_model: value })}
                />
                <ModelSelect
                  label="Reasoning and analysis"
                  value={localSettings.default_reasoning_model || ''}
                  models={models}
                  onChange={(value) => setLocalSettings({ ...localSettings, default_reasoning_model: value })}
                />
              </div>
            </div>
          </section>

          <aside className="rounded-3xl border border-white/[0.08] bg-[#07100f]/72 p-6 shadow-[0_24px_70px_rgba(0,0,0,0.18)] backdrop-blur-xl">
            <div className="mb-5 grid h-12 w-12 place-items-center rounded-2xl bg-[#20dcca]/10 text-[#7ffff0]">
              <Route className="h-5 w-5" />
            </div>
            <h3 className="text-lg font-semibold text-white">Routing logic</h3>
            <p className="mt-2 text-sm leading-6 text-[#819690]">
              The router scores prompts for coding, debugging, writing, translation, Q&A, reasoning, and general chat.
            </p>
            <div className="mt-5 space-y-3 text-sm text-[#cbdad6]">
              <LogicItem text="Code keywords and snippets route to coding models." />
              <LogicItem text="Analytical prompts route to reasoning-capable models." />
              <LogicItem text="Short everyday prompts prefer faster general models." />
            </div>

            <div className="mt-8 flex flex-col gap-3">
              <button
                onClick={handleSave}
                className="inline-flex items-center justify-center gap-2 rounded-2xl bg-[#20dcca] px-4 py-3 text-sm font-semibold text-[#06211e] shadow-[0_18px_45px_rgba(32,220,202,0.18)] transition hover:bg-[#68f8ea]"
              >
                <Save className="h-4 w-4" />
                {saved ? 'Saved' : 'Save settings'}
              </button>
              <button
                onClick={handleReset}
                className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/[0.08] bg-white/[0.035] px-4 py-3 text-sm font-semibold text-[#cbdad6] transition hover:border-[#28ead8]/25 hover:text-[#8ffcf0]"
              >
                <RotateCcw className="h-4 w-4" />
                Reset defaults
              </button>
            </div>
          </aside>
        </div>
      </div>
    </main>
  );
}

function Role({ icon: Icon, label, text }) {
  return (
    <div className="rounded-2xl border border-white/[0.06] bg-white/[0.03] p-4">
      <Icon className="mb-3 h-5 w-5 text-[#70fff0]" />
      <div className="text-sm font-semibold text-white">{label}</div>
      <div className="mt-1 text-xs leading-5 text-[#819690]">{text}</div>
    </div>
  );
}

function ModelSelect({ label, value, models, onChange }) {
  return (
    <label className="block">
      <span className="mb-2 block text-sm font-medium text-[#dce9e5]">{label}</span>
      <select
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="h-12 w-full rounded-2xl border border-white/[0.08] bg-[#0b1716] px-4 text-sm text-white outline-none transition focus:border-[#28ead8]/35"
      >
        <option value="">Select a model</option>
        {models.map((model) => (
          <option key={model.name} value={model.name}>
            {model.name}
          </option>
        ))}
      </select>
    </label>
  );
}

function LogicItem({ text }) {
  return (
    <div className="flex gap-3 rounded-2xl border border-white/[0.06] bg-white/[0.03] p-3">
      <span className="mt-1 h-2 w-2 flex-shrink-0 rounded-full bg-[#20dcca]" />
      <span>{text}</span>
    </div>
  );
}
