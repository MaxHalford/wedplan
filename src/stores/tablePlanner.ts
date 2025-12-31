import { defineStore } from 'pinia'
import type { Table, CanvasSettings } from '../types'
import { TABLE_DEFAULTS, CANVAS_DEFAULTS } from '../types'

const STORAGE_KEY = 'wedding-planner-state'

interface TablePlannerState {
  tables: Table[]
  selectedTableId: string | null
  canvasSettings: CanvasSettings
}

function loadStateFromLocalStorage(): Partial<TablePlannerState> {
  try {
    const stored = localStorage.getItem(STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (error) {
    console.error('Failed to load state from localStorage:', error)
  }
  return {}
}

function saveStateToLocalStorage(state: TablePlannerState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch (error) {
    console.error('Failed to save state to localStorage:', error)
  }
}

export const useTablePlannerStore = defineStore('tablePlanner', {
  state: (): TablePlannerState => {
    const savedState = loadStateFromLocalStorage()
    return {
      tables: savedState.tables || [],
      selectedTableId: savedState.selectedTableId || null,
      canvasSettings: savedState.canvasSettings || {
        width: CANVAS_DEFAULTS.WIDTH,
        height: CANVAS_DEFAULTS.HEIGHT,
      },
    }
  },

  actions: {
    /**
     * Add a new table at the specified position
     */
    addTable(x: number, y: number): void {
      const newTable: Table = {
        id: crypto.randomUUID(),
        x,
        y,
        seatCount: TABLE_DEFAULTS.DEFAULT_SEAT_COUNT,
        createdAt: Date.now(),
      }
      this.tables.push(newTable)
      this.persistState()
    },

    /**
     * Update the position of a table
     */
    updateTablePosition(id: string, x: number, y: number): void {
      const table = this.tables.find(t => t.id === id)
      if (table) {
        table.x = x
        table.y = y
        this.persistState()
      }
    },

    /**
     * Update the seat count of a table
     */
    updateTableSeatCount(id: string, seatCount: number): void {
      const table = this.tables.find(t => t.id === id)
      if (table) {
        // Clamp seat count to valid range
        table.seatCount = Math.max(
          TABLE_DEFAULTS.MIN_SEAT_COUNT,
          Math.min(TABLE_DEFAULTS.MAX_SEAT_COUNT, seatCount)
        )
        this.persistState()
      }
    },

    /**
     * Select a table (or deselect if null)
     */
    selectTable(id: string | null): void {
      this.selectedTableId = id
      // Don't persist selection state - it's transient UI state
    },

    /**
     * Remove a table by ID
     */
    removeTable(id: string): void {
      const index = this.tables.findIndex(t => t.id === id)
      if (index !== -1) {
        this.tables.splice(index, 1)
        if (this.selectedTableId === id) {
          this.selectedTableId = null
        }
        this.persistState()
      }
    },

    /**
     * Persist current state to localStorage
     */
    persistState(): void {
      saveStateToLocalStorage({
        tables: this.tables,
        selectedTableId: null, // Don't persist selection
        canvasSettings: this.canvasSettings,
      })
    },

    /**
     * Clear all tables and reset state
     */
    clearAll(): void {
      this.tables = []
      this.selectedTableId = null
      this.persistState()
    },
  },
})
