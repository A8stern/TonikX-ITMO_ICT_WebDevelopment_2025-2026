import { http } from "./http";

export async function getHotels() {
  const res = await http.get("/api/hotels/");
  return res.data;
}

export async function getHotel(id) {
  const res = await http.get(`/api/hotels/${id}/`);
  return res.data;
}

export async function getHotelRoomTypes(id) {
  const res = await http.get(`/api/hotels/${id}/room-types/`);
  return res.data;
}

export async function getRoomTypeDetail(hotelId, typeId) {
  const res = await http.get(`/api/hotels/${hotelId}/room-types/${typeId}/`);
  return res.data;
}

export async function getRoomTypeAvailability(hotelId, typeId, start, end) {
  const res = await http.get(`/api/hotels/${hotelId}/room-types/${typeId}/availability`, {
    params: { start, end },
  });
  return res.data;
}

export async function bookRoomType(hotelId, typeId, payload) {
  const res = await http.post(`/api/hotels/${hotelId}/room-types/${typeId}/book/`, payload);
  return res.data;
}