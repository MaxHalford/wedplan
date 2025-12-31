<script setup lang="ts">
import { ref, computed, reactive } from 'vue'
import { useGesture } from '@vueuse/gesture'
import { useTablePlannerStore } from '../stores/tablePlanner'
import type { Table } from '../types'
import { TABLE_DEFAULTS } from '../types'
import SeatCountEditor from './SeatCountEditor.vue'

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

// Get all guest names for this table (flattened from groups)
const guestNames = computed(() => {
  return store.getGuestNamesForTable(props.table.id)
})

// Calculate positions for guest initials around the table
const guestPositions = computed(() => {
  const names = guestNames.value
  const count = names.length
  const radius = TABLE_DEFAULTS.WIDTH / 2 + 20 // Position outside the table

  return names.map((name, index) => {
    const angle = (index / count) * 2 * Math.PI - Math.PI / 2 // Start from top
    const x = radius * Math.cos(angle)
    const y = radius * Math.sin(angle)

    // Get initials from name (handle single names and full names)
    const nameParts = name.trim().split(/\s+/)
    const initials = nameParts.length >= 2
      ? `${nameParts[0].charAt(0)}${nameParts[nameParts.length - 1].charAt(0)}`.toUpperCase()
      : name.substring(0, 2).toUpperCase()

    // Find which group this guest belongs to (for highlighting)
    const group = tableGroups.value.find(g => g.guestNames.includes(name))

    return {
      name,
      groupId: group?.id,
      x,
      y,
      initials,
    }
  })
})
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

    <!-- Guest initials around the table -->
    <div
      v-for="(pos, index) in guestPositions"
      :key="`${props.table.id}-guest-${index}`"
      class="guest-initial"
      :class="{ highlighted: pos.groupId === store.highlightedGroupId }"
      :style="{
        left: `calc(50% + ${pos.x}px)`,
        top: `calc(50% + ${pos.y}px)`,
      }"
      :title="pos.name"
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

.seat-count {
  font-family: var(--font-elegant);
  font-size: 2rem;
  font-weight: 600;
  color: var(--burgundy);
  text-shadow: 0 1px 2px rgba(255, 255, 255, 0.8);
  pointer-events: none;
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
  pointer-events: none;
  box-shadow: 0 2px 4px var(--shadow-brown);
  border: 2px solid var(--parchment-light);
  transition: all var(--transition-medium);
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
</style>
