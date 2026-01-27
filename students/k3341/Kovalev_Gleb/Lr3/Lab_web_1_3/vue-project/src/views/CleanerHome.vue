<script setup>
import { ref, onMounted } from "vue";
import CleaningList from "../components/CleaningList.vue";
import { getCleanerRooms, getCleaningsByDate, addCleaning, deleteCleaning } from "../api/cleaner";

const rooms = ref([]);
const day = ref(new Date().toISOString().slice(0, 10)); // YYYY-MM-DD

const list = ref([]);
const loading = ref(true);
const error = ref("");
const ok = ref("");

const roomId = ref("");
const time = ref("12:00");
const status = ref("Убран");

function niceError(e) {
  const d = e?.response?.data;
  if (d?.detail) return d.detail;
  return d ? JSON.stringify(d) : "Ошибка";
}

async function loadRooms() {
  try {
    rooms.value = await getCleanerRooms();
  } catch (e) {
    error.value = niceError(e);
  }
}

async function loadCleanings() {
  loading.value = true;
  error.value = "";
  ok.value = "";
  try {
    const res = await getCleaningsByDate(day.value);
    list.value = res.items || [];
  } catch (e) {
    error.value = niceError(e);
  } finally {
    loading.value = false;
  }
}

async function createCleaning() {
  error.value = "";
  ok.value = "";

  if (!roomId.value) {
    error.value = "Выберите номер.";
    return;
  }

  try {
    await addCleaning({
        room: Number(roomId.value),
        cleaning_time: time.value,
        date: day.value,
        cleaning_status: status.value,
    });

    ok.value = "Запись добавлена.";
    await loadRooms();      // ✅ обновить список доступных (неубранных) номеров
    await loadCleanings();
  } catch (e) {
    error.value = niceError(e);
  }
}

async function onDelete(item) {
  error.value = "";
  ok.value = "";
  try {
    await deleteCleaning(item.id_cleaning);
    ok.value = "Удалено.";
    await loadRooms();
    await loadCleanings();
  } catch (e) {
    error.value = niceError(e);
  }
}

onMounted(async () => {
  await loadRooms();
  await loadCleanings();
});
</script>

<template>
  <div style="max-width:900px; margin:24px auto; padding:0 16px;">
    <h2>Уборки</h2>

    <div style="border:1px solid #ddd; border-radius:12px; padding:12px; margin-top:12px;">
      <h3 style="margin:0 0 10px;">Добавить уборку</h3>

      <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:end;">
        <label>
          День<br />
          <input type="date" v-model="day" @change="loadCleanings" />
        </label>

        <label>
          Номер<br />
          <select v-model="roomId">
            <option value="">-- выбрать --</option>
            <option v-for="r in rooms" :key="r.id_number" :value="r.id_number">
              №{{ r.room_number }} ({{ r.room_type?.name }})
            </option>
          </select>
        </label>

        <label>
          Время<br />
          <input type="time" v-model="time" />
        </label>

        <label>
          Статус<br />
          <select v-model="status">
            <option>Убран</option>
            <option>Не убран</option>
          </select>
        </label>

        <button
          @click="createCleaning"
          style="border:1px solid #ddd; background:white; padding:6px 10px; border-radius:8px; cursor:pointer;"
        >
          Сохранить
        </button>
      </div>

      <p v-if="ok" style="color:#0a7a0a; margin-top:10px;">{{ ok }}</p>
      <p v-if="error" style="color:#b00020; margin-top:10px;">{{ error }}</p>
    </div>

    <h3 style="margin-top:16px;">Список уборок за день</h3>
    <p v-if="loading">Загрузка...</p>

    <CleaningList v-if="!loading" :items="list" :onDelete="onDelete" />
  </div>
</template>