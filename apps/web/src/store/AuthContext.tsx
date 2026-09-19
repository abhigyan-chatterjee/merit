import React, { createContext, useContext, useEffect, useState, useCallback } from "react";
import { authApi, UserProfile, ApiError } from "@/utils/api";

interface AuthContextType {
  user: UserProfile | null;
  isLoading: boolean;
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

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isLoading, setIsLoading] = useState<boolean>(true);

  const refreshUser = useCallback(async (): Promise<UserProfile | null> => {
    try {
      const profile = await authApi.getMe();
      setUser(profile);
      return profile;
    } catch {
      setUser(null);
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
    setUser(profile);
  };

  const register = async (email: string, password: string, displayName: string) => {
    const profile = await authApi.register(email, password, displayName);
    setUser(profile);
  };

  const loginWithClerk = async (clerkToken: string) => {
    const profile = await authApi.loginWithClerk(clerkToken);
    setUser(profile);
  };

  const logout = async () => {
    try {
      await authApi.logout();
    } finally {
      setUser(null);
    }
  };

  const deleteAccount = async () => {
    await authApi.deleteAccount();
    setUser(null);
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

export { ApiError };
