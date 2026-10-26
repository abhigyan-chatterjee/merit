import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ClerkProvider, UserProfile, useAuth as useClerkAuth } from '@clerk/clerk-react';
import { ArrowLeft, User as UserIcon, Code2, Download, Trash2, KeyRound, RefreshCw, Save } from 'lucide-react';
import { useAuth } from '../store/AuthContext';
import { authApi, progressApi } from '../utils/api';
import { NotFound } from '../components/NotFound';
import { isClerkConfigured } from '../components/ClerkOAuth';
import { loadTutorCatalog, TUTOR_PRESETS, useTutorKey } from '../hooks/useTutorKey';
import { EDITOR_LANGUAGES, EditorLang, isEditorLang } from '../data/languages';

const CLERK_PUBLISHABLE_KEY = import.meta.env.VITE_CLERK_PUBLISHABLE_KEY as string | undefined;

type Tab = 'profile' | 'tutor' | 'language' | 'data' | 'danger';

// Hoisted so ClerkProvider does not receive a fresh object on every render,
// which would re-render the embedded widget through componentDidUpdate.
const CLERK_APPEARANCE = {
  variables: {
    colorBackground: '#12181f',
    colorInputBackground: '#0d1117',
    colorText: '#e6edf3',
    colorTextSecondary: '#8b949e',
    colorPrimary: '#3fb950',
    colorInputText: '#e6edf3',
    borderRadius: '0.75rem',
  },
  elements: {
    rootBox: 'w-full max-w-4xl mx-auto',
    cardBox: 'w-full shadow-none border-0 bg-transparent',
    card: 'w-full shadow-none border-0 bg-transparent',
    navbar: 'border-r border-line bg-transparent',
    navbarButton: 'text-muted hover:text-ink hover:bg-canvas',
    pageScrollBox: 'p-4 sm:p-6 bg-transparent',
  },
};

const SecurityHeading: React.FC<{ subtitle: string }> = ({ subtitle }) => (
  <div>
    <h2 className="text-sm font-bold text-ink">Account security</h2>
    <p className="text-xs text-muted mt-0.5">{subtitle}</p>
  </div>
);

type FormMessage = { ok: boolean; text: string } | null;

/**
 * Merit's own credential controls. These back every account that was created
 * with a password (all seeded accounts, and anything that never went through
 * Clerk), which have no Clerk user for <UserProfile> to render.
 */
