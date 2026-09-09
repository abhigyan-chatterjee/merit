import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  User as UserIcon,
  LogOut,
  ChevronDown,
  Settings,
  Download,
  Trash2,
} from 'lucide-react';
import { useAuth } from '../store/AuthContext';

export const UserDropdown: React.FC = () => {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (!open) return;
    const onDown = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setOpen(false);
    };
    window.addEventListener('mousedown', onDown);
    window.addEventListener('keydown', onKey);
    return () => {
      window.removeEventListener('mousedown', onDown);
      window.removeEventListener('keydown', onKey);
    };
  }, [open ]);

  if (!user) return null;

  const go = (path: string) => {
    setOpen(false);
    navigate(path);
  };

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((o) => !o)}
        title={`Signed in as ${user.displayName} (${user.email})`}
        aria-label="Account menu"
        aria-expanded={open}
        className="flex items-center gap-1.5 px-2 py-1 rounded-lg border border-line bg-surface text-xs font-mono text-ink hover:border-steel transition cursor-pointer"
      >
        <UserIcon className="w-3.5 h-3.5 text-mint" />
        <span className="max-w-[80px] sm:max-w-[120px] truncate">{user.displayName}</span>
        <ChevronDown className={`w-3 h-3 text-muted transition-transform ${open ? 'rotate-180' : ''}`} />
      </button>

      {open && (
        <div className="absolute right-0 mt-2 w-60 rounded-xl border border-line bg-surface shadow-2xl p-2 z-50">
          <div className="px-3 py-2 border-b border-line mb-1">
            <p className="text-xs font-semibold text-ink truncate">{user.displayName}</p>
            <p className="text-[11px] font-mono text-muted truncate">{user.email}</p>
            <p className="text-[10px] font-mono text-muted capitalize mt-0.5">{user.role}</p>
          </div>

          {user.role === 'admin' && (
            <button
              onClick={() => go('/admin')}
              className="w-full text-left px-3 py-2 rounded-lg text-xs text-violet hover:bg-canvas transition cursor-pointer"
            >
              Admin Console
            </button>
          )}
          <button
            onClick={() => go('/profile')}
            className="w-full flex items-center gap-2 text-left px-3 py-2 rounded-lg text-xs text-ink hover:bg-canvas transition cursor-pointer"
          >
            <Settings className="w-3.5 h-3.5 text-muted" />
            Profile & settings
          </button>
          <button
            onClick={() => go('/profile?tab=data')}
            className="w-full flex items-center gap-2 text-left px-3 py-2 rounded-lg text-xs text-ink hover:bg-canvas transition cursor-pointer"
          >
            <Download className="w-3.5 h-3.5 text-muted" />
            Export my data
          </button>
          <button
            onClick={() => go('/profile?tab=danger')}
            className="w-full flex items-center gap-2 text-left px-3 py-2 rounded-lg text-xs text-rose hover:bg-canvas transition cursor-pointer"
          >
            <Trash2 className="w-3.5 h-3.5" />
            Delete account
          </button>
          <div className="border-t border-line mt-1 pt-1">
            <button
              onClick={() => {
                setOpen(false);
                logout();
              }}
              className="w-full flex items-center gap-2 text-left px-3 py-2 rounded-lg text-xs text-muted hover:text-rose hover:bg-canvas transition cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5" />
              Sign out
            </button>
          </div>
        </div>
      )}
    </div>
  );
};
