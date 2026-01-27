<script setup>
import { ref, onMounted, watch } from "vue";
import {
  getAdminBookings,
  patchAdminBooking,
  adminCheckin,
  adminCheckout,
  adminChangeRoom,
  getAdminRooms,
  getRoomTypes,
} from "../api/admin";

const loading = ref(true);
const error = ref("");
const ok = ref("");

const page = ref(1);
const pageSize = ref(10);

const status = ref(""); // filter
const typeId = ref(""); // filter
const start = ref(""); // filter
const end = ref(""); // filter
const q = ref(""); // filter

const roomTypes = ref([]);
const rooms = ref([]);

const count = ref(0);
const next = ref(null);
const previous = ref(null);
const items = ref([]);

// UI state for per-row actions
const editMap = ref({}); // { [id_book]: { date_start, date_end, book_status } }
const roomPickMap = ref({}); // { [id_book]: room_id } (for checkin)
const changeRoomPickMap = ref({}); // { [id_book]: room_id } (for change-room)
const busyMap = ref({}); // { [id_book]: boolean }

function niceError(e) {
  const d = e?.response?.data;
  if (d?.detail) return d.detail;
  return d ? JSON.stringify(d) : "Ошибка";
}

async function loadTypes() {
  try {
    const data = await getRoomTypes();
    roomTypes.value = Array.isArray(data) ? data : data.results || [];
  } catch {
    roomTypes.value = [];
  }
}

async function loadRooms() {
  try {
    const data = await getAdminRooms({ page: 1, page_size: 500 });
    rooms.value = data.results || data;
  } catch {
    rooms.value = [];
  }
}

function initRowState(list) {
  for (const b of list) {
    if (!editMap.value[b.id_book]) {
      editMap.value[b.id_book] = {
        date_start: b.date_start,
        date_end: b.date_end,
        book_status: b.book_status,
      };
    }
    if (roomPickMap.value[b.id_book] === undefined) roomPickMap.value[b.id_book] = "";
    if (changeRoomPickMap.value[b.id_book] === undefined) changeRoomPickMap.value[b.id_book] = "";
    if (busyMap.value[b.id_book] === undefined) busyMap.value[b.id_book] = false;
  }
}

