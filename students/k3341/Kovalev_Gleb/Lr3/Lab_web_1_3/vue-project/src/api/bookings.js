import { http } from "./http";

export async function getMyBookings() {
  const res = await http.get("/api/client/my-bookings/");
  return res.data;
}

export async function cancelBooking(id) {
  const res = await http.post(`/api/client/bookings/${id}/cancel/`);
  return res.data;
}