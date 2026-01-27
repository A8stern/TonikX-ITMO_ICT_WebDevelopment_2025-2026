<script setup>
defineProps({
  items: { type: Array, default: () => [] },
  onDelete: { type: Function, default: null },
});
</script>

<template>
  <div style="display:grid; gap:12px;">
    <div
      v-for="c in items"
      :key="c.id_cleaning"
      class="card card-pad"
      style="display:flex; justify-content:space-between; gap:14px; flex-wrap:wrap; align-items:flex-start;"
    >
      <div style="display:grid; gap:8px;">
        <div style="display:flex; gap:10px; flex-wrap:wrap; align-items:center;">
          <span class="tag">
            Номер <b>№{{ c.room?.room_number }}</b>
          </span>

          <span class="tag tag-muted">
            Дата <b>{{ c.date }}</b>
          </span>

          <span class="tag tag-muted">
            Время <b>{{ c.cleaning_time }}</b>
          </span>

          <span
            class="tag"
            :class="c.cleaning_status === 'Убран' ? 'tag-ok' : 'tag-bad'"
          >
            Статус: <b>{{ c.cleaning_status }}</b>
          </span>
        </div>

        <div class="muted" style="font-size:13px;">
          Тип: <b style="color: var(--text);">{{ c.room?.room_type?.name || "—" }}</b>
        </div>
      </div>

      <button
        v-if="onDelete"
        class="btn btn-danger"
        @click="onDelete(c)"
        style="height: fit-content;"
      >
        Удалить
      </button>
    </div>

    <div v-if="!items.length" class="card card-pad muted">
      Нет записей.
    </div>
  </div>
</template>

<style scoped>
.tag{
  display:inline-flex;
  align-items:center;
  gap:8px;
  padding: 6px 10px;
  border-radius: 999px;
  background: rgba(110,168,254,.14);
  border: 1px solid rgba(110,168,254,.22);
  color: #2457b7;
  font-size: 13px;
  font-weight: 600;
}

.tag b{
  color: var(--text);
  font-weight: 900;
}

.tag-muted{
  background: rgba(107,114,128,.10);
  border-color: rgba(107,114,128,.18);
  color: var(--muted);
}

.tag-ok{
  background: rgba(110,231,183,.22);
  border-color: rgba(110,231,183,.35);
  color: #0f6a44;
}

.tag-bad{
  background: rgba(239,68,68,.12);
  border-color: rgba(239,68,68,.25);
  color: #a01414;
}
</style>