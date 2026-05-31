import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "../stores/authStore";
import { authService, userService } from "../services/auth";

export function useAuth() {
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const setAuth = useAuthStore((s) => s.setAuth);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  const login = useCallback(async (username_or_email: string, password: string) => {
    const { data: resp } = await authService.login({ username_or_email, password });
    const d = resp.data as Record<string, unknown>;
    setAuth(d.access_token as string, d.refresh_token as string, { id: d.user_id as number, username: d.username as string, avatar_url: null });
    navigate("/");
  }, [setAuth, navigate]);

  const register = useCallback(async (username: string, email: string, password: string) => {
    const { data: resp } = await authService.register({ username, email, password });
    const d = resp.data as Record<string, unknown>;
    setAuth(d.access_token as string, d.refresh_token as string, { id: d.user_id as number, username: d.username as string, avatar_url: null });
    navigate("/");
  }, [setAuth, navigate]);

  const doLogout = useCallback(() => {
    logout();
    navigate("/login");
  }, [logout, navigate]);

  const fetchMe = useCallback(async () => {
    const { data: resp } = await userService.getMe();
    useAuthStore.setState({ user: resp.data as unknown as any });
  }, []);

  return { token, user, isAuthenticated: !!token, login, register, logout: doLogout, fetchMe };
}
