import { create } from "zustand";

interface AuthState {
  token: string | null;
  user: { id: number; username: string; avatar_url: string | null } | null;
  setAuth: (token: string, refreshToken: string, user: AuthState["user"]) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>((set) => ({
  token: localStorage.getItem("access_token"),
  user: null,
  setAuth: (token, refreshToken, user) => {
    localStorage.setItem("access_token", token);
    localStorage.setItem("refresh_token", refreshToken);
    set({ token, user });
  },
  logout: () => {
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    set({ token: null, user: null });
  },
}));
