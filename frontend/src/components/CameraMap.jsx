import { useEffect, useState } from "react";
import { fetchCameras } from "../services/api.js";
import ConfigModal from "./ConfigModal.jsx";

export default function CameraMap() {
  const [cams, setCams] = useState([]);
  const [editing, setEditing] = useState(null);

  const load = async () => setCams(await fetchCameras());
  useEffect(() => { load(); }, []);

  return (
    <div className="card">
      <h2>Kamera</h2>
      <table>
        <thead>
          <tr>
            <th>ID</th>
            <th>Lokasi</th>
            <th>Koordinat</th>
            <th>Threshold</th>
            <th>Status</th>
            <th>Alert Aktif</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          {cams.map((c) => (
            <tr key={c.id}>
              <td>{c.id}</td>
              <td>{c.location_name}</td>
              <td>{c.lat}, {c.lng}</td>
              <td>{c.disappear_threshold}s</td>
              <td>
                <span className={`badge ${c.online ? "resolved" : "active"}`}>
                  {c.online ? "online" : "offline"}
                </span>
              </td>
              <td>{c.active_alerts}</td>
              <td><button onClick={() => setEditing(c)}>Konfigurasi</button></td>
            </tr>
          ))}
          {cams.length === 0 && <tr><td colSpan={6} style={{ textAlign: "center", padding: 24 }}>Belum ada kamera</td></tr>}
        </tbody>
      </table>
      {editing && (
        <ConfigModal
          camera={editing}
          onClose={() => setEditing(null)}
          onSaved={() => { setEditing(null); load(); }}
        />
      )}
    </div>
  );
}
