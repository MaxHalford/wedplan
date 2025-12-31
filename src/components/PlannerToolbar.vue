<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  'add:table': []
  'import:csv': [file: File]
  'start:matching': []
}>()

const fileInput = ref<HTMLInputElement>()

function handleAddTable() {
  emit('add:table')
}

function triggerFileInput() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    emit('import:csv', file)
  }
}

function handleStartMatching() {
  emit('start:matching')
}
</script>

<template>
  <div class="planner-toolbar">
    <h1 class="toolbar-title">
      <span class="drop-cap">W</span>edding
      <span class="drop-cap">S</span>eating
      <span class="drop-cap">P</span>lanner
    </h1>
    <div class="toolbar-actions">
      <button @click="triggerFileInput" class="toolbar-button import-button">
        <span class="button-icon">📜</span>
        Import CSV
      </button>
      <button @click="handleStartMatching" class="toolbar-button match-button">
        <span class="button-icon">💕</span>
        Match Groups
      </button>
      <button @click="handleAddTable" class="toolbar-button add-table-button">
        <span class="button-icon">+</span>
        Add Table
      </button>
      <input
        ref="fileInput"
        type="file"
        accept=".csv"
        @change="handleFileSelect"
        style="display: none"
      />
    </div>
  </div>
</template>

<style scoped>
.planner-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg) var(--spacing-xl);
  background:
    linear-gradient(to bottom, var(--parchment-light), var(--parchment-medium)),
    repeating-linear-gradient(
      90deg,
      transparent,
      transparent 2px,
      rgba(139, 105, 20, 0.03) 2px,
      rgba(139, 105, 20, 0.03) 4px
    );
  border-bottom: 4px double var(--ornate-border);
  box-shadow:
    inset 0 2px 0 rgba(255, 255, 255, 0.6),
    inset 0 -2px 4px rgba(139, 105, 20, 0.1),
    0 4px 12px var(--shadow-brown);
  position: relative;
}

.planner-toolbar::before {
  content: '';
  position: absolute;
  left: 0;
  right: 0;
  bottom: -4px;
  height: 2px;
  background: linear-gradient(
    90deg,
    transparent,
    var(--gold) 20%,
    var(--gold) 80%,
    transparent
  );
}

.toolbar-title {
  margin: 0;
  font-size: 2.25rem;
  color: var(--burgundy);
  text-shadow:
    0 2px 3px rgba(255, 255, 255, 0.9),
    0 1px 0 rgba(255, 255, 255, 0.5);
  letter-spacing: 0.08em;
  display: flex;
  align-items: center;
  gap: 0.15em;
}

.drop-cap {
  font-family: var(--font-decorative);
  font-size: 3rem;
  color: var(--deep-red);
  text-shadow:
    2px 2px 0 var(--gold),
    0 0 8px rgba(212, 175, 55, 0.4);
  line-height: 1;
  font-weight: 700;
  display: inline-block;
  margin-right: -0.1em;
}

.toolbar-actions {
  display: flex;
  gap: var(--spacing-md);
}

.toolbar-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 1rem;
  padding: var(--spacing-md) var(--spacing-lg);
  background: linear-gradient(to bottom, var(--parchment-light), var(--parchment-medium));
  border: 2px solid var(--ornate-border);
  position: relative;
}

.toolbar-button::before {
  content: '';
  position: absolute;
  inset: -1px;
  border: 1px solid rgba(255, 255, 255, 0.3);
  border-radius: 4px;
  pointer-events: none;
}

.toolbar-button:hover {
  background: linear-gradient(to bottom, var(--parchment-medium), var(--parchment-light));
  border-color: var(--gold);
}

.button-icon {
  font-size: 1.3rem;
  line-height: 1;
}

.import-button .button-icon {
  font-size: 1.2rem;
}
</style>
