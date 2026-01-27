import { http } from "./http";

export async function getCleanerRooms() {
  const res = await http.get("/api/cleaner/rooms/");
  return res.data;
}

export async function getCleaningsByDate(date) {
  const res = await http.get("/api/cleaner/cleanings/", { params: { date } });
  return res.data;
}

export async function addCleaning(payload) {
  const res = await http.post("/api/cleaner/cleanings/", payload);
  return res.data;
}

export async function deleteCleaning(id) {
  const res = await http.delete(`/api/cleaner/cleanings/${id}/`);
  return res.data;
}