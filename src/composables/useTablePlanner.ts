import { reactive, readonly } from 'vue'
import type { PlannerState, Table } from '../types'
import { TABLE_DEFAULTS, CANVAS_DEFAULTS } from '../types'

const state = reactive<PlannerState>({
  tables: [],
  selectedTableId: null,
  canvasSettings: {
    width: CANVAS_DEFAULTS.WIDTH,
    height: CANVAS_DEFAULTS.HEIGHT,
  },
})

export function useTablePlanner() {
  /**
   * Add a new table at the specified position
   */
  function addTable(x: number, y: number): void {
    const newTable: Table = {
      id: crypto.randomUUID(),
      x,
      y,
      seatCount: TABLE_DEFAULTS.DEFAULT_SEAT_COUNT,
      createdAt: Date.now(),
    }
    state.tables.push(newTable)
  }

  /**
   * Update the position of a table
   */
  function updateTablePosition(id: string, x: number, y: number): void {
    const table = state.tables.find(t => t.id === id)
    if (table) {
      table.x = x
      table.y = y
    }
  }

  /**
   * Update the seat count of a table
   */
  function updateTableSeatCount(id: string, seatCount: number): void {
    const table = state.tables.find(t => t.id === id)
    if (table) {
      // Clamp seat count to valid range
      table.seatCount = Math.max(
        TABLE_DEFAULTS.MIN_SEAT_COUNT,
        Math.min(TABLE_DEFAULTS.MAX_SEAT_COUNT, seatCount)
      )
    }
  }

  /**
   * Select a table (or deselect if null)
   */
  function selectTable(id: string | null): void {
    state.selectedTableId = id
  }

  /**
   * Remove a table by ID
   */
  function removeTable(id: string): void {
    const index = state.tables.findIndex(t => t.id === id)
    if (index !== -1) {
      state.tables.splice(index, 1)
      if (state.selectedTableId === id) {
        state.selectedTableId = null
      }
    }
  }

  return {
    state: readonly(state),
    addTable,
    updateTablePosition,
    updateTableSeatCount,
    selectTable,
    removeTable,
  }
}
