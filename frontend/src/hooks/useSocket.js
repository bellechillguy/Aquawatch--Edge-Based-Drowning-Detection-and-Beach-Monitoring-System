import { useEffect, useRef } from "react";
import { io } from "socket.io-client";

const SOCKET_URL = import.meta.env.VITE_SOCKET_URL || window.location.origin;

export function useSocket(onEvent) {
  const ref = useRef(null);
  useEffect(() => {
    const socket = io(SOCKET_URL, { transports: ["websocket", "polling"] });
    ref.current = socket;
    socket.on("connect", () => {
      console.info("[socket] connected", socket.id);
      onEvent?.("socket_connected", { id: socket.id });
    });
    socket.on("new_alert", (data) => onEvent?.("new_alert", data));
    socket.on("alert_updated", (data) => onEvent?.("alert_updated", data));
    return () => socket.disconnect();
  }, [onEvent]);
  return ref;
}
