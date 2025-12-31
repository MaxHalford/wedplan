<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'

interface StepInfo {
  number: number
  total: number
  title: string
  description: string
  hint?: string
  targetSelector: string
  isOptional?: boolean
  // Progress tracking fields
  showProgress?: boolean
  currentSeats?: number
  requiredSeats?: number
  canContinue?: boolean
  continueLabel?: string
  skipLabel?: string
}

const props = defineProps<{
  stepInfo: StepInfo
}>()

const emit = defineEmits<{
  skip: []
  continue: []
  dismiss: []
  createTables: [count: number, seats: number]
}>()

// Bulk table creation form
const tableCount = ref(4)
const seatsPerTable = ref(8)

function handleCreateTables() {
  emit('createTables', tableCount.value, seatsPerTable.value)
}

// Progress percentage (capped at 100%)
const progressPercent = computed(() => {
  if (!props.stepInfo.showProgress || !props.stepInfo.requiredSeats) return 0
  return Math.min(100, Math.round((props.stepInfo.currentSeats || 0) / props.stepInfo.requiredSeats * 100))
})

const isClosing = ref(false)
const tooltipPosition = ref({ top: '0px', left: '0px' })
const arrowPosition = ref<'top' | 'bottom'>('top')

function calculatePosition() {
  const target = document.querySelector(props.stepInfo.targetSelector)
  if (!target) return

  const rect = target.getBoundingClientRect()
  const tooltipWidth = 320
  const tooltipHeight = 200 // approximate
  const padding = 16

  // Position below the target by default
  let top = rect.bottom + padding
  let left = rect.left + rect.width / 2 - tooltipWidth / 2

  // Check if tooltip would go off bottom of screen
  if (top + tooltipHeight > window.innerHeight) {
    // Position above the target instead
    top = rect.top - tooltipHeight - padding
    arrowPosition.value = 'bottom'
  } else {
    arrowPosition.value = 'top'
  }

  // Keep within horizontal bounds
  if (left < padding) {
    left = padding
  } else if (left + tooltipWidth > window.innerWidth - padding) {
    left = window.innerWidth - tooltipWidth - padding
  }

  tooltipPosition.value = {
    top: `${top}px`,
    left: `${left}px`,
  }
}

function handleSkip() {
  isClosing.value = true
  setTimeout(() => {
    emit('skip')
  }, 150)
}

function handleContinue() {
  isClosing.value = true
  setTimeout(() => {
    emit('continue')
  }, 150)
}

function handleDismiss() {
  isClosing.value = true
  setTimeout(() => {
    emit('dismiss')
  }, 150)
}

// Recalculate on resize
onMounted(() => {
  calculatePosition()
  window.addEventListener('resize', calculatePosition)
})

onUnmounted(() => {
  window.removeEventListener('resize', calculatePosition)
})

// Recalculate when step changes
watch(() => props.stepInfo.targetSelector, () => {
  isClosing.value = false
  calculatePosition()
})
</script>

<template>
  <div
    class="onboarding-tooltip"
    :class="[
      { closing: isClosing },
      arrowPosition === 'bottom' ? 'arrow-bottom' : ''
    ]"
    :style="tooltipPosition"
  >
    <div class="tooltip-header">
      <span class="tooltip-step-badge">
        Step {{ stepInfo.number }}/{{ stepInfo.total }}
      </span>
      <button @click="handleDismiss" class="tooltip-dismiss" aria-label="Dismiss">
        &times;
      </button>
    </div>

    <div class="tooltip-body">
      <h3 class="tooltip-title">{{ stepInfo.title }}</h3>
      <p class="tooltip-description">{{ stepInfo.description }}</p>

      <!-- Progress bar for steps with progress tracking -->
      <div v-if="stepInfo.showProgress" class="tooltip-progress">
        <div class="progress-bar">
          <div
            class="progress-fill"
            :class="{ complete: stepInfo.canContinue }"
            :style="{ width: `${progressPercent}%` }"
          />
        </div>
        <div class="progress-label">
          <span>{{ stepInfo.currentSeats }} / {{ stepInfo.requiredSeats }} seats</span>
          <span v-if="stepInfo.canContinue" class="progress-complete">Ready!</span>
        </div>
      </div>

      <!-- Bulk table creation form -->
      <div v-if="stepInfo.showProgress" class="tooltip-bulk-create">
        <div class="bulk-create-row">
          <label>
            <span>Tables</span>
            <input
              type="number"
              v-model.number="tableCount"
              min="1"
              max="20"
              class="bulk-input"
            />
          </label>
          <span class="bulk-separator">x</span>
          <label>
            <span>Seats</span>
            <input
              type="number"
              v-model.number="seatsPerTable"
              min="2"
              max="16"
              class="bulk-input"
            />
          </label>
          <button @click="handleCreateTables" class="bulk-create-btn">
            Create
          </button>
        </div>
        <p class="bulk-hint">Or click "Add Table" / drag tables on the canvas</p>
      </div>

      <p v-if="stepInfo.hint && !stepInfo.showProgress" class="tooltip-hint">{{ stepInfo.hint }}</p>
    </div>

    <!-- Actions for steps with progress (Continue + Skip) -->
    <div v-if="stepInfo.showProgress" class="tooltip-actions tooltip-actions-progress">
      <button
        @click="handleContinue"
        class="tooltip-continue-btn"
        :class="{ enabled: stepInfo.canContinue }"
        :disabled="!stepInfo.canContinue"
      >
        {{ stepInfo.continueLabel || 'Continue' }}
      </button>
      <button @click="handleSkip" class="tooltip-skip-btn">
        {{ stepInfo.skipLabel || 'Skip' }}
      </button>
    </div>

    <!-- Actions for optional steps (just Skip) -->
    <div v-else-if="stepInfo.isOptional" class="tooltip-actions">
      <button @click="handleSkip" class="tooltip-skip-btn">
        Skip this step
      </button>
    </div>
  </div>
</template>

<style scoped>
/* Styles are in onboarding.css */
</style>
