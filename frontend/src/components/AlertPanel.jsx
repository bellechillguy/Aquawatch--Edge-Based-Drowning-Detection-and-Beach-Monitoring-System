import { useAlerts } from "../context/AlertContext.jsx";
import { updateAlert } from "../services/api.js";

export default function AlertPanel() {
  const { activePopup, dismissPopup } = useAlerts();
  if (!activePopup) return null;

  const resolve = async (status) => {
    await updateAlert(activePopup.id, status);
    dismissPopup();
  };

  return (
    <div className="alert-popup" role="alertdialog">
      <p className="eyebrow">Critical alert</p>
      <h3>Potensi tenggelam</h3>
      <div className="alert-detail-grid">
        <span>Kamera</span><strong>{activePopup.camera_id}</strong>
        <span>Track</span><strong>{activePopup.track_id}</strong>
        <span>Durasi</span><strong>{activePopup.disappear_duration_seconds?.toFixed(1)}s</strong>
        <span>Posisi</span><strong>({activePopup.last_position?.x}, {activePopup.last_position?.y})</strong>
      </div>
      <div className="row">
        <button onClick={() => resolve("resolved")}>Sudah Ditangani</button>
        <button className="ghost" onClick={() => resolve("false_alarm")}>False Alarm</button>
      </div>
    </div>
  );
}
