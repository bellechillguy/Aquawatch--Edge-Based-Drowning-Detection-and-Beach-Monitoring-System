import { useMemo, useEffect, useState } from "react";
import { updateAlert } from "../services/api.js";
import { useAlerts } from "../context/AlertContext.jsx";

export default function AlertHistory() {
  const { alerts, reload } = useAlerts();
  const [filter, setFilter] = useState({
    status: "",
    camera_id: ""
  });

  useEffect(() => {
    reload();
  }, [reload]);

  const rows = useMemo(() => {
    return alerts.filter((a) => {
      const statusOk =
        !filter.status || a.status === filter.status;

      const cameraOk =
        !filter.camera_id ||
        (a.camera_id ?? "")
          .toLowerCase()
          .includes(filter.camera_id.toLowerCase());

      return statusOk && cameraOk;
    });
  }, [alerts, filter]);

  const act = async (id, status) => {
    await updateAlert(id, status);
    reload();
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
