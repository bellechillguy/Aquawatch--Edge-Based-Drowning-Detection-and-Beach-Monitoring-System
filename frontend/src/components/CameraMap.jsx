import { useEffect, useState } from "react";
import { fetchCameras } from "../services/api.js";
import ConfigModal from "./ConfigModal.jsx";

export default function CameraMap() {
  const [cams, setCams] = useState([]);
  const [editing, setEditing] = useState(null);

  const load = async () => setCams(await fetchCameras());
  useEffect(() => { load(); }, []);

  return (
    <div className="card table-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Camera network</p>
          <h2>Kamera</h2>
        </div>
        <span className="count-pill">{cams.length} unit</span>
      </div>
      <div className="table-wrap">
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
                <td><span className="mono">{c.id}</span></td>
                <td>{c.location_name || "Belum diberi lokasi"}</td>
                <td>{c.lat ?? "-"}, {c.lng ?? "-"}</td>
                <td>{c.disappear_threshold}s</td>
                <td>
                  <span className={`badge ${c.online ? "online" : "offline"}`}>
                    <span className="status-dot" />
                    {c.online ? "online" : "offline"}
                  </span>
                </td>
                <td><span className="alert-count">{c.active_alerts}</span></td>
                <td><button className="secondary small" onClick={() => setEditing(c)}>Konfigurasi</button></td>
              </tr>
            ))}
            {cams.length === 0 && (
              <tr>
                <td colSpan={7} className="empty-state">Belum ada kamera terdaftar</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
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
