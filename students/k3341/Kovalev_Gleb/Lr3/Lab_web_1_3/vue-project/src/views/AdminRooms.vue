<script setup>
import { ref, onMounted, watch } from "vue";
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
  if (!e?.response) return "Нет соединения с сервером. Проверь, что Django запущен на :8000.";
  if (d?.detail) return d.detail;
  return d ? JSON.stringify(d) : "Ошибка";
}

function badgeStatusStyle(s) {
  return s === "Свободен"
    ? "background: rgba(110,231,183,.22); border-color: rgba(110,231,183,.35); color:#0f6a44;"
    : "background: rgba(239,68,68,.12); border-color: rgba(239,68,68,.25); color:#a01414;";
}

function badgeCleanStyle(v) {
  // v может быть true / false / null
  return v === true
    ? "background: rgba(110,231,183,.22); border-color: rgba(110,231,183,.35); color:#0f6a44;"
    : "background: rgba(249,168,212,.18); border-color: rgba(249,168,212,.28); color:#8a1f4f;";
}

async function loadTypes() {
  try {
    const data = await getRoomTypes();
    roomTypes.value = Array.isArray(data) ? data : (data.results || []);
  } catch {
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
    rooms.value = data.results || [];
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

watch(pageSize, () => {
  page.value = 1;
  load();
});

onMounted(async () => {
  await loadTypes();
  await load();
});
</script>

<template>
  <div class="container" style="padding-top: 18px; padding-bottom: 28px; max-width: 1100px;">
    <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:end;">
      <div>
        <h2 class="h1" style="font-size:24px;">Номера</h2>
        <div class="muted" style="margin-top:6px;">
          Фильтры по типу, уборке и статусу + поиск по номеру
        </div>
      </div>

      <span class="badge badge-muted">
        Всего: <b style="color:var(--text)">{{ count }}</b>
      </span>
    </div>

    <!-- Filters (как в Персонале) -->
    <div class="card card-pad" style="margin-top: 12px;">
      <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:end;">
        <div>
          <h3 class="h2">Фильтры</h3>
          <div class="muted" style="margin-top:6px;">
            “Не убран” включает <b style="color:var(--text)">false</b> и <b style="color:var(--text)">null</b>
          </div>
        </div>

        <label style="display:grid; gap:6px;">
          <span class="muted" style="font-size:13px;">На странице</span>
          <select v-model="pageSize">
            <option :value="5">5</option>
            <option :value="10">10</option>
            <option :value="20">20</option>
            <option :value="50">50</option>
          </select>
        </label>
      </div>

      <div class="hr"></div>

      <div style="display:flex; gap:12px; flex-wrap:wrap; align-items:end;">
        <label style="display:grid; gap:6px; min-width: 240px;">
          <span class="muted" style="font-size:13px;">Тип номера</span>
          <select v-model="typeId" @change="applyFilters">
            <option value="">Все</option>
            <option v-for="t in roomTypes" :key="t.id_type" :value="t.id_type">
              {{ t.name }} ({{ t.num_of_places }} мест)
            </option>
          </select>
        </label>

        <label style="display:grid; gap:6px;">
          <span class="muted" style="font-size:13px;">Уборка</span>
          <select v-model="cleaned" @change="applyFilters">
            <option value="">Все</option>
            <option value="true">Убран</option>
            <option value="false">Не убран</option>
          </select>
        </label>

        <label style="display:grid; gap:6px;">
          <span class="muted" style="font-size:13px;">Статус</span>
          <select v-model="status" @change="applyFilters">
            <option value="">Все</option>
            <option value="Свободен">Свободен</option>
            <option value="Занят">Занят</option>
          </select>
        </label>

        <label style="display:grid; gap:6px;">
          <span class="muted" style="font-size:13px;">Поиск (номер)</span>
          <input class="input" v-model="search" placeholder="например 101" style="width:180px;" />
        </label>

        <button class="btn btn-primary" @click="applyFilters">Применить</button>
        <button class="btn" @click="resetFilters">Сброс</button>
      </div>
    </div>

    <!-- Loading / Error -->
    <div v-if="loading" class="card card-pad" style="margin-top: 12px;">
      Загрузка...
    </div>

    <div
      v-if="error"
      class="card card-pad"
      style="margin-top:12px; border-color: rgba(239,68,68,.25); background: rgba(239,68,68,.08); color:#a01414; box-shadow:none;"
    >
      <b>Ошибка.</b> {{ error }}
    </div>

    <!-- List (как блоки в Персонале) -->
    <div v-if="!loading && !error" class="card card-pad" style="margin-top: 12px;">
      <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:end;">
        <div>
          <h3 class="h2">Список номеров</h3>
          <div class="muted" style="margin-top:6px;">
            Страница {{ page }} · Показано: <b style="color:var(--text)">{{ rooms.length }}</b>
          </div>
        </div>

        <span class="badge badge-muted">
          Отфильтровано: <b style="color:var(--text)">{{ count }}</b>
        </span>
      </div>

      <div class="hr"></div>

      <div style="display:grid; gap:12px;">
        <div
          v-for="r in rooms"
          :key="r.id_number"
          class="card card-pad"
          style="box-shadow:none; display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:flex-start;"
        >
          <div style="display:grid; gap:8px;">
            <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
              <span class="badge">
                Номер <b style="color:var(--text)">№{{ r.room_number }}</b>
              </span>

              <span class="badge badge-muted">
                {{ r.room_type?.name }} · {{ r.places_number }} мест
              </span>

              <span class="badge" :style="badgeStatusStyle(r.status)">
                <b style="color:inherit">{{ r.status }}</b>
              </span>

              <span class="badge" :style="badgeCleanStyle(r.cleaned)">
                Уборка: <b style="color:inherit">{{ r.cleaned === true ? "Убран" : "Не убран" }}</b>
              </span>
            </div>

            <div class="muted" style="font-size:13px;">
              id: <b style="color:var(--text)">{{ r.id_number }}</b>
            </div>
          </div>
        </div>

        <div v-if="rooms.length === 0" class="card card-pad muted" style="box-shadow:none;">
          Ничего не найдено.
        </div>
      </div>

      <!-- Pagination (как в Персонале) -->
      <div
        class="card card-pad"
        style="margin-top:12px; display:flex; justify-content:space-between; align-items:center; gap:12px; flex-wrap:wrap; box-shadow:none;"
      >
        <div class="muted">
          Всего: <b style="color:var(--text)">{{ count }}</b> · Страница:
          <b style="color:var(--text)">{{ page }}</b>
        </div>

        <div style="display:flex; gap:10px;">
          <button class="btn" @click="prevPage" :disabled="!previous">← Назад</button>
          <button class="btn" @click="nextPage" :disabled="!next">Вперёд →</button>
        </div>
      </div>
    </div>
  </div>
</template>