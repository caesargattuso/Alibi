import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { ConfigProvider, theme } from "antd";
import { Home } from "./pages/Home";
import { ScriptDetail } from "./pages/ScriptDetail";
import { Game } from "./pages/Game";
import { Login, Register } from "./pages/Auth";
import { Profile } from "./pages/Profile";
import ScriptEditor from "./pages/ScriptEditor";
import { useAuthStore } from "./stores/authStore";

function PrivateRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  return token ? <>{children}</> : <Navigate to="/login" />;
}

function App() {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm,
        token: {
          colorPrimary: "#FF6B9D",
          borderRadius: 8,
        },
      }}
    >
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<PrivateRoute><Home /></PrivateRoute>} />
          <Route path="/scripts/:id" element={<PrivateRoute><ScriptDetail /></PrivateRoute>} />
          <Route path="/scripts/create" element={<PrivateRoute><ScriptEditor /></PrivateRoute>} />
          <Route path="/scripts/:id/edit" element={<PrivateRoute><ScriptEditor /></PrivateRoute>} />
          <Route path="/game/:sessionId" element={<PrivateRoute><Game /></PrivateRoute>} />
          <Route path="/profile" element={<PrivateRoute><Profile /></PrivateRoute>} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
        </Routes>
      </BrowserRouter>
    </ConfigProvider>
  );
}

export default App;