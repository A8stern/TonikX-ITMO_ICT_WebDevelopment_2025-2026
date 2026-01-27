<script setup>
import { onMounted, ref } from "vue";
import { getHotels } from "../api/hotels";

const hotels = ref([]);
const loading = ref(true);
const error = ref("");

onMounted(async () => {
  try {
    hotels.value = await getHotels();
  } catch (e) {
    error.value = e?.response?.data ? JSON.stringify(e.response.data) : "Ошибка загрузки отелей";
  } finally {
    loading.value = false;
  }
});
</script>

<template>
  <div style="max-width: 900px; margin: 24px auto; padding: 0 16px;">
    <h1>Отели</h1>

    <p v-if="loading">Загрузка...</p>
    <p v-if="error" style="color: red;">{{ error }}</p>

    <div
      v-if="!loading && !error"
      style="display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr)); gap: 12px; margin-top: 16px;"
    >
      <RouterLink
        v-for="h in hotels"
        :key="h.id_hotel"
        :to="`/hotels/${h.id_hotel}`"
        style="text-decoration: none; color: inherit;"
      >
        <div
          style="
            border: 1px solid #ddd;
            border-radius: 10px;
            padding: 12px;
            cursor: pointer;
            transition: transform 0.12s ease, box-shadow 0.12s ease;
          "
          @mouseover="$event.currentTarget.style.transform='scale(1.01)'; $event.currentTarget.style.boxShadow='0 6px 18px rgba(0,0,0,0.08)'"
          @mouseout="$event.currentTarget.style.transform='scale(1)'; $event.currentTarget.style.boxShadow='none'"
        >
          <img
          :src="h.image_url || 'https://via.placeholder.com/600x300?text=Hotel'"
          alt="hotel"
          style="width: 100%; height: 140px; object-fit: cover; display: block;"
          />
          <h3 style="margin: 0 0 8px;">{{ h.name }}</h3>
          <div>Город: <b>{{ h.city }}</b></div>
          <div>Адрес: {{ h.address }}</div>
          <div>Номеров: {{ h.num_of_rooms }}</div>
        </div>
      </RouterLink>
    </div>
  </div>
</template>