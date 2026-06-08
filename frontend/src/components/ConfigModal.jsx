import { useState } from "react";
import { updateCameraConfig } from "../services/api.js";

export default function ConfigModal({ camera, onClose, onSaved }) {
  const [threshold, setThreshold] = useState(camera.disappear_threshold ?? 15);
  const [polygon, setPolygon] = useState(JSON.stringify(camera.zone_polygon || [], null, 2));

  const save = async () => {
    try {
      const parsed = JSON.parse(polygon);
      await updateCameraConfig(camera.id, {
        disappear_threshold: Number(threshold),
        zone_polygon: parsed,
      });
      onSaved?.();
    } catch (e) {
      alert("Polygon JSON tidak valid: " + e.message);
    }
  };

  return (
    <div style={{
      position: "fixed", inset: 0, background: "rgba(0,0,0,.6)",
      display: "flex", alignItems: "center", justifyContent: "center", zIndex: 100,
    }}>
      <div className="card" style={{ width: 480 }}>
        <h3>Konfigurasi {camera.id}</h3>
        <div style={{ margin: "12px 0" }}>
          <label>Disappear Threshold (detik)</label><br />
          <input type="number" value={threshold} onChange={(e) => setThreshold(e.target.value)} />
        </div>
        <div style={{ margin: "12px 0" }}>
          <label>Zone Polygon (JSON array of [x,y])</label>
          <textarea
            rows={8} style={{ width: "100%", fontFamily: "monospace" }}
            value={polygon} onChange={(e) => setPolygon(e.target.value)}
          />
        </div>
        <div style={{ display: "flex", gap: 8, justifyContent: "flex-end" }}>
          <button className="ghost" onClick={onClose}>Batal</button>
          <button onClick={save}>Simpan</button>
        </div>
      </div>
    </div>
  );
}
