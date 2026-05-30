import { useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { message } from "antd";
import { useAuthStore } from "../stores/authStore";
import { authService, userService } from "../services/auth";

export function useAuth() {
  const token = useAuthStore((s) => s.token);
  const user = useAuthStore((s) => s.user);
  const setAuth = useAuthStore((s) => s.setAuth);
  const logout = useAuthStore((s) => s.logout);
  const navigate = useNavigate();

  const login = useCallback(async (username_or_email: string, password: string) => {
    const { data } = await authService.login({ username_or_email, password });
    const d = data.data;
    setAuth(d.access_token, d.refresh_token, { id: d.user_id, username: d.username, avatar_url: null });
    navigate("/");
  }, [setAuth, navigate]);

  const register = useCallback(async (username: string, email: string, password: string) => {
    const { data } = await authService.register({ username, email, password });
    const d = data.data;
    setAuth(d.access_token, d.refresh_token, { id: d.user_id, username: d.username, avatar_url: null });
    navigate("/");
  }, [setAuth, navigate]);

  const doLogout = useCallback(() => {
    logout();
    navigate("/login");
  }, [logout, navigate]);

  const fetchMe = useCallback(async () => {
    const { data } = await userService.getMe();
    useAuthStore.setState({ user: data.data });
  }, []);

  return { token, user, isAuthenticated: !!token, login, register, logout: doLogout, fetchMe };
}
