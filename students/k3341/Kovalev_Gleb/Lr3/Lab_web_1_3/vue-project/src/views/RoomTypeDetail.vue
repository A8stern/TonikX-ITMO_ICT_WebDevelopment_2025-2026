<script setup>
import { ref, onMounted, computed } from "vue";
import { useRoute } from "vue-router";
import { getRoomTypeDetail, getRoomTypeAvailability, bookRoomType } from "../api/hotels";
import { getMyBookings, cancelBooking } from "../api/bookings";

const route = useRoute();
const hotelId = route.params.hotelId;
const typeId = route.params.typeId;

const data = ref(null);
const loading = ref(true);
const error = ref("");

const dateStart = ref("");
const dateEnd = ref("");

const availability = ref(null);

const errAvailability = ref("");
const errBooking = ref("");
const successMessage = ref("");

const myBooking = ref(null);
const cancelling = ref(false);

function niceError(e) {
  const status = e?.response?.status;
  const data = e?.response?.data;

  if (status === 403) return "Нет прав. Войдите как клиент.";
  if (status === 401) return "Вы не авторизованы. Сначала войдите в аккаунт.";
  if (data?.detail) return data.detail;
  if (typeof data === "string") return data;
  if (data) return JSON.stringify(data);
  return "Произошла ошибка.";
}

const canCancel = computed(() => {
  return (
    !!myBooking.value &&
    (myBooking.value.book_status === "Забронирован" ||
      myBooking.value.book_status === "Ожидает оплату")
  );
});

async function loadMyBooking() {
  myBooking.value = null;
  try {
    const list = await getMyBookings();
    myBooking.value =
      list.find(
        (b) =>
          (b.book_status === "Забронирован" || b.book_status === "Ожидает оплату") &&
          String(b.hotel?.id_hotel) === String(hotelId) &&
          String(b.room_type?.id_type) === String(typeId)
      ) || null;
  } catch (e) {
    myBooking.value = null;
  }
}

async function load() {
  loading.value = true;
  error.value = "";
  try {
    data.value = await getRoomTypeDetail(hotelId, typeId);
  } catch (e) {
    error.value = niceError(e);
  } finally {
    loading.value = false;
  }
}

async function checkAvailability() {
  errAvailability.value = "";
  errBooking.value = "";
  successMessage.value = "";
  availability.value = null;

  if (!dateStart.value || !dateEnd.value) {
    errAvailability.value = "Выберите даты заезда и выезда.";
    return;
  }
  if (dateEnd.value < dateStart.value) {
    errAvailability.value = "Дата выезда должна быть позже или равна дате заезда.";
    return;
  }

  try {
    availability.value = await getRoomTypeAvailability(hotelId, typeId, dateStart.value, dateEnd.value);
  } catch (e) {
    errAvailability.value = niceError(e);
  }
}

const canPressBook = computed(() => {
  if (myBooking.value) return false;      // есть активная бронь
  if (!availability.value) return false; // не проверили
  return !!availability.value.can_book;
});

async function book() {
  errBooking.value = "";
  successMessage.value = "";

  if (myBooking.value) {
    errBooking.value = "У вас уже есть бронь на этот тип номера. Можете отменить её или посмотреть в профиле.";
    return;
  }
  if (!dateStart.value || !dateEnd.value) {
    errBooking.value = "Сначала выберите даты.";
    return;
  }
  if (!availability.value) {
    errBooking.value = "Сначала нажмите «Проверить».";
    return;
  }
  if (!availability.value.can_book) {
    errBooking.value = "На выбранные даты нет свободных номеров.";
    return;
  }

  try {
    const res = await bookRoomType(hotelId, typeId, {
      date_start: dateStart.value,
      date_end: dateEnd.value,
      type_of_payment: "Карта",
    });

    successMessage.value = `Бронь создана: #${res.id_book} (${res.book_status})`;

    await checkAvailability();
    await loadMyBooking();
  } catch (e) {
    errBooking.value = niceError(e);
  }
}

