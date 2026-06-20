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
    <div className="modal-backdrop" role="dialog" aria-modal="true">
      <div className="form-modal">
        <div className="preview-header">
          <div>
            <p className="eyebrow">Camera config</p>
            <h3>Konfigurasi {camera.id}</h3>
          </div>
          <button className="ghost small" onClick={onClose}>Tutup</button>
        </div>
        <label className="field">
          Disappear Threshold (detik)
          <input type="number" value={threshold} onChange={(e) => setThreshold(e.target.value)} />
        </label>
        <label className="field">
          Zone Polygon (JSON array of [x,y])
          <textarea
            rows={8}
            value={polygon} onChange={(e) => setPolygon(e.target.value)}
          />
        </label>
        <div className="modal-actions">
          <button className="ghost" onClick={onClose}>Batal</button>
          <button onClick={save}>Simpan</button>
        </div>
      </div>
    </div>
  );
}