const NativeSecurityForm: React.FC = () => {
  const { user, changeEmail, changePassword } = useAuth();

  const [newEmail, setNewEmail] = useState(user?.email ?? '');
  const [emailPassword, setEmailPassword] = useState('');
  const [emailMsg, setEmailMsg] = useState<FormMessage>(null);
  const [emailBusy, setEmailBusy] = useState(false);

  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [passwordMsg, setPasswordMsg] = useState<FormMessage>(null);
  const [passwordBusy, setPasswordBusy] = useState(false);

  const submitEmail = async (event: React.FormEvent) => {
    event.preventDefault();
    setEmailMsg(null);
    setEmailBusy(true);
    try {
      await changeEmail(newEmail.trim(), emailPassword);
      setEmailPassword('');
      setEmailMsg({ ok: true, text: 'Email updated.' });
    } catch (error) {
      setEmailMsg({ ok: false, text: error instanceof Error ? error.message : 'Could not update email.' });
    } finally {
      setEmailBusy(false);
    }
  };

  const submitPassword = async (event: React.FormEvent) => {
    event.preventDefault();
    setPasswordMsg(null);
    if (newPassword.length < 10) {
      setPasswordMsg({ ok: false, text: 'New password must be at least 10 characters.' });
      return;
    }
    if (newPassword !== confirmPassword) {
      setPasswordMsg({ ok: false, text: 'New password and confirmation do not match.' });
      return;
    }
    setPasswordBusy(true);
    try {
      await changePassword(currentPassword, newPassword);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
      setPasswordMsg({ ok: true, text: 'Password updated.' });
    } catch (error) {
      setPasswordMsg({ ok: false, text: error instanceof Error ? error.message : 'Could not update password.' });
    } finally {
      setPasswordBusy(false);
    }
  };

  return (
    <div className="space-y-6">
      <form aria-label="Change email" className="space-y-2" onSubmit={submitEmail}>
        <h3 className="text-xs font-mono text-muted">Change email</h3>
        <div className="flex flex-wrap gap-2">
          <input
            aria-label="New email"
            type="email"
            required
            autoComplete="email"
            value={newEmail}
            onChange={(event) => setNewEmail(event.target.value)}
            className="flex-1 min-w-52 px-3 py-2 rounded-lg bg-canvas border border-line text-sm text-ink focus:border-mint"
          />
          <input
            aria-label="Account password"
            type="password"
            required
            autoComplete="current-password"
            placeholder="Account password"
            value={emailPassword}
            onChange={(event) => setEmailPassword(event.target.value)}
            className="flex-1 min-w-40 px-3 py-2 rounded-lg bg-canvas border border-line text-sm text-ink focus:border-mint placeholder-muted"
          />
          <button
            type="submit"
            disabled={emailBusy}
            className="px-4 py-2 rounded-lg bg-mint text-canvas text-xs font-semibold hover:brightness-110 transition disabled:opacity-50 cursor-pointer"
          >
            {emailBusy ? 'Saving…' : 'Update email'}
          </button>
        </div>
        {emailMsg && (
          <p role={emailMsg.ok ? 'status' : 'alert'} className={`text-xs font-mono ${emailMsg.ok ? 'text-mint' : 'text-rose'}`}>
            {emailMsg.text}
          </p>
        )}
      </form>

      <form aria-label="Change password" className="space-y-2" onSubmit={submitPassword}>
        <h3 className="text-xs font-mono text-muted">Change password</h3>
        <div className="grid gap-2 sm:grid-cols-3">
          <input
            aria-label="Current password"
            type="password"
            required
            autoComplete="current-password"
            placeholder="Current password"
            value={currentPassword}
            onChange={(event) => setCurrentPassword(event.target.value)}
            className="px-3 py-2 rounded-lg bg-canvas border border-line text-sm text-ink focus:border-mint placeholder-muted"
          />
          <input
            aria-label="New password"
            type="password"
            required
            minLength={10}
            autoComplete="new-password"
            placeholder="New password"
            value={newPassword}
            onChange={(event) => setNewPassword(event.target.value)}
            className="px-3 py-2 rounded-lg bg-canvas border border-line text-sm text-ink focus:border-mint placeholder-muted"
          />
          <input
            aria-label="Confirm new password"
            type="password"
            required
            minLength={10}
            autoComplete="new-password"
            placeholder="Confirm new password"
            value={confirmPassword}
            onChange={(event) => setConfirmPassword(event.target.value)}
            className="px-3 py-2 rounded-lg bg-canvas border border-line text-sm text-ink focus:border-mint placeholder-muted"
          />
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <button
            type="submit"
            disabled={passwordBusy}
            className="px-4 py-2 rounded-lg bg-mint text-canvas text-xs font-semibold hover:brightness-110 transition disabled:opacity-50 cursor-pointer"
          >
            {passwordBusy ? 'Saving…' : 'Update password'}
          </button>
          <span className="text-[11px] font-mono text-muted">At least 10 characters.</span>
        </div>
        {passwordMsg && (
          <p role={passwordMsg.ok ? 'status' : 'alert'} className={`text-xs font-mono ${passwordMsg.ok ? 'text-mint' : 'text-rose'}`}>
            {passwordMsg.text}
          </p>
        )}
      </form>
    </div>
  );
};

/**
 * Clerk's embedded profile only renders for a Clerk user. Rendering it
 * unconditionally left a zero-height box on every password-backed account,
 * so it is gated on a live Clerk session and the native controls fill in
 * when there is none. Runs inside ClerkProvider.
 */
const ClerkSecurityPanel: React.FC = () => {
  const { isLoaded, isSignedIn } = useClerkAuth();

  // While Clerk's script is still loading, or blocked outright, the native
  // controls stay usable instead of showing an empty panel.
  if (!isLoaded || !isSignedIn) {
    return (
      <>
        <SecurityHeading subtitle="Change the email and password used to sign in to Merit." />
        <NativeSecurityForm />
      </>
    );
  }

  return (
    <>
      <SecurityHeading subtitle="Manage emails, connected accounts and security." />
      <div className="w-full flex justify-center overflow-x-auto py-2">
        <UserProfile routing="hash" />
      </div>
    </>
  );
};

const AccountSecuritySection: React.FC = () => (
  <section aria-label="Account security" className="w-full rounded-xl border border-line bg-surface p-6 sm:p-8 space-y-4">
    {isClerkConfigured() && CLERK_PUBLISHABLE_KEY ? (
      <ClerkProvider publishableKey={CLERK_PUBLISHABLE_KEY} appearance={CLERK_APPEARANCE}>
        <ClerkSecurityPanel />
      </ClerkProvider>
    ) : (
      <>
        <SecurityHeading subtitle="Change the email and password used to sign in to Merit." />
        <NativeSecurityForm />
      </>
    )}
  </section>
);

