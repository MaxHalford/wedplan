<script setup lang="ts">
import { ref, computed } from 'vue'
import { useOnboarding } from '../composables/useOnboarding'
import { useTablePlannerStore } from '../stores/tablePlanner'

const emit = defineEmits<{
  'add:table': []
  'import:csv': [file: File]
  'start:matching': []
  'download:pdf': []
}>()

const store = useTablePlannerStore()
const { isActive, currentStep, showCSVHelper, restart, OnboardingStep } = useOnboarding()
const showRestartConfirm = ref(false)

const fileInput = ref<HTMLInputElement>()

// Compute button classes based on onboarding state
const importButtonClasses = computed(() => ({
  'onboarding-spotlight': isActive.value && !showCSVHelper.value && currentStep.value === OnboardingStep.IMPORT_GUESTS,
  'onboarding-dimmed': isActive.value && !showCSVHelper.value && currentStep.value !== OnboardingStep.IMPORT_GUESTS,
}))

const addTableButtonClasses = computed(() => ({
  'onboarding-spotlight': isActive.value && !showCSVHelper.value && currentStep.value === OnboardingStep.ADD_TABLES,
  'onboarding-dimmed': isActive.value && !showCSVHelper.value && currentStep.value !== OnboardingStep.ADD_TABLES,
}))

const matchButtonClasses = computed(() => ({
  'onboarding-spotlight': isActive.value && !showCSVHelper.value && currentStep.value === OnboardingStep.SET_PREFERENCES,
  'onboarding-dimmed': isActive.value && !showCSVHelper.value && currentStep.value !== OnboardingStep.SET_PREFERENCES,
}))

const downloadButtonClasses = computed(() => ({
  'onboarding-dimmed': isActive.value && !showCSVHelper.value && currentStep.value !== OnboardingStep.COMPLETE,
}))

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

function handleRestartClick() {
  showRestartConfirm.value = true
}

function handleRestartConfirm() {
  store.clearAll()
  restart()
  showRestartConfirm.value = false
}

function handleRestartCancel() {
  showRestartConfirm.value = false
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
      <button
        @click="triggerFileInput"
        class="toolbar-button import-button"
        :class="importButtonClasses"
      >
        <span class="button-icon">📜</span>
        Import CSV
      </button>
      <button
        @click="handleStartMatching"
        class="toolbar-button match-button"
        :class="matchButtonClasses"
      >
        <span class="button-icon">💕</span>
        Match Groups
      </button>
      <button
        @click="handleAddTable"
        class="toolbar-button add-table-button"
        :class="addTableButtonClasses"
      >
        <span class="button-icon">+</span>
        Add Table
      </button>
      <button
        @click="handleDownloadPDF"
        class="toolbar-button download-button"
        :class="downloadButtonClasses"
      >
        <span class="button-icon">📄</span>
        Download PDF
      </button>
      <button
        @click="handleRestartClick"
        class="toolbar-button reset-button"
      >
        <span class="button-icon">↺</span>
        Reset Session
      </button>
      <input
        ref="fileInput"
        type="file"
        accept=".csv"
        @change="handleFileSelect"
        style="display: none"
      />
    </div>

    <!-- Reset Confirmation Dialog -->
    <Teleport to="body">
      <div v-if="showRestartConfirm" class="confirm-overlay" @click.self="handleRestartCancel">
        <div class="confirm-dialog">
          <h3>Reset Session?</h3>
          <p>This will clear all guests, tables, and preferences. This action cannot be undone.</p>
          <div class="confirm-actions">
            <button @click="handleRestartCancel" class="confirm-btn confirm-btn-cancel">
              Cancel
            </button>
            <button @click="handleRestartConfirm" class="confirm-btn confirm-btn-confirm">
              Reset Everything
            </button>
          </div>
        </div>
      </div>
    </Teleport>
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

/* Reset button styling */
.reset-button {
  border-color: var(--faded-text);
  color: var(--faded-text);
}

.reset-button:hover {
  border-color: var(--deep-red);
  color: var(--deep-red);
}

/* Confirmation dialog */
.confirm-overlay {
  position: fixed;
  inset: 0;
  background: rgba(44, 24, 16, 0.6);
  z-index: 2000;
  display: flex;
  align-items: center;
  justify-content: center;
  animation: fadeIn var(--transition-medium) ease;
}

@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.confirm-dialog {
  background: var(--parchment-light);
  border: 3px solid var(--ornate-border);
  border-radius: 8px;
  padding: var(--spacing-xl);
  max-width: 400px;
  width: 90%;
  box-shadow: 0 8px 32px var(--shadow-brown);
  animation: slideUp var(--transition-medium) ease;
}

@keyframes slideUp {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.confirm-dialog h3 {
  margin: 0 0 var(--spacing-md) 0;
  font-family: var(--font-elegant);
  font-size: 1.25rem;
  color: var(--burgundy);
}

.confirm-dialog p {
  margin: 0 0 var(--spacing-lg) 0;
  font-family: var(--font-body);
  color: var(--brown-text);
  line-height: 1.5;
}

.confirm-actions {
  display: flex;
  gap: var(--spacing-md);
  justify-content: flex-end;
}

.confirm-btn {
  padding: var(--spacing-sm) var(--spacing-lg);
  font-size: 0.95rem;
}

.confirm-btn-cancel {
  background: transparent;
  border-color: var(--ornate-border);
  color: var(--brown-text);
}

.confirm-btn-cancel:hover {
  background: var(--parchment-medium);
}

.confirm-btn-confirm {
  background: linear-gradient(to bottom, var(--deep-red), var(--burgundy));
  border-color: var(--deep-red);
  color: var(--parchment-light);
}

.confirm-btn-confirm:hover {
  background: linear-gradient(to bottom, var(--burgundy), var(--deep-red));
  box-shadow: 0 4px 12px rgba(139, 26, 26, 0.4);
}
</style>
