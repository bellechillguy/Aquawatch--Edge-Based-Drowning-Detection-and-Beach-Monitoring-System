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
      <h3>⚠️ Potensi Tenggelam</h3>
      <div>Kamera: <strong>{activePopup.camera_id}</strong></div>
      <div>Track ID: {activePopup.track_id}</div>
      <div>Hilang selama: {activePopup.disappear_duration_seconds?.toFixed(1)}s</div>
      <div>Posisi: ({activePopup.last_position?.x}, {activePopup.last_position?.y})</div>
      <div className="row">
        <button onClick={() => resolve("resolved")}>Sudah Ditangani</button>
        <button className="ghost" onClick={() => resolve("false_alarm")}>False Alarm</button>
      </div>
    </div>
  );
}
