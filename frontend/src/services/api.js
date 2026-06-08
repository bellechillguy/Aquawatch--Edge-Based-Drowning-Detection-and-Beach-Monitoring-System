import axios from "axios";

export const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || "/api",
});

api.interceptors.request.use((cfg) => {
  const t = localStorage.getItem("aw_token");
  if (t) cfg.headers.Authorization = `Bearer ${t}`;
  return cfg;
});

export const login = (username, password) =>
  api.post("/auth/login", { username, password }).then((r) => r.data);

export const fetchAlerts = (params = {}) =>
  api.get("/alerts", { params }).then((r) => r.data);

export const updateAlert = (id, status) =>
  api.patch(`/alerts/${id}`, { status }).then((r) => r.data);

export const fetchCameras = () => api.get("/cameras").then((r) => r.data);

export const updateCameraConfig = (id, payload) =>
  api.put(`/cameras/${id}/config`, payload).then((r) => r.data);
