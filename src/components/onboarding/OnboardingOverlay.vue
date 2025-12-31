<script setup lang="ts">
import { computed, watch, onMounted } from 'vue'
import { useOnboarding } from '../../composables/useOnboarding'
import { useTablePlannerStore } from '../../stores/tablePlanner'
import { TABLE_DEFAULTS, CANVAS_DEFAULTS } from '../../types'
import CSVHelperModal from './CSVHelperModal.vue'
import OnboardingTooltip from './OnboardingTooltip.vue'

const store = useTablePlannerStore()

const {
  isActive,
  currentStep,
  stepInfo,
  shouldShowCSVHelper,
  showCSVHelper,
  closeCSVHelper,
  skipStep,
  continueToNextStep,
  dismissOnboarding,
  completeOnboarding,
  OnboardingStep,
} = useOnboarding()

// Show CSV helper modal automatically on first visit to step 1
onMounted(() => {
  if (shouldShowCSVHelper.value) {
    // Small delay to let the page render first
    setTimeout(() => {
      showCSVHelper.value = true
    }, 500)
  }
})

// Watch for step changes to potentially show CSV helper
watch(shouldShowCSVHelper, (shouldShow) => {
  if (shouldShow) {
    showCSVHelper.value = true
  }
})

function handleCSVHelperClose() {
  closeCSVHelper()
}

function handleSkipAll() {
  completeOnboarding()
}

function handleTooltipSkip() {
  skipStep()
}

function handleTooltipContinue() {
  continueToNextStep()
}

function handleTooltipDismiss() {
  dismissOnboarding()
}

function handleCreateTables(count: number, seats: number) {
  const canvasWidth = store.canvasSettings.width
  const canvasHeight = store.canvasSettings.height
  const tableWidth = TABLE_DEFAULTS.WIDTH
  const tableHeight = TABLE_DEFAULTS.HEIGHT
  const padding = 40

  // Calculate grid layout
  const cols = Math.ceil(Math.sqrt(count))
  const rows = Math.ceil(count / cols)

  const spacingX = (canvasWidth - padding * 2) / cols
  const spacingY = (canvasHeight - padding * 2) / rows

  for (let i = 0; i < count; i++) {
    const col = i % cols
    const row = Math.floor(i / cols)

    const x = padding + col * spacingX + (spacingX - tableWidth) / 2
    const y = padding + row * spacingY + (spacingY - tableHeight) / 2

    store.addTable(x, y)

    // Update seat count for the newly added table
    const newTable = store.tables[store.tables.length - 1]
    if (newTable && seats !== TABLE_DEFAULTS.DEFAULT_SEAT_COUNT) {
      store.updateTableSeatCount(newTable.id, seats)
    }
  }
}

// Progress dots
const progressSteps = computed(() => {
  const steps = [
    { step: OnboardingStep.IMPORT_GUESTS, label: 'Import' },
    { step: OnboardingStep.ADD_TABLES, label: 'Tables' },
    { step: OnboardingStep.SET_PREFERENCES, label: 'Preferences' },
  ]

  const currentIndex = steps.findIndex(s => s.step === currentStep.value)

  return steps.map((s, index) => ({
    ...s,
    isActive: s.step === currentStep.value,
    isCompleted: index < currentIndex,
  }))
})

// Don't show backdrop when CSV modal is visible (modal has its own styling)
const showBackdrop = computed(() => {
  return isActive.value && !showCSVHelper.value
})

// Allow canvas interaction during ADD_TABLES step
const allowCanvasInteraction = computed(() => {
  return currentStep.value === OnboardingStep.ADD_TABLES
})

// Don't show tooltip when CSV modal is visible
const showTooltip = computed(() => {
  return isActive.value && !showCSVHelper.value && currentStep.value !== OnboardingStep.COMPLETE
})
</script>

<template>
  <Teleport to="body">
    <!-- CSV Helper Modal -->
    <Transition name="fade">
      <div v-if="showCSVHelper" class="onboarding-backdrop">
        <CSVHelperModal
          @close="handleCSVHelperClose"
          @skip-all="handleSkipAll"
        />
      </div>
    </Transition>

    <!-- Backdrop for tooltip steps -->
    <Transition name="fade">
      <div
        v-if="showBackdrop"
        class="onboarding-backdrop"
        :class="{ 'allow-interaction': allowCanvasInteraction }"
        @click.self="handleTooltipDismiss"
      />
    </Transition>

    <!-- Tooltip -->
    <Transition name="tooltip">
      <OnboardingTooltip
        v-if="showTooltip"
        :step-info="stepInfo"
        @skip="handleTooltipSkip"
        @continue="handleTooltipContinue"
        @dismiss="handleTooltipDismiss"
        @create-tables="handleCreateTables"
      />
    </Transition>

    <!-- Progress indicator -->
    <Transition name="fade">
      <div v-if="showBackdrop" class="onboarding-progress">
        <div
          v-for="step in progressSteps"
          :key="step.step"
          class="progress-dot"
          :class="{
            active: step.isActive,
            completed: step.isCompleted,
          }"
          :title="step.label"
        />
      </div>
    </Transition>
  </Teleport>
</template>

<style scoped>
.fade-enter-active,
.fade-leave-active {
  transition: opacity var(--transition-medium) ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

.tooltip-enter-active {
  animation: tooltip-in var(--transition-medium) ease;
}

.tooltip-leave-active {
  animation: tooltip-out var(--transition-fast) ease;
}

@keyframes tooltip-in {
  from {
    opacity: 0;
    transform: translateY(10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes tooltip-out {
  from {
    opacity: 1;
    transform: translateY(0);
  }
  to {
    opacity: 0;
    transform: translateY(-10px);
  }
}
</style>
