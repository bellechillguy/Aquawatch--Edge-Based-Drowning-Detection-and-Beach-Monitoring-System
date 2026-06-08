import { useState } from "react";
import { NavLink, Navigate, Route, Routes, useNavigate } from "react-router-dom";
import AlertPanel from "./components/AlertPanel.jsx";
import AlertHistory from "./components/AlertHistory.jsx";
import CameraMap from "./components/CameraMap.jsx";
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
    <div className="container login">
      <div className="card">
        <h2>AquaWatch Login</h2>
        <form onSubmit={submit} style={{ marginTop: 16 }}>
          <input placeholder="username" value={u} onChange={(e) => setU(e.target.value)} />
          <input placeholder="password" type="password" value={p} onChange={(e) => setP(e.target.value)} />
          {err && <div style={{ color: "#f87171", marginBottom: 8 }}>{err}</div>}
          <button type="submit" style={{ width: "100%" }}>Masuk</button>
        </form>
      </div>
    </div>
  );
}

function Shell() {
  const nav = useNavigate();
  const logout = () => {
    localStorage.removeItem("aw_token");
    localStorage.removeItem("aw_user");
    nav("/login");
  };
  return (
    <div className="app">
      <header className="topbar">
        <div style={{ fontWeight: 700, fontSize: 18 }}>🌊 AquaWatch</div>
        <nav>
          <NavLink to="/" end>Dashboard</NavLink>
          <NavLink to="/history">Riwayat</NavLink>
          <NavLink to="/cameras">Kamera</NavLink>
        </nav>
        <button className="ghost" onClick={logout}>Logout</button>
      </header>
      <main className="container">
        <Routes>
          <Route path="/" element={<><CameraMap /><AlertHistory /></>} />
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
