import { http } from "./http";

// ---- ROOMS ----
export async function getAdminRooms(params) {
  const res = await http.get("/api/admin/rooms/", { params });
  return res.data; // {count,next,previous,results}
}

export async function getRoomTypes(params) {
  const res = await http.get("/api/room-types/", { params });
  return res.data; // массив или {results:[]}
}

// ---- BOOKINGS MANAGEMENT ----
export async function getAdminBookings(params) {
  const res = await http.get("/api/admin/bookings/", { params });
  return res.data; // {count,next,previous,results}
}

export async function patchAdminBooking(id, payload) {
  const res = await http.patch(`/api/admin/bookings/${id}/`, payload);
  return res.data;
}

export async function adminCheckin(id, payload) {
  const res = await http.post(`/api/admin/bookings/${id}/checkin/`, payload);
  return res.data;
}

export async function adminCheckout(id, payload = {}) {
  const res = await http.post(`/api/admin/bookings/${id}/checkout/`, payload);
  return res.data;
}

// ✅ новый эндпоинт смены номера (должен быть на бэке)
export async function adminChangeRoom(id, payload) {
  const res = await http.post(`/api/admin/bookings/${id}/change-room/`, payload);
  return res.data;
}

// ---- STAFF (cleaners) ----
export async function getAdminCleaners(params) {
  const res = await http.get("/api/admin/cleaners/", { params });
  return res.data; // {count,next,previous,results}
}

export async function getCleanerStats(staffId, start, end) {
  const res = await http.get(`/api/admin/cleaners/${staffId}/stats/`, { params: { start, end } });
  return res.data; // {cleanings_count,...}
}

export async function fireCleaner(staffId) {
  const res = await http.post(`/api/admin/cleaners/${staffId}/fire/`, {});
  return res.data;
}

// ---- CLEANINGS list/update ----
export async function getAdminCleanings(params) {
  const res = await http.get("/api/admin/cleanings/", { params });
  return res.data; // {count,next,previous,results}
}

export async function patchAdminCleaning(cleaningId, payload) {
  const res = await http.patch(`/api/admin/cleanings/${cleaningId}/`, payload);
  return res.data;
}