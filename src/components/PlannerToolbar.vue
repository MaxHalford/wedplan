<script setup lang="ts">
import { ref } from 'vue'

const emit = defineEmits<{
  'add:table': []
  'import:csv': [file: File]
  'start:matching': []
  'download:pdf': []
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

function handleDownloadPDF() {
  emit('download:pdf')
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
      <button @click="handleDownloadPDF" class="toolbar-button download-button">
        <span class="button-icon">📄</span>
        Download PDF
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
  font-size: 1.5rem;
  color: var(--burgundy);
  text-shadow:
    0 2px 3px rgba(255, 255, 255, 0.9),
    0 1px 0 rgba(255, 255, 255, 0.5);
  letter-spacing: 0.05em;
  display: flex;
  align-items: center;
  gap: 0.1em;
  flex-shrink: 0;
}

.drop-cap {
  font-family: var(--font-decorative);
  font-size: 2rem;
  color: var(--deep-red);
  text-shadow:
    2px 2px 0 var(--gold),
    0 0 8px rgba(212, 175, 55, 0.4);
  line-height: 1;
  font-weight: 700;
  display: inline-block;
  margin-right: -0.05em;
}

.toolbar-actions {
  display: flex;
  gap: var(--spacing-lg);
  flex-wrap: wrap;
  justify-content: flex-end;
  flex: 1;
}

.toolbar-button {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  font-size: 0.95rem;
  padding: var(--spacing-sm) var(--spacing-md);
  background: linear-gradient(to bottom, var(--parchment-light), var(--parchment-medium));
  border: 2px solid var(--ornate-border);
  position: relative;
  white-space: nowrap;
  min-height: 44px;
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

/* Mobile responsiveness */
@media (max-width: 768px) {
  .planner-toolbar {
    flex-direction: column;
    gap: var(--spacing-md);
    padding: var(--spacing-md);
  }

  .toolbar-title {
    font-size: 1.25rem;
    width: 100%;
    justify-content: center;
  }

  .drop-cap {
    font-size: 1.75rem;
  }

  .toolbar-actions {
    width: 100%;
    justify-content: center;
    gap: var(--spacing-sm);
  }

  .toolbar-button {
    font-size: 0.85rem;
    padding: var(--spacing-xs) var(--spacing-sm);
    flex: 1;
    min-width: 0;
    justify-content: center;
  }

  .button-icon {
    font-size: 1.1rem !important;
  }
}

@media (max-width: 480px) {
  .toolbar-actions {
    flex-direction: column;
    width: 100%;
  }

  .toolbar-button {
    width: 100%;
  }
}
</style>
