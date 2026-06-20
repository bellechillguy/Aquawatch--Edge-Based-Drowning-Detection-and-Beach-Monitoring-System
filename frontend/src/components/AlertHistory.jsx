import { useMemo, useEffect, useState } from "react";
import { fetchAlertThumbnail, updateAlert } from "../services/api.js";
import { useAlerts } from "../context/AlertContext.jsx";

export default function AlertHistory() {
  const { alerts, reload } = useAlerts();
  const [preview, setPreview] = useState(null);
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

  const openPreview = async (alert) => {
    if (preview?.url) {
      URL.revokeObjectURL(preview.url);
    }

    const blob = await fetchAlertThumbnail(alert.id);
    const url = URL.createObjectURL(blob);
    setPreview({ alert, url });
  };

  const closePreview = () => {
    if (preview?.url) {
      URL.revokeObjectURL(preview.url);
    }
    setPreview(null);
  };

  useEffect(() => {
    return () => {
      if (preview?.url) {
        URL.revokeObjectURL(preview.url);
      }
    };
  }, [preview]);

  return (
    <div className="card table-card">
      <div className="section-heading">
        <div>
          <p className="eyebrow">Incident timeline</p>
          <h2>Riwayat Alert</h2>
        </div>
        <span className="count-pill">{rows.length} alert</span>
      </div>
      <div className="toolbar">
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
      <div className="table-wrap">
        <table>
          <thead>
            <tr>
              <th>ID</th><th>Kamera</th><th>Track</th><th>Waktu</th>
              <th>Durasi</th><th>Status</th><th>Aksi</th>
            </tr>
          </thead>
          <tbody>
            {rows.map((a) => (
              <tr key={a.id}>
                <td><span className="mono">#{a.id}</span></td>
                <td>{a.camera_id}</td>
                <td>{a.track_id}</td>
                <td>{new Date(a.triggered_at).toLocaleString()}</td>
                <td>{a.disappear_duration_seconds?.toFixed(1)}s</td>
                <td><span className={`badge ${a.status}`}>{a.status}</span></td>
                <td>
                  <div className="action-group">
                    {a.thumbnail_path && (
                      <button className="secondary small" onClick={() => openPreview(a)}>Preview</button>
                    )}
                    {a.status === "active" && (
                      <>
                        <button className="small" onClick={() => act(a.id, "resolved")}>Resolve</button>
                        <button className="ghost small" onClick={() => act(a.id, "false_alarm")}>False</button>
                      </>
                    )}
                  </div>
                </td>
              </tr>
            ))}
            {rows.length === 0 && (
              <tr>
                <td colSpan={7} className="empty-state">Belum ada data alert</td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      {preview && (
        <div className="modal-backdrop" role="dialog" aria-modal="true">
          <div className="preview-modal">
            <div className="preview-header">
              <div>
                <h3>Preview Alert #{preview.alert.id}</h3>
                <p>Kamera {preview.alert.camera_id} - Track {preview.alert.track_id}</p>
              </div>
              <button className="ghost" onClick={closePreview}>Tutup</button>
            </div>
            <img src={preview.url} alt={`Preview alert ${preview.alert.id}`} />
          </div>
        </div>
      )}
    </div>
  );
}
