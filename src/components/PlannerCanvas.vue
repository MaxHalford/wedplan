<script setup lang="ts">
import { computed } from 'vue'
import type { Table, CanvasSettings } from '../types'
import DraggableTable from './DraggableTable.vue'

interface Props {
  tables: Table[]
  selectedTableId: string | null
  canvasSettings: CanvasSettings
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:position': [id: string, x: number, y: number]
  'select:table': [id: string | null]
  'update:seatCount': [id: string, seatCount: number]
}>()

const canvasStyle = computed(() => ({
  width: `${props.canvasSettings.width}px`,
  height: `${props.canvasSettings.height}px`,
}))

function handleBackgroundClick() {
  // Deselect any selected table when clicking the background
  emit('select:table', null)
}

function handleTableSelect(id: string) {
  emit('select:table', id)
}

function handlePositionUpdate(id: string, x: number, y: number) {
  emit('update:position', id, x, y)
}

function handleSeatCountUpdate(id: string, seatCount: number) {
  emit('update:seatCount', id, seatCount)
}
</script>

<template>
  <div
    class="planner-canvas"
    :style="canvasStyle"
    @click="handleBackgroundClick"
  >
    <DraggableTable
      v-for="table in tables"
      :key="table.id"
      :table="table"
      :is-selected="table.id === selectedTableId"
      @update:position="handlePositionUpdate"
      @select="handleTableSelect"
      @update:seat-count="handleSeatCountUpdate"
    />

    <!-- Empty state message when no tables -->
    <div v-if="tables.length === 0" class="empty-state">
      <p>Click "Add Table" to start planning your seating arrangement</p>
    </div>
  </div>
</template>

<style scoped>
.planner-canvas {
  position: relative;
  background: linear-gradient(135deg, var(--parchment-medium) 0%, var(--parchment-light) 100%);
  border: 3px solid var(--ornate-border);
  border-radius: 8px;
  box-shadow:
    inset 0 2px 8px var(--shadow-brown),
    0 4px 12px var(--shadow-brown);
  overflow: hidden;
  /* Parchment texture pattern */
  background-image:
    linear-gradient(135deg, var(--parchment-medium) 0%, var(--parchment-light) 100%),
    repeating-linear-gradient(
      90deg,
      transparent,
      transparent 2px,
      rgba(212, 197, 170, 0.1) 2px,
      rgba(212, 197, 170, 0.1) 4px
    );
}

.empty-state {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  text-align: center;
  pointer-events: none;
  user-select: none;
}

.empty-state p {
  font-family: var(--font-elegant);
  font-size: 1.25rem;
  color: var(--faded-text);
  font-style: italic;
  margin: 0;
}
</style>
