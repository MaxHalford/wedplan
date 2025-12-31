<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { useTablePlannerStore } from '../stores/tablePlanner'
import { TABLE_DEFAULTS } from '../types'
import { useToast } from '../composables/useToast'
import PlannerToolbar from './PlannerToolbar.vue'
import PlannerCanvas from './PlannerCanvas.vue'
import GuestList from './GuestList.vue'
import GroupMatcher from './GroupMatcher.vue'
import ToastNotification from './ToastNotification.vue'

const store = useTablePlannerStore()
const { showToast } = useToast()
const showMatcher = ref(false)
const canvasContainerRef = ref<HTMLElement>()

// Watch for optimization status changes and show toast on infeasible
watch(
  () => store.lastOptimizationStatus,
  (status) => {
    if (status === 'INFEASIBLE') {
      showToast(
        'Cannot find valid seating arrangement. Try relaxing constraints or adding more tables.',
        'error',
        6000
      )
    }
  }
)

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

async function handleDownloadPDF() {
  if (!canvasContainerRef.value) return

  try {
    // Lazy load PDF dependencies only when needed
    const [{ default: html2canvas }, { default: jsPDF }] = await Promise.all([
      import('html2canvas'),
      import('jspdf'),
    ])

    // Find the actual canvas element (PlannerCanvas div)
    const canvasElement = canvasContainerRef.value.querySelector('.planner-canvas') as HTMLElement
    if (!canvasElement) return

    // Capture the canvas as an image
    const canvas = await html2canvas(canvasElement, {
      backgroundColor: '#f4e8d0',
      scale: 2, // Higher quality
      logging: false,
    })

    // Create PDF
    const imgData = canvas.toDataURL('image/png')
    const pdf = new jsPDF({
      orientation: canvas.width > canvas.height ? 'landscape' : 'portrait',
      unit: 'px',
      format: [canvas.width, canvas.height],
    })

    pdf.addImage(imgData, 'PNG', 0, 0, canvas.width, canvas.height)
    pdf.save('wedding-seating-plan.pdf')
  } catch (error) {
    console.error('Failed to generate PDF:', error)
    alert('Failed to generate PDF. Please try again.')
  }
}
</script>

<template>
  <div class="wedding-planner">
    <PlannerToolbar
      @add:table="handleAddTable"
      @import:csv="handleImportCSV"
      @start:matching="handleStartMatching"
      @download:pdf="handleDownloadPDF"
    />
    <div class="main-content">
      <GuestList class="guest-pane" />
      <div ref="canvasContainerRef" class="canvas-container">
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
    <ToastNotification />
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

/* Mobile responsiveness */
@media (max-width: 768px) {
  .main-content {
    flex-direction: column;
  }

  .guest-pane {
    width: 100%;
    max-height: 40vh;
    border-right: none;
    border-bottom: 4px double var(--ornate-border);
  }

  .canvas-container {
    padding: var(--spacing-md);
    min-height: 60vh;
  }
}

@media (max-width: 480px) {
  .canvas-container {
    padding: var(--spacing-sm);
  }
}
</style>
