<script setup>
import { onMounted, ref } from "vue";
import { useRoute } from "vue-router";
import { getHotelRoomTypes } from "../api/hotels";

const route = useRoute();
const data = ref(null);
const loading = ref(true);
const error = ref("");

const hotelFallback =
  "https://via.placeholder.com/1200x500?text=Hotel";
const typeFallback =
  "https://via.placeholder.com/800x400?text=Room+Type";

onMounted(async () => {
  try {
    data.value = await getHotelRoomTypes(route.params.id);
  } catch (e) {
    error.value = e?.response?.data ? JSON.stringify(e.response.data) : "Ошибка загрузки отеля";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div style="max-width: 900px; margin: 24px auto; padding: 0 16px;">
    <p><RouterLink to="/">← Все отели</RouterLink></p>

    <p v-if="loading">Загрузка...</p>
    <p v-if="error" style="color: red;">{{ error }}</p>

    <div v-if="data">
      <!-- Карточка отеля -->
      <div style="border: 1px solid #ddd; border-radius: 12px; overflow: hidden;">
        <img
          :src="data.hotel.image_url || hotelFallback"
          alt="hotel"
          style="width: 100%; height: 220px; object-fit: cover; display: block;"
        />
        <div style="padding: 16px;">
          <h2 style="margin: 0 0 8px;">{{ data.hotel.name }}</h2>
          <div><b>Город:</b> {{ data.hotel.city }}</div>
          <div><b>Адрес:</b> {{ data.hotel.address }}</div>
          <div><b>Номеров всего:</b> {{ data.hotel.num_of_rooms }}</div>
        </div>
      </div>

      <h3 style="margin-top: 18px;">Типы номеров</h3>

      <div style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px;">
        <RouterLink
          v-for="t in data.room_types"
          :key="t.id_type"
          :to="`/hotels/${data.hotel.id_hotel}/types/${t.id_type}`"
          style="text-decoration: none; color: inherit;"
        >
          <div
            style="
              border: 1px solid #ddd;
              border-radius: 12px;
              padding: 12px;
              cursor: pointer;
              transition: transform 0.12s ease, box-shadow 0.12s ease;
            "
            @mouseover="$event.currentTarget.style.transform='scale(1.01)'; $event.currentTarget.style.boxShadow='0 6px 18px rgba(0,0,0,0.08)'"
            @mouseout="$event.currentTarget.style.transform='scale(1)'; $event.currentTarget.style.boxShadow='none'"
          >
            <img
              :src="t.image_url || typeFallback"
              alt="room type"
              style="width: 100%; height: 120px; object-fit: cover; border-radius: 10px; display: block; margin-bottom: 8px;"
            />

            <h4 style="margin: 0 0 8px;">{{ t.name }}</h4>
            <div>Мест: <b>{{ t.num_of_places }}</b></div>
            <div>Цена/сутки: <b>{{ t.base_price }}</b></div>
            <div>Всего номеров: {{ t.total_rooms }}</div>
            <div>Свободных сейчас: <b>{{ t.free_rooms }}</b></div>
          </div>
        </RouterLink>
      </div>
    </div>
  </div>
</template>