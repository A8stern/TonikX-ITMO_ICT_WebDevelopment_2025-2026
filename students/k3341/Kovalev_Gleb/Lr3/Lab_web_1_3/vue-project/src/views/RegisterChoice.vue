<template>
  <div style="max-width: 420px; margin: 40px auto;">
    <h2>Регистрация</h2>

    <div style="display: grid; gap: 12px; margin-top: 20px;">
      <RouterLink to="/register/client">
        <button style="width: 100%;">Я клиент</button>
      </RouterLink>

      <RouterLink to="/register/staff">
        <button style="width: 100%;">Я персонал</button>
      </RouterLink>

      <RouterLink to="/login">Уже есть аккаунт → Войти</RouterLink>
    </div>
  </div>
</template>