async function load() {
  loading.value = true;
  error.value = "";
  ok.value = "";
  try {
    const data = await getAdminBookings({
      page: page.value,
      page_size: pageSize.value,
      status: status.value || undefined,
      type_id: typeId.value || undefined,
      start: start.value || undefined,
      end: end.value || undefined,
      q: q.value || undefined,
    });

    count.value = data.count;
    next.value = data.next;
    previous.value = data.previous;
    items.value = data.results || [];

    initRowState(items.value);
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
  status.value = "";
  typeId.value = "";
  start.value = "";
  end.value = "";
  q.value = "";
  page.value = 1;
  load();
}

function prevPage() {
  if (!previous.value) return;
  page.value -= 1;
  load();
}
function nextPage() {
  if (!next.value) return;
  page.value += 1;
  load();
}

function isCheckedIn(b) {
  return b.book_status === "Заселен";
}

function roomsForCheckin(b) {
  // Заселение: только свободные комнаты того же типа
  return rooms.value.filter(
    (r) => String(r.room_type?.id_type) === String(b.room_type?.id_type) && r.status === "Свободен"
  );
}

function roomsForChangeRoom(b) {
  // Смена номера: свободные комнаты того же типа или выше.
  // "выше" — по местам ИЛИ цене (как на бэке, но бэк всё равно проверит)
  return rooms.value.filter((r) => {
    if (r.status !== "Свободен") return false;
    if (!r.room_type || !b.room_type) return false;

    const sameOrMorePlaces = (r.room_type.num_of_places ?? 0) >= (b.room_type.num_of_places ?? 0);
    const sameOrMorePrice = (r.room_type.base_price ?? 0) >= (b.room_type.base_price ?? 0);
    return sameOrMorePlaces && sameOrMorePrice;
  });
}

async function saveBooking(b) {
  const id = b.id_book;

  if (isCheckedIn(b)) {
    error.value = "Нельзя редактировать заселённую бронь. Можно только выселить или сменить номер.";
    return;
  }

  const payload = editMap.value[id];

  busyMap.value[id] = true;
  error.value = "";
  ok.value = "";
  try {
    await patchAdminBooking(id, payload);
    ok.value = `Бронь #${id} обновлена.`;
    await load();
  } catch (e) {
    error.value = niceError(e);
  } finally {
    busyMap.value[id] = false;
  }
}

async function doCheckin(b) {
  const id = b.id_book;
  const roomId = roomPickMap.value[id];

  if (!roomId) {
    error.value = "Выберите номер для заселения.";
    return;
  }

  busyMap.value[id] = true;
  error.value = "";
  ok.value = "";
  try {
    // backend сам: ставит booking.book_status=Заселен, room.status=Занят, payed=price
    await adminCheckin(id, { room_id: Number(roomId) });

    ok.value = `Заселили бронь #${id}. (Оплата поставлена = цене)`;
    await loadRooms();
    await load();
  } catch (e) {
    error.value = niceError(e);
  } finally {
    busyMap.value[id] = false;
  }
}

async function doCheckout(b) {
  const id = b.id_book;

  busyMap.value[id] = true;
  error.value = "";
  ok.value = "";
  try {
    // backend сам: booking=Выселен, room.status=Свободен, cleaned=false
    await adminCheckout(id, {});
    ok.value = `Выселили бронь #${id}.`;
    await loadRooms();
    await load();
  } catch (e) {
    error.value = niceError(e);
  } finally {
    busyMap.value[id] = false;
  }
}

async function doChangeRoom(b) {
  const id = b.id_book;
  const roomId = changeRoomPickMap.value[id];

  if (!roomId) {
    error.value = "Выберите новый номер.";
    return;
  }

  busyMap.value[id] = true;
  error.value = "";
  ok.value = "";
  try {
    await adminChangeRoom(id, { room_id: Number(roomId) });

    ok.value = `Номер для брони #${id} изменён.`;
    await loadRooms();
    await load();
  } catch (e) {
    error.value = niceError(e);
  } finally {
    busyMap.value[id] = false;
  }
}

onMounted(async () => {
  await loadTypes();
  await loadRooms();
  await load();
});

watch(pageSize, () => {
  page.value = 1;
  load();
});
</script>

<template>
  <div style="max-width: 1000px; margin: 24px auto; padding: 0 16px;">
    <h2>Заселения / Бронирования</h2>

    <!-- Filters -->
    <div
      style="
        border: 1px solid #ddd;
        border-radius: 12px;
        padding: 12px;
        margin-top: 12px;
        display: flex;
        gap: 12px;
        flex-wrap: wrap;
        align-items: end;
      "
    >
      <label>
        Статус<br />
        <select v-model="status" @change="applyFilters">
          <option value="">Все (кроме Отменен/Выселен)</option>
          <option>Забронирован</option>
          <option>Ожидает оплату</option>
          <option>Заселен</option>
        </select>
      </label>

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
        Период от<br />
        <input type="date" v-model="start" />
      </label>

      <label>
        до<br />
        <input type="date" v-model="end" />
      </label>

      <label>
        Поиск (ФИО/email)<br />
        <input v-model="q" placeholder="Иван / ivan@" style="width: 180px;" />
      </label>

      <button
        @click="applyFilters"
        style="border: 1px solid #ddd; background: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;"
      >
        Применить
      </button>

      <button
        @click="resetFilters"
        style="border: 1px solid #ddd; background: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;"
      >
        Сброс
      </button>

      <label>
        На странице<br />
        <select v-model="pageSize">
          <option :value="5">5</option>
          <option :value="10">10</option>
          <option :value="20">20</option>
          <option :value="50">50</option>
        </select>
      </label>
    </div>

    <p v-if="loading" style="margin-top: 12px;">Загрузка...</p>
    <p v-if="ok" style="color: #0a7a0a; margin-top: 12px;">{{ ok }}</p>
    <p v-if="error" style="color: #b00020; margin-top: 12px;">{{ error }}</p>

    <!-- List -->
    <div v-if="!loading && !error" style="display: grid; gap: 12px; margin-top: 12px;">
      <div
        v-for="b in items"
        :key="b.id_book"
        style="border: 1px solid #ddd; border-radius: 12px; padding: 12px;"
      >
        <div style="display: flex; justify-content: space-between; gap: 12px; flex-wrap: wrap;">
          <div>
            <div style="font-size: 16px;">
              <b>#{{ b.id_book }}</b> — <b>{{ b.book_status }}</b>
              <span v-if="b.room_number"> · Номер: <b>№{{ b.room_number }}</b></span>
            </div>

            <div style="margin-top: 6px; color: #555;">
              Клиент: <b>{{ b.client?.surname }} {{ b.client?.name }}</b>
              <span v-if="b.client?.email"> · {{ b.client.email }}</span>
            </div>

            <div style="margin-top: 6px; color: #555;">
              Тип: <b>{{ b.room_type?.name }}</b> · Цена: <b>{{ b.price }}</b> · Оплачено: <b>{{ b.payed }}</b>
            </div>

            <div style="margin-top: 6px; color: #555;">
              Даты: <b>{{ b.date_start }}</b> → <b>{{ b.date_end }}</b>
            </div>
          </div>

          <div style="color: #777; font-size: 13px;">
            Отель: {{ b.hotel?.name }}
          </div>
        </div>

        <!-- Edit section -->
        <div
          style="
            margin-top: 10px;
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
            align-items: end;
            border-top: 1px solid #eee;
            padding-top: 10px;
          "
        >
          <!-- Если НЕ заселен — можно редактировать -->
          <template v-if="!isCheckedIn(b)">
            <label>
              Статус<br />
              <select v-model="editMap[b.id_book].book_status">
                <option>Забронирован</option>
                <option>Ожидает оплату</option>
                <!-- Заселен/Выселен — только через кнопки -->
              </select>
            </label>

            <label>
              Заезд<br />
              <input type="date" v-model="editMap[b.id_book].date_start" />
            </label>

            <label>
              Выезд<br />
              <input type="date" v-model="editMap[b.id_book].date_end" />
            </label>

            <button
              @click="saveBooking(b)"
              :disabled="busyMap[b.id_book]"
              style="border: 1px solid #ddd; background: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;"
            >
              {{ busyMap[b.id_book] ? "Сохранение..." : "Сохранить" }}
            </button>

            <label>
              Номер для заселения<br />
              <select v-model="roomPickMap[b.id_book]">
                <option value="">-- выбрать --</option>
                <option v-for="r in roomsForCheckin(b)" :key="r.id_number" :value="r.id_number">
                  №{{ r.room_number }}
                </option>
              </select>
            </label>

            <button
              @click="doCheckin(b)"
              :disabled="busyMap[b.id_book]"
              style="border: 1px solid #ddd; background: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;"
            >
              Заселить
            </button>
          </template>

          <!-- Если ЗАСЕЛЕН — только выселить или сменить номер -->
          <template v-else>
            <div style="color:#666; font-size:13px; margin-right: 8px;">
              Заселено: редактирование запрещено.
            </div>

            <label>
              Сменить номер<br />
              <select v-model="changeRoomPickMap[b.id_book]">
                <option value="">-- выбрать --</option>
                <option v-for="r in roomsForChangeRoom(b)" :key="r.id_number" :value="r.id_number">
                  №{{ r.room_number }} ({{ r.room_type?.name }})
                </option>
              </select>
            </label>

            <button
              @click="doChangeRoom(b)"
              :disabled="busyMap[b.id_book]"
              style="border: 1px solid #ddd; background: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;"
            >
              Сменить
            </button>

            <button
              @click="doCheckout(b)"
              :disabled="busyMap[b.id_book]"
              style="border: 1px solid #ddd; background: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;"
            >
              Выселить
            </button>
          </template>
        </div>
      </div>

      <p v-if="items.length === 0" style="color: #666;">Ничего не найдено.</p>
    </div>

    <!-- Pagination -->
    <div
      v-if="!loading && !error"
      style="display: flex; justify-content: space-between; align-items: center; margin-top: 14px;"
    >
      <div style="color: #666;">Всего: {{ count }} · Страница: {{ page }}</div>

      <div style="display: flex; gap: 10px;">
        <button
          @click="prevPage"
          :disabled="!previous"
          style="border: 1px solid #ddd; background: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;"
        >
          ← Назад
        </button>
        <button
          @click="nextPage"
          :disabled="!next"
          style="border: 1px solid #ddd; background: white; padding: 6px 10px; border-radius: 8px; cursor: pointer;"
        >
          Вперёд →
        </button>
      </div>
    </div>
  </div>
</template>