<script setup>
import { computed } from "vue";
import { useRouter } from "vue-router";
import { logout } from "../api/auth";
import { token, role } from "../stores/authStore";

const router = useRouter();

const isLoggedIn = computed(() => !!token.value);
const userRole = computed(() => role.value || "");

const links = computed(() => {
  if (!isLoggedIn.value) return [{ to: "/", label: "Отели" }];

  if (userRole.value === "admin") {
    return [
      { to: "/admin/rooms", label: "Номера" },
      { to: "/admin/checkins", label: "Заселения" },
      { to: "/admin/staff", label: "Персонал" },
    ];
  }

  if (userRole.value === "cleaner") {
    return [{ to: "/cleaner", label: "Уборки" }];
  }

  return [{ to: "/", label: "Отели" }];
});

const roleLabel = computed(() => {
  if (!isLoggedIn.value) return "";
  if (userRole.value === "admin") return "Админ";
  if (userRole.value === "cleaner") return "Уборщик";
  return "Клиент";
});

async function onLogout() {
  try {
    await logout();
  } catch (e) {
    localStorage.removeItem("token");
  }
  router.replace("/login");
}
</script>

<template>
  <header class="ph-header">
    <div class="container ph-row">
      <!-- Brand -->
      <div class="ph-brand" role="button" tabindex="0" @click="$router.push('/')">
        <div class="ph-logo">H</div>
        <div class="ph-brandText">
          <div class="ph-title">Hotels</div>
          <div class="ph-subtitle">Поиск и управление бронированиями</div>
        </div>
      </div>

      <!-- Nav -->
      <nav class="ph-nav">
        <RouterLink
          v-for="l in links"
          :key="l.to"
          :to="l.to"
          class="ph-link"
          active-class="ph-link--active"
        >
          {{ l.label }}
        </RouterLink>
      </nav>

      <!-- Actions -->
      <div class="ph-actions">
        <span v-if="isLoggedIn" class="ph-role">
          {{ roleLabel }}
        </span>

        <RouterLink v-if="!isLoggedIn" to="/login" class="btn btn-primary">
          Войти
        </RouterLink>

        <template v-else>
          <RouterLink to="/profile" class="btn">
            Профиль
          </RouterLink>

          <button class="btn btn-accent" @click="onLogout">
            Выйти
          </button>
        </template>
      </div>
    </div>
  </header>
</template>

<style scoped>
.ph-header{
  position: sticky;
  top: 0;
  z-index: 20;

  /* пастельное стекло */
  background: rgba(255,255,255,.75);
  backdrop-filter: blur(10px);

  border-bottom: 1px solid var(--border);
}

.ph-row{
  display:flex;
  align-items:center;
  justify-content:space-between;
  gap: 14px;
  padding: 10px 0;
}

.ph-brand{
  display:flex;
  align-items:center;
  gap: 10px;
  cursor:pointer;
  user-select:none;
  min-width: 190px;
}

.ph-logo{
  width: 36px;
  height: 36px;
  border-radius: 12px;
  display:flex;
  align-items:center;
  justify-content:center;
  font-weight: 900;
  color: #111;
  background: linear-gradient(180deg, var(--accent2), var(--accent));
  box-shadow: 0 10px 22px rgba(255,204,0,.18);
}

.ph-title{
  font-weight: 900;
  letter-spacing: .2px;
  line-height: 1.05;
}

.ph-subtitle{
  font-size: 12px;
  color: var(--muted);
  margin-top: 2px;
}

.ph-nav{
  display:flex;
  gap: 8px;
  align-items:center;
  flex-wrap: wrap;
}

.ph-link{
  color: var(--muted);
  padding: 10px 12px;
  border-radius: 12px;
  border: 1px solid transparent;
  transition: background .12s ease, border-color .12s ease, color .12s ease;
}

.ph-link:hover{
  color: var(--text);
  background: rgba(110,168,254,.12);
  border-color: rgba(110,168,254,.22);
}

.ph-link--active{
  color: #2457b7;
  background: rgba(110,168,254,.18);
  border-color: rgba(110,168,254,.32);
  font-weight: 800;
}

.ph-actions{
  display:flex;
  align-items:center;
  gap: 10px;
}

.ph-role{
  display:inline-flex;
  align-items:center;
  padding: 7px 10px;
  border-radius: 999px;
  background: rgba(107,114,128,.10);
  border: 1px solid rgba(107,114,128,.18);
  color: var(--muted);
  font-size: 13px;
  font-weight: 800;
}

@media (max-width: 820px){
  .ph-row{
    align-items: flex-start;
  }
  .ph-nav{
    display:none; /* чтобы не ломалось на мобиле */
  }
}
</style>