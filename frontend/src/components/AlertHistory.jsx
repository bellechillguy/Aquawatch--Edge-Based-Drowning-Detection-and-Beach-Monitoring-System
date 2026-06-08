import { useEffect, useState } from "react";
import { fetchAlerts, updateAlert } from "../services/api.js";

export default function AlertHistory() {
  const [rows, setRows] = useState([]);
  const [filter, setFilter] = useState({ status: "", camera_id: "" });

  const load = async () => setRows(await fetchAlerts(filter));
  useEffect(() => { load(); /* eslint-disable-next-line */ }, [filter]);

  const act = async (id, status) => {
    await updateAlert(id, status);
    load();
  };

  return (
    <div className="card">
      <h2>Riwayat Alert</h2>
      <div style={{ display: "flex", gap: 8, margin: "12px 0" }}>
        <select value={filter.status} onChange={(e) => setFilter({ ...filter, status: e.target.value })}>
          <option value="">Semua status</option>
          <option value="active">Active</option>
          <option value="resolved">Resolved</option>
          <option value="false_alarm">False Alarm</option>
        </select>
        <input
          placeholder="camera_id"
          value={filter.camera_id}
          onChange={(e) => setFilter({ ...filter, camera_id: e.target.value })}
        />
      </div>
      <table>
        <thead>
          <tr>
            <th>ID</th><th>Kamera</th><th>Track</th><th>Waktu</th>
            <th>Durasi (s)</th><th>Status</th><th>Aksi</th>
          </tr>
        </thead>
        <tbody>
          {rows.map((a) => (
            <tr key={a.id}>
              <td>{a.id}</td>
              <td>{a.camera_id}</td>
              <td>{a.track_id}</td>
              <td>{new Date(a.triggered_at).toLocaleString()}</td>
              <td>{a.disappear_duration_seconds?.toFixed(1)}</td>
              <td><span className={`badge ${a.status}`}>{a.status}</span></td>
              <td>
                {a.status === "active" && (
                  <>
                    <button onClick={() => act(a.id, "resolved")}>Resolve</button>{" "}
                    <button className="ghost" onClick={() => act(a.id, "false_alarm")}>False</button>
                  </>
                )}
              </td>
            </tr>
          ))}
          {rows.length === 0 && <tr><td colSpan={7} style={{ textAlign: "center", padding: 24 }}>Belum ada data</td></tr>}
        </tbody>
      </table>
    </div>
  );
}
