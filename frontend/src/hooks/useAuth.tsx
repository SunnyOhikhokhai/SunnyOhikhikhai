import { useQuery, useQueryClient } from "@tanstack/react-query";
import { createContext, useCallback, useContext, useMemo, type ReactNode } from "react";
import { api } from "@/lib/api";
import type { Me } from "@/lib/types";

interface AuthState {
  user: Me | null;
  loading: boolean;
  smsEnabled: boolean;
  setUser: (u: Me | null) => void;
  refresh: () => Promise<unknown>;
  logout: () => Promise<void>;
  can: (perm: string) => boolean;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const qc = useQueryClient();
  const { data, isLoading, refetch } = useQuery({
    queryKey: ["me"],
    queryFn: async () => (await api.get<{ data: { user: Me | null; sms_enabled: boolean } }>("/api/auth/me")).data,
    staleTime: 60_000,
    retry: false,
  });

  const setUser = useCallback(
    (u: Me | null) => qc.setQueryData(["me"], (old: { sms_enabled: boolean } | undefined) => ({ sms_enabled: old?.sms_enabled ?? false, user: u })),
    [qc],
  );

  const logout = useCallback(async () => {
    await api.post("/api/auth/logout").catch(() => undefined);
    qc.clear();
    qc.setQueryData(["me"], { user: null, sms_enabled: data?.sms_enabled ?? false });
  }, [qc, data?.sms_enabled]);

  const value = useMemo<AuthState>(
    () => ({
      user: data?.user ?? null,
      loading: isLoading,
      smsEnabled: data?.sms_enabled ?? false,
      setUser,
      refresh: refetch,
      logout,
      can: (perm: string) => !!data?.user?.admin?.permissions.includes(perm),
    }),
    [data, isLoading, setUser, refetch, logout],
  );
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
