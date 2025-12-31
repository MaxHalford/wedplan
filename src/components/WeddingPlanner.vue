<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useTablePlannerStore } from '../stores/tablePlanner'
import { TABLE_DEFAULTS } from '../types'
import PlannerToolbar from './PlannerToolbar.vue'
import PlannerCanvas from './PlannerCanvas.vue'
import GuestList from './GuestList.vue'
import GroupMatcher from './GroupMatcher.vue'

const store = useTablePlannerStore()
const showMatcher = ref(false)

// Handle keyboard events
function handleKeyDown(event: KeyboardEvent) {
  // Delete or Backspace key
  if (event.key === 'Delete' || event.key === 'Backspace') {
    if (store.selectedTableId) {
      // Prevent default backspace navigation
      event.preventDefault()
      store.removeTable(store.selectedTableId)
    }
  }

  // Escape key to deselect
  if (event.key === 'Escape') {
    store.selectTable(null)
    store.highlightGroup(null)
  }
}

// Add keyboard listener on mount
onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

// Remove keyboard listener on unmount
onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

function handleAddTable() {
  // Add new table at the center of the canvas
  const centerX = store.canvasSettings.width / 2 - TABLE_DEFAULTS.WIDTH / 2
  const centerY = store.canvasSettings.height / 2 - TABLE_DEFAULTS.HEIGHT / 2

  // Add a small random offset so multiple tables don't stack exactly on top of each other
  const offsetX = (Math.random() - 0.5) * 100
  const offsetY = (Math.random() - 0.5) * 100

  store.addTable(centerX + offsetX, centerY + offsetY)
}

function handlePositionUpdate(id: string, x: number, y: number) {
  // Clamp position to keep table within canvas bounds
  const maxX = store.canvasSettings.width - TABLE_DEFAULTS.WIDTH
  const maxY = store.canvasSettings.height - TABLE_DEFAULTS.HEIGHT

  const clampedX = Math.max(0, Math.min(maxX, x))
  const clampedY = Math.max(0, Math.min(maxY, y))

  store.updateTablePosition(id, clampedX, clampedY)
}

function handleTableSelect(id: string | null) {
  store.selectTable(id)
}

function handleSeatCountUpdate(id: string, seatCount: number) {
  store.updateTableSeatCount(id, seatCount)
}

function handleImportCSV(file: File) {
  store.importGuestsFromCSV(file).catch(error => {
    console.error('Failed to import CSV:', error)
    alert('Failed to import CSV file. Please check the format.')
  })
}

function handleStartMatching() {
  showMatcher.value = true
}

function handleCloseMatcher() {
  showMatcher.value = false
}
</script>

<template>
  <div class="wedding-planner">
    <PlannerToolbar
      @add:table="handleAddTable"
      @import:csv="handleImportCSV"
      @start:matching="handleStartMatching"
    />
    <div class="main-content">
      <GuestList class="guest-pane" />
      <div class="canvas-container">
        <PlannerCanvas
          :tables="store.tables"
          :selected-table-id="store.selectedTableId"
          :canvas-settings="store.canvasSettings"
          @update:position="handlePositionUpdate"
          @select:table="handleTableSelect"
          @update:seat-count="handleSeatCountUpdate"
        />
      </div>
    </div>
    <GroupMatcher v-if="showMatcher" @close="handleCloseMatcher" />
  </div>
</template>

<style scoped>
.wedding-planner {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.main-content {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.guest-pane {
  width: 320px;
  flex-shrink: 0;
}

.canvas-container {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  overflow: auto;
  background: radial-gradient(
    circle at center,
    var(--parchment-light) 0%,
    var(--parchment-dark) 100%
  );
}
</style>
