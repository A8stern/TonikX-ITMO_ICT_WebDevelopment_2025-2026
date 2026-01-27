<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { registerStaff, login } from "../api/auth";
import { getHotels } from "../api/hotels";
import { me } from "../api/auth";
import { redirectPathByRole } from "../utils/redirectByRole";

const router = useRouter();

const username = ref("");
const password = ref("");
const role = ref("cleaner"); // "admin" | "cleaner"
const hotel_id = ref("");
const code = ref(""); // STAFF_REGISTRATION_CODE

const hotels = ref([]);
const error = ref("");
const ok = ref("");

onMounted(async () => {
  try {
    hotels.value = await getHotels();
  } catch (e) {
    // если отели закрыты авторизацией, можно временно сделать endpoint публичным или логиниться сначала
    // но лучше разрешить GET /api/hotels/ для всех авторизованных (или вообще публично)
    error.value = "Не удалось загрузить отели";
  }
});

async function onSubmit() {
  error.value = "";
  ok.value = "";
  try {
    await registerStaff({
      username: username.value,
      password: password.value,
      role: role.value,
      hotel_id: Number(hotel_id.value),
      code: code.value,
    });

    // сразу логиним
    await login({ username: username.value, password: password.value });
    const u = await me();
    router.replace(redirectPathByRole(u.role));
  } catch (e) {
    error.value = e?.response?.data ? JSON.stringify(e.response.data) : "Ошибка регистрации персонала";
  }
}
</script>

<template>
  <div style="max-width: 520px; margin: 40px auto;">
    <h2>Регистрация персонала</h2>

    <form @submit.prevent="onSubmit" style="display: grid; gap: 10px; margin-top: 16px;">
      <input v-model="username" placeholder="username" />
      <input v-model="password" type="password" placeholder="password" />

      <label>
        Роль:
        <select v-model="role">
          <option value="cleaner">Уборщик</option>
          <option value="admin">Администратор</option>
        </select>
      </label>

      <label>
        Отель:
        <select v-model="hotel_id">
          <option value="" disabled>Выбери отель</option>
          <option v-for="h in hotels" :key="h.id_hotel" :value="h.id_hotel">
            {{ h.name }} — {{ h.city }}
          </option>
        </select>
      </label>

      <input v-model="code" placeholder="Код персонала" />

      <button type="submit" :disabled="!hotel_id">Зарегистрироваться</button>
    </form>

    <p v-if="ok" style="color: green;">{{ ok }}</p>
    <p v-if="error" style="color: red;">{{ error }}</p>

    <div style="margin-top: 14px;">
      <RouterLink to="/register">← Назад</RouterLink>
    </div>
  </div>
</template>