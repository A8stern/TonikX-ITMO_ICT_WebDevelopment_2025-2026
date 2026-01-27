import { http } from "./http";
import { setToken, setRole, clearAuth } from "../stores/authStore";

export async function me() {
  const res = await http.get("/auth/users/me/");
  return res.data;
}

export async function login({ username, password }) {
  const res = await http.post("/auth/token/login/", { username, password });
  setToken(res.data.auth_token);

  const u = await me();
  setRole(u.role || "");
  return u;
}

export async function registerClient({ username, password, email }) {
  const res = await http.post("/auth/client/register/", { username, password, email });
  setToken(res.data.auth_token);

  const u = await me();
  setRole(u.role || "");
  return u;
}

export async function registerStaff({ username, password, email, code, hotel_id, role, full_name }) {
  const res = await http.post("/auth/staff/register/", {
    username, password, email, code, hotel_id, role, full_name
  });
  setToken(res.data.auth_token);

  const u = await me();
  setRole(u.role || "");
  return u;
}

export async function logout() {
  try {
    await http.post("/auth/token/logout/");
  } catch (e) {
  } finally {
    clearAuth();
  }
}