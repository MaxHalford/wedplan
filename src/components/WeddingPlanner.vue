<script setup lang="ts">
import { useTablePlannerStore } from '../stores/tablePlanner'
import { TABLE_DEFAULTS } from '../types'
import PlannerToolbar from './PlannerToolbar.vue'
import PlannerCanvas from './PlannerCanvas.vue'

const store = useTablePlannerStore()

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
</script>

<template>
  <div class="wedding-planner">
    <PlannerToolbar @add:table="handleAddTable" />
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
</template>

<style scoped>
.wedding-planner {
  width: 100%;
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
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
