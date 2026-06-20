import { useState } from "react";
import { NavLink, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import AlertPanel from "./components/AlertPanel.jsx";
import AlertHistory from "./components/AlertHistory.jsx";
import CameraMap from "./components/CameraMap.jsx";
import { useAlerts } from "./context/AlertContext.jsx";
import { login } from "./services/api.js";

function RequireAuth({ children }) {
  const token = localStorage.getItem("aw_token");
  return token ? children : <Navigate to="/login" replace />;
}

function Login() {
  const nav = useNavigate();
  const [u, setU] = useState("");
  const [p, setP] = useState("");
  const [err, setErr] = useState("");

  const submit = async (e) => {
    e.preventDefault();
    try {
      const res = await login(u, p);
      localStorage.setItem("aw_token", res.access_token);
      localStorage.setItem("aw_user", JSON.stringify(res.user));
      nav("/");
    } catch {
      setErr("Login gagal");
    }
  };

  return (
    <div className="login-page">
      <div className="login-shell">
        <div className="brand-lockup">
          <span className="brand-mark">AW</span>
          <span>AquaWatch</span>
        </div>
        <h1>Kolam aman, keputusan lebih cepat.</h1>
        <p>Masuk untuk memantau kamera, alert tenggelam, dan status edge device secara real time.</p>
        <form className="login-card" onSubmit={submit}>
          <label>
            Username
            <input placeholder="admin" value={u} onChange={(e) => setU(e.target.value)} />
          </label>
          <label>
            Password
            <input placeholder="aquawatch" type="password" value={p} onChange={(e) => setP(e.target.value)} />
          </label>
          {err && <div className="form-error">{err}</div>}
          <button type="submit">Masuk dashboard</button>
        </form>
      </div>
    </div>
  );
}

function DashboardHome() {
  const { alerts } = useAlerts();
  const active = alerts.filter((a) => a.status === "active").length;
  const resolved = alerts.filter((a) => a.status === "resolved").length;
  const latest = alerts[0];

  return (
    <>
      <section className="page-hero">
        <div>
          <p className="eyebrow">Live safety operations</p>
          <h1>Monitoring deteksi tenggelam</h1>
          <p className="hero-copy">
            Pantau status kamera, alert aktif, dan preview frame deteksi dari edge AI dalam satu dashboard.
          </p>
        </div>
        <div className="metric-strip" aria-label="Ringkasan alert">
          <div className="metric-card danger">
            <span>Alert aktif</span>
            <strong>{active}</strong>
          </div>
          <div className="metric-card">
            <span>Ditangani</span>
            <strong>{resolved}</strong>
          </div>
          <div className="metric-card wide">
            <span>Alert terbaru</span>
            <strong>{latest ? `#${latest.id}` : "Belum ada"}</strong>
          </div>
        </div>
      </section>
      <CameraMap />
      <AlertHistory />
    </>
  );
}

function Shell() {
  const nav = useNavigate();
  const storedUser = localStorage.getItem("aw_user");
  let user = null;
  try {
    user = storedUser ? JSON.parse(storedUser) : null;
  } catch {
    user = null;
  }
  const logout = () => {
    localStorage.removeItem("aw_token");
    localStorage.removeItem("aw_user");
    nav("/login");
  };
  return (
    <div className="app">
      <header className="topbar">
        <div className="brand-lockup">
          <span className="brand-mark">AW</span>
          <span>AquaWatch</span>
        </div>
        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/history">Riwayat</NavLink>
          <NavLink to="/cameras">Kamera</NavLink>
        </nav>
        <div className="topbar-actions">
          <span className="user-chip">{user?.username ?? "operator"}</span>
          <button className="ghost" onClick={logout}>Logout</button>
        </div>
      </header>
      <main className="container">
        <Routes>
          <Route path="/" element={<DashboardHome />} />
          <Route path="/history" element={<AlertHistory />} />
          <Route path="/cameras" element={<CameraMap />} />
        </Routes>
      </main>
      <AlertPanel />
    </div>
  );
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/*" element={<RequireAuth><Shell /></RequireAuth>} />
    </Routes>
  );
}
