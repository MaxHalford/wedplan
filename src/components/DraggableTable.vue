<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useGesture } from '@vueuse/gesture'
import type { Table } from '../types'
import { TABLE_DEFAULTS } from '../types'
import SeatCountEditor from './SeatCountEditor.vue'

interface Props {
  table: Table
  isSelected: boolean
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:position': [id: string, x: number, y: number]
  select: [id: string]
  'update:seatCount': [id: string, seatCount: number]
}>()

const tableRef = ref<HTMLElement>()
const isEditing = ref(false)
const isDragging = ref(false)

// Local position for smooth dragging
const position = reactive({
  x: props.table.x,
  y: props.table.y,
})

// Update local position when prop changes (for initial positioning)
const updatePosition = () => {
  position.x = props.table.x
  position.y = props.table.y
}

// Initialize position
updatePosition()

// Setup drag gesture
useGesture(
  {
    onDrag: ({ movement: [mx, my], dragging, first }) => {
      isDragging.value = dragging
      if (first) {
        // Store the initial position when drag starts
        position.x = props.table.x
        position.y = props.table.y
      }
      // Apply movement to initial position
      position.x = props.table.x + mx
      position.y = props.table.y + my
    },
    onDragEnd: () => {
      isDragging.value = false
      emit('update:position', props.table.id, position.x, position.y)
    },
  },
  {
    domTarget: tableRef,
  }
)

const tableStyle = computed(() => ({
  transform: `translate(${position.x}px, ${position.y}px)`,
  width: `${TABLE_DEFAULTS.WIDTH}px`,
  height: `${TABLE_DEFAULTS.HEIGHT}px`,
  cursor: isDragging.value ? 'grabbing' : 'grab',
}))

function handleClick(event: MouseEvent) {
  // Don't trigger selection/edit if we just finished dragging
  if (isDragging.value) return

  event.stopPropagation()

  // If not selected, select it first
  if (!props.isSelected) {
    emit('select', props.table.id)
  } else {
    // If already selected, toggle edit mode
    isEditing.value = !isEditing.value
  }
}

function handleSeatCountUpdate(newCount: number) {
  emit('update:seatCount', props.table.id, newCount)
  isEditing.value = false
}
</script>

<template>
  <div
    ref="tableRef"
    class="draggable-table"
    :class="{ selected: isSelected, dragging: isDragging }"
    :style="tableStyle"
    @click="handleClick"
  >
    <div class="table-content">
      <SeatCountEditor
        v-if="isEditing"
        :model-value="table.seatCount"
        :min="TABLE_DEFAULTS.MIN_SEAT_COUNT"
        :max="TABLE_DEFAULTS.MAX_SEAT_COUNT"
        @update:model-value="handleSeatCountUpdate"
        @blur="isEditing = false"
      />
      <div v-else class="seat-count">
        {{ table.seatCount }}
      </div>
    </div>
  </div>
</template>

<style scoped>
.draggable-table {
  position: absolute;
  top: 0;
  left: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--parchment-light) 0%, var(--parchment-medium) 100%);
  border: 3px solid var(--ornate-border);
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 0.5),
    inset 0 -2px 4px var(--shadow-brown),
    0 4px 8px var(--shadow-brown);
  transition: box-shadow var(--transition-medium), border-color var(--transition-medium), border-width var(--transition-medium);
  user-select: none;
  touch-action: none;
  will-change: transform;
}

.draggable-table:hover {
  border-color: var(--gold);
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 0.5),
    inset 0 -2px 4px var(--shadow-brown),
    0 6px 12px var(--shadow-brown),
    0 0 0 2px rgba(212, 175, 55, 0.3);
}

.draggable-table.selected {
  border-color: var(--gold);
  border-width: 4px;
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 0.5),
    inset 0 -2px 4px var(--shadow-brown),
    0 6px 16px var(--shadow-brown),
    0 0 0 3px rgba(212, 175, 55, 0.4);
}

.draggable-table.dragging {
  cursor: grabbing;
  opacity: 0.95;
  box-shadow:
    inset 0 2px 4px rgba(255, 255, 255, 0.5),
    inset 0 -2px 4px var(--shadow-brown),
    0 8px 20px var(--shadow-brown);
}

.table-content {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.seat-count {
  font-family: var(--font-elegant);
  font-size: 2rem;
  font-weight: 600;
  color: var(--burgundy);
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
  pointer-events: none;
}
</style>
