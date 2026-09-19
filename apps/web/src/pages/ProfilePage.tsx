import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowLeft, User as UserIcon, Code2, Download, Trash2 } from 'lucide-react';
import { useAuth } from '../store/AuthContext';
import { authApi, progressApi } from '../utils/api';
import { NotFound } from '../components/NotFound';

type Tab = 'profile' | 'language' | 'data' | 'danger';

export const ProfilePage: React.FC = () => {
  const { user, updateProfile, deleteAccount } = useAuth();
  const [tab, setTab] = useState<Tab>(() => {
    const q = new URLSearchParams(window.location.search).get('tab');
    return q === 'data' || q === 'danger' || q === 'language' ? q : 'profile';
  });

  const [name, setName] = useState('');
  const [nameMsg, setNameMsg] = useState<string | null>(null);
  const [lang, setLang] = useState<'javascript' | 'python'>('javascript');
  const [langMsg, setLangMsg] = useState<string | null>(null);
  const [dataMsg, setDataMsg] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);

  React.useEffect(() => {
    if (user) {
      setName(user.displayName || '');
    }
    progressApi
      .getSettings()
      .then((s) => {
        if (s.preferred_language === 'python' || s.preferred_language === 'javascript') {
          setLang(s.preferred_language);
        }
      })
      .catch(() => {});
  }, [user?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  if (!user) {
    return (
      <NotFound
        title="Sign in required"
        message="Your profile lives behind your account. Sign in to manage it."
        backTo="/login"
        backLabel="Sign in"
      />
    );
  }

  const tabs: { id: Tab; label: string }[] = [
    { id: 'profile', label: 'Profile' },
    { id: 'language', label: 'Language' },
    { id: 'data', label: 'Data' },
    { id: 'danger', label: 'Danger' },
  ];

  return (
    <div className="max-w-3xl mx-auto px-4 py-8 space-y-6">
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-[10px] font-mono text-muted">
        <Link to="/dashboard" className="hover:text-mint transition-colors">
          dashboard
        </Link>
        <span>/</span>
        <span className="text-ink">profile</span>
      </nav>

      <div className="flex items-center gap-3 pb-4 border-b border-line">
        <div className="w-10 h-10 rounded-xl border border-line bg-surface grid place-items-center text-mint">
          <UserIcon className="w-5 h-5" />
        </div>
        <div>
          <h1 className="text-xl font-bold text-ink">{user.displayName}</h1>
          <p className="text-xs font-mono text-muted">{user.email} · {user.role}</p>
        </div>
      </div>

      <div className="flex flex-wrap gap-1.5">
        {tabs.map((t) => (
          <button
            key={t.id}
            onClick={() => setTab(t.id)}
            className={`px-3 py-1.5 rounded-lg text-xs font-mono transition cursor-pointer border ${
              tab === t.id
                ? 'bg-mint text-canvas border-mint font-semibold'
                : 'bg-surface text-muted border-line hover:text-ink'
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'profile' && (
        <div className="space-y-5">
          <section className="p-5 rounded-xl border border-line bg-surface space-y-3">
            <h2 className="text-sm font-bold text-ink flex items-center gap-2">
              <UserIcon className="w-4 h-4 text-mint" /> Display name
            </h2>
            <form
              className="flex flex-wrap gap-2"
              onSubmit={async (e) => {
                e.preventDefault();
                setNameMsg(null);
                try {
                  await updateProfile(name.trim());
                  setNameMsg('Saved.');
                } catch (err) {
                  setNameMsg(err instanceof Error ? err.message : 'Could not save.');
                }
              }}
            >
              <input
                value={name}
                onChange={(e) => setName(e.target.value)}
                minLength={2}
                maxLength={50}
                aria-label="Display name"
                className="flex-1 min-w-40 px-3 py-2 rounded-lg bg-canvas border border-line text-sm text-ink focus:outline-none focus:border-mint"
              />
              <button type="submit" className="px-4 py-2 rounded-lg bg-mint text-canvas text-xs font-semibold hover:brightness-110 transition cursor-pointer">
                Save
              </button>
            </form>
            {nameMsg && <p className="text-xs font-mono text-muted">{nameMsg}</p>}
          </section>

        </div>
      )}

      {tab === 'language' && (
        <section className="p-5 rounded-xl border border-line bg-surface space-y-3">
          <h2 className="text-sm font-bold text-ink flex items-center gap-2">
            <Code2 className="w-4 h-4 text-mint" /> Preferred language
          </h2>
          <p className="text-xs text-muted">Used as the default in code runners (Python and JS supported).</p>
          <div className="flex gap-2">
            {(['javascript', 'python'] as const).map((l) => (
              <button
                key={l}
                onClick={async () => {
                  setLang(l);
                  setLangMsg(null);
                  try {
                    await progressApi.saveSettings({ preferred_language: l });
                    setLangMsg(`Default language: ${l}.`);
                  } catch {
                    setLangMsg('Could not save (offline?).');
                  }
                }}
                className={`px-4 py-2 rounded-lg border text-xs font-mono transition cursor-pointer ${
                  lang === l ? 'border-mint bg-mint/10 text-mint font-semibold' : 'border-line bg-canvas text-muted hover:text-ink'
                }`}
              >
                {l === 'javascript' ? 'JavaScript' : 'Python'}
              </button>
            ))}
          </div>
          {langMsg && <p className="text-xs font-mono text-muted">{langMsg}</p>}
        </section>
      )}

      {tab === 'data' && (
        <section className="p-5 rounded-xl border border-line bg-surface space-y-3">
          <h2 className="text-sm font-bold text-ink flex items-center gap-2">
            <Download className="w-4 h-4 text-mint" /> Export my data
          </h2>
          <p className="text-xs text-muted">Download everything stored for your account (progress, notes, submissions, attempts).</p>
          <button
            onClick={async () => {
              setDataMsg(null);
              try {
                const data = await authApi.exportData();
                const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' });
                const url = URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                a.download = 'merit-export.json';
                a.click();
                URL.revokeObjectURL(url);
                setDataMsg('Exported.');
              } catch {
                setDataMsg('Export failed.');
              }
            }}
            className="px-4 py-2 rounded-lg border border-line bg-canvas text-xs font-mono text-ink hover:border-mint transition cursor-pointer"
          >
            Download JSON
          </button>
          {dataMsg && <p className="text-xs font-mono text-muted">{dataMsg}</p>}
        </section>
      )}

      {tab === 'danger' && (
        <section className="p-5 rounded-xl border border-rose/40 bg-rose/5 space-y-3">
          <h2 className="text-sm font-bold text-rose flex items-center gap-2">
            <Trash2 className="w-4 h-4" /> Delete account
          </h2>
          <p className="text-xs text-muted">Permanently deletes your account and all associated data. This cannot be undone.</p>
          {!confirmDelete ? (
            <button
              onClick={() => setConfirmDelete(true)}
              className="px-4 py-2 rounded-lg border border-rose/40 text-rose text-xs font-semibold hover:bg-rose/10 transition cursor-pointer"
            >
              Delete my account…
            </button>
          ) : (
            <div className="flex flex-wrap gap-2">
              <button
                onClick={async () => {
                  await deleteAccount();
                  window.location.href = '/';
                }}
                className="px-4 py-2 rounded-lg bg-rose text-white text-xs font-semibold hover:brightness-110 transition cursor-pointer"
              >
                Yes, delete everything
              </button>
              <button
                onClick={() => setConfirmDelete(false)}
                className="px-4 py-2 rounded-lg border border-line text-xs text-muted hover:text-ink transition cursor-pointer"
              >
                Cancel
              </button>
            </div>
          )}
        </section>
      )}

      <Link to="/dashboard" className="inline-flex items-center gap-1.5 text-xs font-mono text-muted hover:text-ink transition-colors">
        <ArrowLeft className="w-3.5 h-3.5" /> Back to dashboard
      </Link>
    </div>
  );
};
