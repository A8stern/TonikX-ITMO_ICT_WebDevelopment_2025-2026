<script setup>
import { ref, onMounted, computed } from "vue";
import { role } from "../stores/authStore";
import { me } from "../api/auth";

import { getMyBookings, cancelBooking } from "../api/bookings";
import { getCleaningsByDate, deleteCleaning } from "../api/cleaner";
import CleaningList from "../components/CleaningList.vue";

const userRole = computed(() => role.value || "client");
const meData = ref(null);

const loading = ref(true);
const error = ref("");
const ok = ref("");

const bookings = ref([]);
const day = ref(new Date().toISOString().slice(0, 10));
const cleanings = ref([]);

function niceError(e) {
  const d = e?.response?.data;
  if (d?.detail) return d.detail;
  return d ? JSON.stringify(d) : "Ошибка.";
}

async function load() {
  loading.value = true;
  error.value = "";
  ok.value = "";

  try {
    meData.value = await me();

    if (userRole.value === "cleaner") {
      const res = await getCleaningsByDate(day.value);
      cleanings.value = res.items || [];
    } else if (userRole.value === "client") {
      bookings.value = await getMyBookings();
    } else if (userRole.value === "admin") {
      // админский профиль пока без списков — просто показываем отель
    }
  } catch (e) {
    error.value = niceError(e);
  } finally {
    loading.value = false;
  }
}

async function onCancelBooking(id) {
  try {
    await cancelBooking(id);
    ok.value = "Бронь отменена.";
    await load();
  } catch (e) {
    error.value = niceError(e);
  }
}

async function onDeleteCleaning(item) {
  try {
    await deleteCleaning(item.id_cleaning);
    ok.value = "Запись удалена.";
    await load();
  } catch (e) {
    error.value = niceError(e);
  }
}

onMounted(load);
</script>

<template>
  <div style="max-width:900px; margin:24px auto; padding:0 16px;">
    <h2 v-if="userRole==='admin'">Профиль администратора</h2>
    <h2 v-else-if="userRole==='cleaner'">Профиль уборщика</h2>
    <h2 v-else>Профиль клиента</h2>

    <p v-if="loading">Загрузка...</p>
    <p v-if="ok" style="color:#0a7a0a;">{{ ok }}</p>
    <p v-if="error" style="color:#b00020;">{{ error }}</p>

    <!-- ✅ Блок отеля для admin/cleaner -->
    <div
      v-if="!loading && !error && (userRole==='admin' || userRole==='cleaner')"
      style="border:1px solid #ddd; border-radius:12px; padding:12px; margin-top:12px;"
    >
      <div v-if="meData?.hotel">
        <b>Отель:</b> {{ meData.hotel.name }} ({{ meData.hotel.city }})<br />
        <b>Адрес:</b> {{ meData.hotel.address }}
      </div>
      <div v-else style="color:#666;">
        Отель не привязан к профилю.
      </div>
    </div>

    <!-- CLEANER -->
    <div v-if="!loading && !error && userRole==='cleaner'" style="margin-top:12px;">
      <div style="display:flex; gap:12px; align-items:end; flex-wrap:wrap; margin-bottom:12px;">
        <label>День<br /><input type="date" v-model="day" @change="load" /></label>
      </div>
      <CleaningList :items="cleanings" :onDelete="onDeleteCleaning" />
    </div>

    <!-- CLIENT -->
    <div v-if="!loading && !error && userRole==='client'" style="margin-top:12px;">
      <h3>Мои бронирования</h3>
      <div style="display:grid; gap:12px; margin-top:12px;">
        <div v-for="b in bookings" :key="b.id_book" style="border:1px solid #ddd; border-radius:12px; padding:12px;">
          <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap;">
            <div>
              <div><b>Статус:</b> {{ b.book_status }}</div>
              <div><b>Даты:</b> {{ b.date_start }} → {{ b.date_end }}</div>
              <div v-if="b.hotel"><b>Отель:</b> {{ b.hotel.name }} ({{ b.hotel.city }})</div>
              <div v-if="b.room_type"><b>Тип:</b> {{ b.room_type.name }}</div>
            </div>

            <button
              v-if="b.book_status === 'Забронирован' || b.book_status === 'Ожидает оплату'"
              @click="onCancelBooking(b.id_book)"
              style="border:1px solid #ddd; background:white; padding:6px 10px; border-radius:8px; cursor:pointer;"
            >
              Отменить
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- ADMIN: пока можно добавить ссылки -->
    <div v-if="!loading && !error && userRole==='admin'" style="margin-top:12px; color:#666;">
      Перейдите в разделы: Номера / Заселения / Персонал вверху.
    </div>
  </div>
</template>