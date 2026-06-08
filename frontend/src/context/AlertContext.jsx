import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { fetchAlerts } from "../services/api.js";
import { useSocket } from "../hooks/useSocket.js";

const AlertContext = createContext(null);
export const useAlerts = () => useContext(AlertContext);

export function AlertProvider({ children }) {
  const [alerts, setAlerts] = useState([]);
  const [activePopup, setActivePopup] = useState(null);

  const load = useCallback(async () => {
    try {
      if (!localStorage.getItem("aw_token")) return;
      setAlerts(await fetchAlerts({ limit: 50 }));
    } catch (e) {
      console.warn("fetchAlerts failed", e);
    }
  }, []);

  useEffect(() => {
    load();
    const id = setInterval(load, 30000); // 30s fallback poll
    return () => clearInterval(id);
  }, [load]);

  const onSocketEvent = useCallback((event, data) => {
    if (event === "new_alert") {
      setAlerts((prev) => [data, ...prev]);
      setActivePopup(data);
      try {
        new Audio("/alert.mp3").play().catch(() => {});
      } catch {}
    } else if (event === "alert_updated") {
      setAlerts((prev) => prev.map((a) => (a.id === data.id ? data : a)));
      setActivePopup((p) => (p && p.id === data.id ? null : p));
    } else if (event === "socket_connected") {
      load();
    }
  }, [load]);

  useSocket(onSocketEvent);

  return (
    <AlertContext.Provider
      value={{ alerts, activePopup, dismissPopup: () => setActivePopup(null), reload: load }}
    >
      {children}
    </AlertContext.Provider>
  );
}
