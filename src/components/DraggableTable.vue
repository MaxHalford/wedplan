<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useGesture } from '@vueuse/gesture'
import { useTablePlannerStore } from '../stores/tablePlanner'
import type { Table } from '../types'
import { TABLE_DEFAULTS } from '../types'
import SeatCountEditor from './SeatCountEditor.vue'
import { getGuestInitials } from '../utils/guestHelpers'

interface Props {
  table: Table
  isSelected: boolean
}

const props = defineProps<Props>()
const store = useTablePlannerStore()

const emit = defineEmits<{
  'update:position': [id: string, x: number, y: number]
  select: [id: string]
  'update:seatCount': [id: string, seatCount: number]
}>()

const tableRef = ref<HTMLElement>()
const isEditing = ref(false)
const isDragging = ref(false)

// Guest drag-and-drop state
const draggedGuestId = ref<string | null>(null)
const dropTargetGuestId = ref<string | null>(null)

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

// Get groups assigned to this table
const tableGroups = computed(() => {
  return store.getGroupsForTable(props.table.id)
})

// Build a map from guestId to guest info for quick lookups
const guestInfoMap = computed(() => {
  const map = new Map<string, { name: string; groupId: string }>()
  for (const group of tableGroups.value) {
    for (let i = 0; i < group.guestNames.length; i++) {
      const guestId = `${group.id}:${i}`
      map.set(guestId, { name: group.guestNames[i], groupId: group.id })
    }
  }
  return map
})

// Calculate positions for guest initials around the table using seat order
const guestPositions = computed(() => {
  const seatOrder = store.getSeatOrderForTable(props.table.id)
  const count = seatOrder.length
  const radius = TABLE_DEFAULTS.WIDTH / 2 + 20 // Position outside the table

  return seatOrder.map((guestId, index) => {
    const angle = (index / count) * 2 * Math.PI - Math.PI / 2 // Start from top
    const x = radius * Math.cos(angle)
    const y = radius * Math.sin(angle)

    const info = guestInfoMap.value.get(guestId)
    const name = info?.name ?? ''
    const groupId = info?.groupId

    return {
      guestId,
      name,
      groupId,
      x,
      y,
      initials: getGuestInitials(name),
    }
  })
})

// Guest drag-and-drop handlers
function handleGuestDragStart(event: DragEvent, guestId: string): void {
  draggedGuestId.value = guestId
  if (event.dataTransfer) {
    event.dataTransfer.effectAllowed = 'move'
    event.dataTransfer.setData('text/plain', guestId)
  }
}

function handleGuestDragOver(event: DragEvent, guestId: string): void {
  event.preventDefault()
  if (draggedGuestId.value && draggedGuestId.value !== guestId) {
    dropTargetGuestId.value = guestId
  }
}

function handleGuestDragLeave(): void {
  dropTargetGuestId.value = null
}

function handleGuestDrop(event: DragEvent, targetGuestId: string): void {
  event.preventDefault()
  if (draggedGuestId.value && draggedGuestId.value !== targetGuestId) {
    store.swapGuestSeats(props.table.id, draggedGuestId.value, targetGuestId)
  }
  draggedGuestId.value = null
  dropTargetGuestId.value = null
}

function handleGuestDragEnd(): void {
  draggedGuestId.value = null
  dropTargetGuestId.value = null
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
      <div v-else class="seat-info">
        <div class="seat-count">{{ table.seatCount }}</div>
        <div v-if="guestPositions.length > 0" class="seat-occupancy">
          {{ guestPositions.length }}/{{ table.seatCount }}
        </div>
      </div>
    </div>

    <!-- Guest initials around the table -->
    <div
      v-for="pos in guestPositions"
      :key="pos.guestId"
      class="guest-initial"
      :class="{
        highlighted: pos.groupId === store.highlightedGroupId,
        dragging: pos.guestId === draggedGuestId,
        'drop-target': pos.guestId === dropTargetGuestId,
      }"
      :style="{
        left: `calc(50% + ${pos.x}px)`,
        top: `calc(50% + ${pos.y}px)`,
      }"
      :title="pos.name"
      draggable="true"
      @dragstart="handleGuestDragStart($event, pos.guestId)"
      @dragover="handleGuestDragOver($event, pos.guestId)"
      @dragleave="handleGuestDragLeave"
      @drop="handleGuestDrop($event, pos.guestId)"
      @dragend="handleGuestDragEnd"
    >
      {{ pos.initials }}
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

.seat-info {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 2px;
  pointer-events: none;
}

.seat-count {
  font-family: var(--font-elegant);
  font-size: 2rem;
  font-weight: 600;
  color: var(--burgundy);
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
  line-height: 1;
}

.seat-occupancy {
  font-family: var(--font-elegant);
  font-size: 0.75rem;
  font-weight: 600;
  color: var(--ornate-border);
  text-shadow: 0 1px 1px rgba(255, 255, 255, 0.8);
  line-height: 1;
}

.guest-initial {
  position: absolute;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--burgundy);
  color: var(--parchment-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-elegant);
  font-size: 0.75rem;
  font-weight: 600;
  transform: translate(-50%, -50%);
  pointer-events: auto;
  cursor: grab;
  box-shadow: 0 2px 4px var(--shadow-brown);
  border: 2px solid var(--parchment-light);
  transition: all var(--transition-medium);
  z-index: 5;
}

.guest-initial:hover {
  transform: translate(-50%, -50%) scale(1.1);
  box-shadow:
    0 3px 6px var(--shadow-brown),
    0 0 0 2px rgba(212, 175, 55, 0.3);
}

.guest-initial.highlighted {
  background: var(--gold);
  color: var(--ink-black);
  border-color: var(--gold);
  box-shadow:
    0 2px 4px var(--shadow-brown),
    0 0 0 3px rgba(212, 175, 55, 0.5);
  transform: translate(-50%, -50%) scale(1.2);
  z-index: 10;
}

.guest-initial.dragging {
  opacity: 0.5;
  cursor: grabbing;
  transform: translate(-50%, -50%) scale(0.9);
  z-index: 20;
}

.guest-initial.drop-target {
  background: var(--gold);
  border-color: var(--burgundy);
  transform: translate(-50%, -50%) scale(1.25);
  box-shadow:
    0 4px 8px var(--shadow-brown),
    0 0 0 4px rgba(212, 175, 55, 0.6);
  z-index: 15;
}
</style>
