<script setup>
import { ref } from "vue";
import { useRouter } from "vue-router";
import { login, me } from "../api/auth";

const router = useRouter();

const username = ref("");
const password = ref("");

const loading = ref(false);
const message = ref(""); // success info (optional)
const errorText = ref(""); // pretty error text

function prettyAuthError(e) {
  const status = e?.response?.status;
  const data = e?.response?.data;

  // Network / server down
  if (!e?.response) {
    return "Не удалось подключиться к серверу. Проверь, что Django запущен на :8000 и CORS настроен.";
  }

  // Djoser token login errors often: 400 {non_field_errors: ["Unable to log in with provided credentials."]}
  if (status === 400) {
    const nfe = data?.non_field_errors?.[0];
    if (nfe) {
      if (String(nfe).toLowerCase().includes("unable to log in")) {
        return "Неверный логин или пароль.";
      }
      return String(nfe);
    }
    const u = data?.username?.[0];
    const p = data?.password?.[0];
    if (u || p) return `${u ? "Логин: " + u : ""}${u && p ? " · " : ""}${p ? "Пароль: " + p : ""}`;
    return "Проверь введённые данные.";
  }

  if (status === 401) {
    return "Неверный логин или пароль.";
  }

  // Deactivated user / forbidden
  if (status === 403) {
    return "Доступ запрещён. Возможно, аккаунт был деактивирован администратором.";
  }

  // Fallback
  if (data?.detail) return String(data.detail);
  if (typeof data === "string") return data;
  return "Произошла ошибка при входе.";
}

async function onSubmit() {
  message.value = "";
  errorText.value = "";
  loading.value = true;

  try {
    await login({ username: username.value, password: password.value });

    // подтягиваем профиль и кидаем по роли
    const profile = await me(); // { role, hotel, client, staff? }
    message.value = "Вход выполнен.";

    if (profile?.role === "admin") {
      router.push("/admin/rooms");
    } else if (profile?.role === "cleaner") {
      router.push("/cleaner");
    } else {
      router.push("/");
    }
  } catch (e) {
    errorText.value = prettyAuthError(e);
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div style="max-width: 420px; margin: 40px auto; padding: 0 16px;">
    <h2 style="margin: 0 0 14px;">Вход</h2>

    <!-- nice error -->
    <div
      v-if="errorText"
      style="
        border: 1px solid #f2b8c0;
        background: #fff5f7;
        color: #8b0a1a;
        border-radius: 12px;
        padding: 12px;
        margin-bottom: 12px;
      "
    >
      <div style="font-weight: 700; margin-bottom: 6px;">Не получилось войти</div>
      <div style="line-height: 1.35;">{{ errorText }}</div>
      <div style="margin-top: 8px; font-size: 13px; color: #7a4b52;">
        Подсказка: проверь логин/пароль или попроси администратора проверить активность аккаунта.
      </div>
    </div>

    <!-- optional success -->
    <div
      v-if="message && !errorText"
      style="
        border: 1px solid #bde5c8;
        background: #f4fff7;
        color: #0a7a0a;
        border-radius: 12px;
        padding: 10px 12px;
        margin-bottom: 12px;
      "
    >
      {{ message }}
    </div>

    <form @submit.prevent="onSubmit" style="display: grid; gap: 10px;">
      <label style="display: grid; gap: 6px;">
        <span style="font-size: 13px; color: #666;">Логин</span>
        <input
          v-model="username"
          placeholder="например: cleaner_2"
          autocomplete="username"
          style="padding: 8px 10px; border: 1px solid #ddd; border-radius: 10px;"
        />
      </label>

      <label style="display: grid; gap: 6px;">
        <span style="font-size: 13px; color: #666;">Пароль</span>
        <input
          v-model="password"
          type="password"
          placeholder="••••••••"
          autocomplete="current-password"
          style="padding: 8px 10px; border: 1px solid #ddd; border-radius: 10px;"
        />
      </label>

      <button
        type="submit"
        :disabled="loading"
        style="
          margin-top: 6px;
          border: 1px solid #ddd;
          background: white;
          padding: 8px 10px;
          border-radius: 10px;
          cursor: pointer;
        "
      >
        {{ loading ? "Входим..." : "Войти" }}
      </button>
    </form>

    <div style="margin-top: 12px; font-size: 14px;">
      Нет аккаунта —
      <RouterLink to="/register" style="text-decoration: underline;">Регистрация</RouterLink>
    </div>
  </div>
</template>