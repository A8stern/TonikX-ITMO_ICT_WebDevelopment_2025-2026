import { ref } from "vue";

export const token = ref(localStorage.getItem("token") || "");
export const role = ref(localStorage.getItem("role") || "");

export function setToken(value) {
  token.value = value || "";
  if (token.value) localStorage.setItem("token", token.value);
  else localStorage.removeItem("token");
}

export function setRole(value) {
  role.value = value || "";
  if (role.value) localStorage.setItem("role", role.value);
  else localStorage.removeItem("role");
}

export function clearAuth() {
  setToken("");
  setRole("");
}