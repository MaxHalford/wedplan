<script setup lang="ts">
const emit = defineEmits<{
  'add:table': []
}>()

function handleAddTable() {
  emit('add:table')
}
</script>

<template>
  <div class="planner-toolbar">
    <h1 class="toolbar-title">Wedding Seating Planner</h1>
    <div class="toolbar-actions">
      <button @click="handleAddTable" class="add-table-button">
        <span class="button-icon">+</span>
        Add Table
      </button>
    </div>
  </div>
</template>

<style scoped>
.planner-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg) var(--spacing-xl);
  background: linear-gradient(to bottom, var(--parchment-light), var(--parchment-medium));
  border-bottom: 3px solid var(--ornate-border);
  box-shadow:
    inset 0 1px 0 rgba(255, 255, 255, 0.5),
    0 4px 8px var(--shadow-brown);
}

.toolbar-title {
  margin: 0;
  font-size: 2rem;
  color: var(--burgundy);
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
  letter-spacing: 0.05em;
}

.toolbar-actions {
  display: flex;
  gap: var(--spacing-md);
}

.add-table-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 1.1rem;
  padding: var(--spacing-md) var(--spacing-lg);
}

.button-icon {
  font-size: 1.5rem;
  line-height: 1;
  font-weight: bold;
}
</style>
