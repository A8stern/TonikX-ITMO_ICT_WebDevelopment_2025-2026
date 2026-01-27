<script setup>
import { ref, onMounted } from "vue";
import { getAdminRooms, getRoomTypes } from "../api/admin";

const loading = ref(true);
const error = ref("");

const page = ref(1);
const pageSize = ref(10);

const typeId = ref("");
const cleaned = ref(""); // "" | "true" | "false"
const status = ref("");  // "" | "Свободен" | "Занят"
const search = ref("");

const roomTypes = ref([]);

const count = ref(0);
const next = ref(null);
const previous = ref(null);
const rooms = ref([]);

function niceError(e) {
  const d = e?.response?.data;
  if (d?.detail) return d.detail;
  return d ? JSON.stringify(d) : "Ошибка";
}

async function loadTypes() {
  try {
    // /api/room-types/ может возвращать массив или {results:[]}
    const data = await getRoomTypes();
    roomTypes.value = Array.isArray(data) ? data : (data.results || []);
  } catch (e) {
    // не критично
    roomTypes.value = [];
  }
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    const data = await getAdminRooms({
      page: page.value,
      page_size: pageSize.value,
      type_id: typeId.value || undefined,
      cleaned: cleaned.value || undefined,
      status: status.value || undefined,
      search: search.value || undefined,
    });

    count.value = data.count;
    next.value = data.next;
    previous.value = data.previous;
    rooms.value = data.results;
  } catch (e) {
    error.value = niceError(e);
  } finally {
    loading.value = false;
  }
}

function applyFilters() {
  page.value = 1;
  load();
}

function resetFilters() {
  typeId.value = "";
  cleaned.value = "";
  status.value = "";
  search.value = "";
  page.value = 1;
  load();
}

function nextPage() {
  if (!next.value) return;
  page.value += 1;
  load();
}

function prevPage() {
  if (!previous.value) return;
  page.value -= 1;
  load();
}

onMounted(async () => {
  await loadTypes();
  await load();
});
</script>

<template>
  <div style="max-width:900px;margin:24px auto;padding:0 16px;">
    <h2>Номера</h2>

    <!-- Filters -->
    <div
      style="border:1px solid #ddd;border-radius:12px;padding:12px;margin-top:12px;display:flex;gap:12px;flex-wrap:wrap;align-items:end;"
    >
      <label>
        Тип номера<br />
        <select v-model="typeId" @change="applyFilters">
          <option value="">Все</option>
          <option v-for="t in roomTypes" :key="t.id_type" :value="t.id_type">
            {{ t.name }} ({{ t.num_of_places }} мест)
          </option>
        </select>
      </label>

      <label>
        Уборка<br />
        <select v-model="cleaned" @change="applyFilters">
          <option value="">Все</option>
          <option value="true">Убран</option>
          <option value="false">Не убран</option>
        </select>
      </label>

      <label>
        Статус<br />
        <select v-model="status" @change="applyFilters">
          <option value="">Все</option>
          <option value="Свободен">Свободен</option>
          <option value="Занят">Занят</option>
        </select>
      </label>

      <label>
        Поиск (номер)<br />
        <input v-model="search" placeholder="например 101" style="width:140px;" />
      </label>

      <button
        @click="applyFilters"
        style="border:1px solid #ddd;background:white;padding:6px 10px;border-radius:8px;cursor:pointer;"
      >
        Применить
      </button>

      <button
        @click="resetFilters"
        style="border:1px solid #ddd;background:white;padding:6px 10px;border-radius:8px;cursor:pointer;"
      >
        Сброс
      </button>

      <label>
        На странице<br />
        <select v-model="pageSize" @change="applyFilters">
          <option :value="5">5</option>
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select>
      </label>
    </div>

    <p v-if="loading" style="margin-top:12px;">Загрузка...</p>
    <p v-if="error" style="color:#b00020;margin-top:12px;">{{ error }}</p>

    <!-- List -->
    <div v-if="!loading && !error" style="display:grid; gap:10px; margin-top:12px;">
      <div
        v-for="r in rooms"
        :key="r.id_number"
        style="border:1px solid #ddd;border-radius:12px;padding:12px;display:flex;justify-content:space-between;gap:12px;flex-wrap:wrap;"
      >
        <div>
          <div style="font-size:16px;">
            <b>№{{ r.room_number }}</b> — {{ r.room_type?.name }} ({{ r.places_number }} мест)
          </div>

          <div style="margin-top:6px;color:#555;">
            Статус: <b>{{ r.status }}</b> ·
            Уборка: <b>{{ r.cleaned ? "Убран" : "Не убран" }}</b>
          </div>
        </div>

        <div style="color:#777; font-size:13px;">
          id: {{ r.id_number }}
        </div>
      </div>

      <p v-if="rooms.length === 0" style="color:#666;">Ничего не найдено.</p>
    </div>

    <!-- Pagination -->
    <div
      v-if="!loading && !error"
      style="display:flex;justify-content:space-between;align-items:center;margin-top:14px;"
    >
      <div style="color:#666;">
        Всего: {{ count }} · Страница: {{ page }}
      </div>

      <div style="display:flex; gap:10px;">
        <button
          @click="prevPage"
          :disabled="!previous"
          style="border:1px solid #ddd;background:white;padding:6px 10px;border-radius:8px;cursor:pointer;"
        >
          ← Назад
        </button>
        <button
          @click="nextPage"
          :disabled="!next"
          style="border:1px solid #ddd;background:white;padding:6px 10px;border-radius:8px;cursor:pointer;"
        >
          Вперёд →
        </button>
      </div>
    </div>
  </div>
</template>