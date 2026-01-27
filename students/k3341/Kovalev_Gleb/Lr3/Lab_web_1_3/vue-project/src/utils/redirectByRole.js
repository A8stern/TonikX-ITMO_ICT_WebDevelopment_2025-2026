export function redirectPathByRole(role) {
  if (role === "cleaner") return "/cleaner";
  if (role === "admin") return "/admin/rooms";
  return "/";
}