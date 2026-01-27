<script setup>
import { ref } from "vue";
import { registerClient, login } from "../api/auth";
import { useRouter } from "vue-router";
import { me } from "../api/auth";
import { redirectPathByRole } from "../utils/redirectByRole";

const router = useRouter();

const username = ref("");
const email = ref("");
const password = ref("");

const error = ref("");
const ok = ref("");

function niceError(e) {
  const status = e?.response?.status;
  const data = e?.response?.data;

  if (status === 400 && data) {
    return JSON.stringify(data);
  }
  if (data?.detail) return data.detail;
  if (typeof data === "string") return data;
  if (data) return JSON.stringify(data);
  return "Ошибка регистрации";
}

async function onSubmit() {
  error.value = "";
  ok.value = "";

  if (!username.value || !email.value || !password.value) {
    error.value = "Заполните username, email и пароль.";
    return;
  }

  try {
    await registerClient({
      username: username.value.trim(),
      email: email.value.trim(),
      password: password.value,
    });

    await login({ username: username.value, password: password.value });
    const u = await me();
    router.replace(redirectPathByRole(u.role));
  } catch (e) {
    error.value = niceError(e);
  }
}
</script>

<template>
  <div style="max-width: 420px; margin: 40px auto;">
    <h2>Регистрация клиента</h2>

    <form @submit.prevent="onSubmit" style="display: grid; gap: 10px; margin-top: 16px;">
      <input v-model="username" placeholder="username" />
      <input v-model="email" type="email" placeholder="email" />
      <input v-model="password" type="password" placeholder="password" />
      <button type="submit">Создать аккаунт</button>
    </form>

    <p v-if="ok" style="color: green; margin-top: 10px;">{{ ok }}</p>
    <p v-if="error" style="color: #b00020; margin-top: 10px;">{{ error }}</p>

    <div style="margin-top: 14px;">
      <RouterLink to="/register">← Назад</RouterLink>
    </div>
  </div>
</template>