export const ProfilePage: React.FC = () => {
  const { user, updateProfile, deleteAccount } = useAuth();
  const { search } = useLocation();
  const [tab, setTab] = useState<Tab>(() => {
    const q = new URLSearchParams(search).get('tab');
    return q === 'data' || q === 'danger' || q === 'language' || q === 'tutor' ? q : 'profile';
  });

  const [name, setName] = useState('');
  const [nameMsg, setNameMsg] = useState<string | null>(null);
  const [lang, setLang] = useState<EditorLang>('python');
  const [langMsg, setLangMsg] = useState<string | null>(null);
  const [dataMsg, setDataMsg] = useState<string | null>(null);
  const [confirmDelete, setConfirmDelete] = useState(false);
  const tutor = useTutorKey();
  const [models, setModels] = useState<string[]>([]);
  const [modelsLoading, setModelsLoading] = useState(false);
  const [modelsError, setModelsError] = useState<string | null>(null);
  const [connResult, setConnResult] = useState<{ ok: boolean; text: string } | null>(null);
  const [tutorSaveMsg, setTutorSaveMsg] = useState<string | null>(null);

  useEffect(() => {
    if (user) {
      setName(user.displayName || '');
    }
    progressApi
      .getSettings()
      .then((s) => {
        if (isEditorLang(s.preferred_language)) {
          setLang(s.preferred_language);
        }
      })
      .catch(() => {});
  }, [user?.id]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    if (window.location.hash === '#tutor') setTab('tutor');
  }, []);

  const selectedPreset = TUTOR_PRESETS.find((preset) => preset.baseUrl === tutor.baseUrl) ?? TUTOR_PRESETS[0];
  const loadCatalog = async (catalogId: string) => {
    setModelsError(null);
    try {
      const list = await loadTutorCatalog(catalogId);
      setModels(list);
      if (list.length > 0 && !list.includes(tutor.model)) tutor.setModel(list[0]);
    } catch (error) {
      setModelsError(error instanceof Error ? error.message : 'Could not load the model catalog.');
    }
  };
  const checkModels = async () => {
    if (!tutor.apiKey.trim()) {
      setModelsError('Add an API key before checking the provider.');
      setConnResult({ ok: false, text: 'Connection failed: missing API key.' });
      return;
    }
    setModelsLoading(true);
    setModelsError(null);
    setConnResult(null);
    try {
      const response = await fetch('/api/v1/tutor/models', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include',
        body: JSON.stringify({ base_url: tutor.baseUrl, api_key: tutor.apiKey }),
      });
      if (!response.ok) {
        let detail = `HTTP ${response.status}`;
        try {
          const data = (await response.json()) as { detail?: unknown; error?: { message?: unknown } };
          if (typeof data.detail === 'string' && data.detail) detail = data.detail;
          else if (data.error && typeof data.error.message === 'string') detail = data.error.message;
        } catch {
          // Non-JSON error body — keep the status fallback.
        }
        throw new Error(detail);
      }
      const data = (await response.json()) as { models?: unknown };
      const list = Array.isArray(data.models) ? data.models.filter((item): item is string => typeof item === 'string') : [];
      setModels(list);
      if (list.length > 0) tutor.setModel(list[0]);
      setConnResult({ ok: true, text: `Connection successful! Provider returned ${list.length} models.` });
    } catch (error) {
      const message = error instanceof Error ? error.message : 'Could not load provider models.';
      setModelsError(message);
      setConnResult({ ok: false, text: `Connection failed: ${message}` });
    } finally {
      setModelsLoading(false);
    }
  };

  const saveTutorSettings = () => {
    // setRemember(true) persists the current baseUrl/apiKey/model snapshot
    // to local storage (see useTutorKey.update).
    tutor.setRemember(true);
    setTutorSaveMsg('Tutor settings saved on this device.');
  };

  useEffect(() => {
    void loadCatalog(selectedPreset.catalogId);
    // Load the catalog once for the currently selected provider.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

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
    { id: 'tutor', label: 'Tutor' },
    { id: 'language', label: 'Language' },
    { id: 'data', label: 'Data' },
    { id: 'danger', label: 'Danger' },
  ];

  return (
    <div className="max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-6">
      <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-[10px] font-mono text-muted">
        <Link to="/dashboard" className="inline-block py-1.5 hover:text-mint transition-colors">
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
                className="flex-1 min-w-40 px-3 py-2 rounded-lg bg-canvas border border-line text-sm text-ink focus:border-mint"
              />
              <button type="submit" className="px-4 py-2 rounded-lg bg-mint text-canvas text-xs font-semibold hover:brightness-110 transition cursor-pointer">
                Save
              </button>
            </form>
            {nameMsg && <p className="text-xs font-mono text-muted">{nameMsg}</p>}
          </section>

          <AccountSecuritySection />
        </div>
      )}

      {tab === 'tutor' && (
        <div className="space-y-5">
          <section id="tutor" className="p-5 rounded-xl border border-line bg-surface space-y-4 scroll-mt-6">
            <div>
              <h2 className="text-sm font-bold text-ink flex items-center gap-2"><KeyRound className="w-4 h-4 text-mint" /> Tutor settings</h2>
              <p className="text-xs text-muted mt-1">Your key is kept for this browser session only, never saved to your account. Requests pass through the tutor proxy to reach the provider you selected, so treat it as leaving this device on each call.</p>
            </div>
            <label className="block text-xs font-mono">
              <span className="text-muted">Provider preset</span>
              <select aria-label="Provider preset" value={selectedPreset.id} onChange={(event) => {
                const preset = TUTOR_PRESETS.find((item) => item.id === event.target.value) ?? TUTOR_PRESETS[0];
                tutor.setBaseUrl(preset.baseUrl);
                void loadCatalog(preset.catalogId);
              }} className="mt-1 w-full p-2 rounded-lg bg-canvas border border-line text-xs font-mono text-ink">
                {TUTOR_PRESETS.map((preset) => <option key={preset.id} value={preset.id}>{preset.label}</option>)}
              </select>
            </label>
            <label className="block text-xs font-mono">
              <span className="text-muted">Provider base URL</span>
              <input aria-label="Provider base URL" value={tutor.baseUrl} onChange={(event) => tutor.setBaseUrl(event.target.value)} className="mt-1 w-full p-2 rounded-lg bg-canvas border border-line text-xs font-mono text-ink" />
            </label>
            <label className="block text-xs font-mono">
              <span className="text-muted flex items-center gap-1.5"><KeyRound className="w-3.5 h-3.5" /> API key</span>
              <input type="password" aria-label="API key" value={tutor.apiKey} onChange={(event) => tutor.setApiKey(event.target.value)} placeholder="Paste your provider key" autoComplete="off" className="mt-1 w-full p-2 rounded-lg bg-canvas border border-line text-xs font-mono text-ink placeholder-muted" />
            </label>
            <label className="flex items-center gap-2 text-xs font-mono text-muted cursor-pointer">
              <input type="checkbox" aria-label="Remember on this device" checked={tutor.remember} onChange={(event) => tutor.setRemember(event.target.checked)} className="accent-mint" />
              Remember on this device
            </label>
            <div className="flex flex-wrap items-end gap-2">
              <label className="flex-1 min-w-40 block text-xs font-mono">
                <span className="text-muted">Model</span>
                <select aria-label="Model" value={tutor.model} onChange={(event) => tutor.setModel(event.target.value)} className="mt-1 w-full p-2 rounded-lg bg-canvas border border-line text-xs font-mono text-ink">
                  {models.length === 0 ? <option value="">Loading catalog…</option> : models.map((item) => <option key={item} value={item}>{item}</option>)}
                </select>
              </label>
              <button onClick={saveTutorSettings} className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg bg-mint text-canvas text-xs font-mono font-semibold hover:brightness-110 transition cursor-pointer"><Save className="w-3.5 h-3.5" />Save</button>
              <button onClick={() => void checkModels()} disabled={modelsLoading || !tutor.apiKey.trim()} className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg border border-line text-xs font-mono text-ink hover:border-mint disabled:opacity-50 cursor-pointer"><RefreshCw className={`w-3.5 h-3.5 ${modelsLoading ? 'animate-spin' : ''}`} />{modelsLoading ? 'Checking…' : 'Test connection'}</button>
            </div>
            {tutorSaveMsg && <p className="text-xs font-mono text-mint">{tutorSaveMsg}</p>}
            {modelsError && <p role="alert" className="text-xs font-mono text-rose">{modelsError}</p>}
            {connResult && (
              <p role="status" className={`text-xs font-mono ${connResult.ok ? 'text-mint' : 'text-rose'}`}>
                {connResult.text}
              </p>
            )}
          </section>

        </div>
      )}

      {tab === 'language' && (
        <section className="p-5 rounded-xl border border-line bg-surface space-y-3">
          <h2 className="text-sm font-bold text-ink flex items-center gap-2">
            <Code2 className="w-4 h-4 text-mint" /> Preferred language
          </h2>
          <p className="text-xs text-muted">Used as the default in code runners.</p>
          <div className="flex gap-2">
            {EDITOR_LANGUAGES.map((l) => (
              <button
                key={l.value}
                onClick={async () => {
                  setLang(l.value);
                  setLangMsg(null);
                  try {
                    await progressApi.saveSettings({ preferred_language: l.value });
                    setLangMsg(`Default language: ${l.short}.`);
                  } catch {
                    setLangMsg('Could not save (offline?).');
                  }
                }}
                className={`px-4 py-2 rounded-lg border text-xs font-mono transition cursor-pointer ${
                  lang === l.value ? 'border-mint bg-mint/10 text-mint font-semibold' : 'border-line bg-canvas text-muted hover:text-ink'
                }`}
              >
                {l.short}
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
