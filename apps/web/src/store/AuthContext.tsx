import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { ApiError, authApi, UserProfile } from "@/utils/api";

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
  /**
   * Set when the session probe failed for a reason that is not "you are signed
   * out" (network error, timeout, 5xx). The UI can offer a retry instead of
   * pretending the account disappeared.
   */
  authError: Error | null;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, displayName: string) => Promise<void>;
  loginWithClerk: (clerkToken: string) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<UserProfile | null>;
  updateProfile: (displayName: string) => Promise<void>;
  changeEmail: (newEmail: string, currentPassword: string) => Promise<void>;
  changePassword: (currentPassword: string, newPassword: string) => Promise<void>;
  deleteAccount: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const HAD_SESSION_KEY = 'merit_had_session';
export const SIGNOUT_PENDING_KEY = 'merit.clerk.signout_pending';

const signOutClerk = async () => {
  try {
    const clerk = (
      window as unknown as { Clerk?: { signOut?: () => Promise<unknown> | unknown } }
    ).Clerk;
    if (clerk && typeof clerk.signOut === "function") {
      await clerk.signOut();
      try {
        window.sessionStorage.removeItem(SIGNOUT_PENDING_KEY);
      } catch {
        // ignore storage errors
      }
    } else {
      try {
        window.sessionStorage.setItem(SIGNOUT_PENDING_KEY, '1');
        window.sessionStorage.removeItem('merit.oauth.state');
        window.sessionStorage.removeItem('merit.oauth.next');
      } catch {
        // ignore storage errors
      }
    }
  } catch {
    try {
      window.sessionStorage.removeItem(SIGNOUT_PENDING_KEY);
    } catch {
      // ignore
    }
  }
};

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);
  const [authError, setAuthError] = useState<Error | null>(null);

  const refreshUser = useCallback(async (): Promise<UserProfile | null> => {
    try {
      const hadSession = Boolean(window.localStorage.getItem(HAD_SESSION_KEY));
      const profile = hadSession ? await authApi.getMe() : await authApi.probeSession();
      window.localStorage.setItem(HAD_SESSION_KEY, '1');
      setUser(profile);
      setAuthError(null);
      return profile;
    } catch (error) {
      // Only a real 401 means "signed out". A network blip, a timeout or a
      // 5xx says nothing about the session, so it must not destroy it — the
      // failure is surfaced as `authError` and a reload/retry recovers.
      const status = error instanceof ApiError ? error.status : null;
      if (status === 401) {
        window.localStorage.removeItem(HAD_SESSION_KEY);
        setUser(null);
        setAuthError(null);
      } else {
        setAuthError(error instanceof Error ? error : new Error("AUTH_CHECK_FAILED"));
      }
      return null;
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    refreshUser();
  }, [refreshUser]);

  const login = async (email: string, password: string) => {
    const profile = await authApi.login(email, password);
    window.localStorage.setItem(HAD_SESSION_KEY, '1');
    setAuthError(null);
    setUser(profile);
  };

  const register = async (email: string, password: string, displayName: string) => {
    const profile = await authApi.register(email, password, displayName);
    window.localStorage.setItem(HAD_SESSION_KEY, '1');
    setAuthError(null);
    setUser(profile);
  };

  const loginWithClerk = async (clerkToken: string) => {
    const profile = await authApi.loginWithClerk(clerkToken);
    window.localStorage.setItem(HAD_SESSION_KEY, '1');
    setAuthError(null);
    setUser(profile);
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      await signOutClerk();
      window.localStorage.removeItem(HAD_SESSION_KEY);
      setUser(null);
    }
  };

  const deleteAccount = async () => {
    try {
      await authApi.deleteAccount();
    } finally {
      await signOutClerk();
      window.localStorage.removeItem(HAD_SESSION_KEY);
      setUser(null);
    }
  };

  const updateProfile = async (displayName: string) => {
    const profile = await authApi.updateProfile(displayName);
    setUser(profile);
  };

  const changeEmail = async (newEmail: string, currentPassword: string) => {
    const profile = await authApi.changeEmail(newEmail, currentPassword);
    setUser(profile);
  };

  const changePassword = async (currentPassword: string, newPassword: string) => {
    await authApi.changePassword(currentPassword, newPassword);
  };

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        authError,
        login,
        register,
        loginWithClerk,
        logout,
        refreshUser,
        updateProfile,
        changeEmail,
        changePassword,
        deleteAccount,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    return {
      user: null,
      isLoading: false,
      authError: null,
      login: async () => {},
      register: async () => {},
      loginWithClerk: async () => {},
      logout: async () => {},
      refreshUser: async () => null,
      updateProfile: async () => {},
      changeEmail: async () => {},
      changePassword: async () => {},
      deleteAccount: async () => {},
    };
  }
  return context;
};