async function cancelMyBooking() {
  errBooking.value = "";
  successMessage.value = "";

  if (!myBooking.value) return;

  if (!canCancel.value) {
    errBooking.value = "Эту бронь нельзя отменить по текущему статусу.";
    return;
  }

  cancelling.value = true;
  try {
    await cancelBooking(myBooking.value.id_book);
    successMessage.value = "Бронь отменена.";

    // обновим UI
    await loadMyBooking();
    if (dateStart.value && dateEnd.value) {
      await checkAvailability();
    } else {
      availability.value = null;
    }
  } catch (e) {
    errBooking.value = niceError(e);
  } finally {
    cancelling.value = false;
  }
}

onMounted(async () => {
  await load();
  await loadMyBooking();
});
</script>

<template>
  <div style="max-width: 900px; margin: 24px auto; padding: 0 16px;">
    <p><RouterLink :to="`/hotels/${hotelId}`">← Назад к отелю</RouterLink></p>

    <p v-if="loading">Загрузка...</p>
    <p v-if="error" style="color:#b00020;">{{ error }}</p>

    <div v-if="data">
      <h2 style="margin: 8px 0 10px;">{{ data.room_type.name }}</h2>

      <img
        :src="data.room_type.image_url"
        alt="room type"
        style="
          width: 100%;
          max-width: 520px;
          height: 220px;
          object-fit: cover;
          border-radius: 12px;
          display: block;
          border: 1px solid #ddd;
        "
      />

      <div style="margin-top: 12px;">
        <div><b>Мест:</b> {{ data.room_type.num_of_places }}</div>
        <div><b>Цена/сутки:</b> {{ data.room_type.base_price }}</div>
      </div>

      <!-- Блок существующей брони -->
      <div
        v-if="myBooking"
        style="margin-top: 14px; padding: 12px; border: 1px solid #ddd; border-radius: 10px; background: #fafafa;"
      >
        <div style="display:flex; justify-content:space-between; gap:12px; flex-wrap:wrap; align-items:flex-start;">
          <div>
            <div>
              У вас уже есть бронь на этот тип:
              <b>#{{ myBooking.id_book }}</b>
            </div>
            <div style="margin-top: 6px;">
              <b>Статус:</b> {{ myBooking.book_status }}<br />
              <b>Даты:</b> {{ myBooking.date_start }} → {{ myBooking.date_end }}
            </div>
            <div style="margin-top: 6px; font-size: 13px; color: #666;">
              Пока бронь активна — новую создать нельзя.
            </div>
          </div>

          <button
            v-if="canCancel"
            @click="cancelMyBooking"
            :disabled="cancelling"
            style="border:1px solid #ddd; background:white; padding:6px 10px; border-radius:8px; cursor:pointer;"
          >
            {{ cancelling ? "Отмена..." : "Отменить бронь" }}
          </button>
        </div>
      </div>

      <h3 style="margin-top: 18px;">Снять на период</h3>

      <div style="display:flex; gap:12px; align-items:end; flex-wrap:wrap;">
        <label>
          Заезд<br />
          <input type="date" v-model="dateStart" @change="checkAvailability" />
        </label>

        <label>
          Выезд<br />
          <input type="date" v-model="dateEnd" @change="checkAvailability" />
        </label>

        <button
          @click="checkAvailability"
          style="border:1px solid #ddd; background:white; padding:6px 10px; border-radius:8px; cursor:pointer;"
        >
          Проверить
        </button>

        <button
          @click="book"
          :disabled="!canPressBook"
          style="border:1px solid #ddd; background:white; padding:6px 10px; border-radius:8px; cursor:pointer;"
        >
          Забронировать
        </button>
      </div>

      <p v-if="errAvailability" style="color:#b00020; margin-top:10px;">
        {{ errAvailability }}
      </p>

      <div
        v-if="availability"
        style="margin-top: 10px; padding: 10px; border: 1px solid #eee; border-radius: 10px;"
      >
        <div><b>Минимум свободных на период:</b> {{ availability.min_free_rooms }}</div>
        <div><b>Можно забронировать:</b> {{ availability.can_book ? "Да" : "Нет" }}</div>
      </div>

      <p v-if="errBooking" style="color:#b00020; margin-top:10px;">
        {{ errBooking }}
      </p>

      <p v-if="successMessage" style="color:#0a7a0a; margin-top:10px;">
        {{ successMessage }}
      </p>
    </div>
  </div>
</template>