import { defineStore } from 'pinia'
import type { Table, Guest, CanvasSettings } from '../types'
import { TABLE_DEFAULTS, CANVAS_DEFAULTS } from '../types'
import Papa from 'papaparse'

const STORAGE_KEY = 'wedding-planner-state'

interface TablePlannerState {
  tables: Table[]
  guests: Guest[]
  selectedTableId: string | null
  highlightedGuestId: string | null
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
      guests: savedState.guests || [],
      selectedTableId: savedState.selectedTableId || null,
      highlightedGuestId: savedState.highlightedGuestId || null,
      canvasSettings: savedState.canvasSettings || {
        width: CANVAS_DEFAULTS.WIDTH,
        height: CANVAS_DEFAULTS.HEIGHT,
      },
    }
  },

  getters: {
    /**
     * Get guests assigned to a specific table
     */
    getGuestsForTable: (state) => (tableId: string) => {
      return state.guests.filter(guest => guest.tableId === tableId)
    },

    /**
     * Get unassigned guests
     */
    unassignedGuests: (state) => {
      return state.guests.filter(guest => guest.tableId === null)
    },
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
        guestIds: [],
      }
      this.tables.push(newTable)

      // Automatically assign unassigned guests when a new table is added
      if (this.guests.length > 0) {
        this.runAssignmentAlgorithm()
      }

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
        // Unassign all guests from this table
        const table = this.tables[index]
        this.guests.forEach(guest => {
          if (guest.tableId === table.id) {
            guest.tableId = null
          }
        })

        this.tables.splice(index, 1)
        if (this.selectedTableId === id) {
          this.selectedTableId = null
        }
        this.persistState()
      }
    },

    /**
     * Import guests from CSV
     */
    async importGuestsFromCSV(file: File): Promise<void> {
      return new Promise((resolve, reject) => {
        Papa.parse(file, {
          header: true,
          complete: (results) => {
            const newGuests: Guest[] = results.data
              .filter((row: any) => row.First_Name && row.Last_Name)
              .map((row: any) => ({
                id: crypto.randomUUID(),
                firstName: row.First_Name,
                lastName: row.Last_Name,
                tableId: null,
                email: row.Email,
                phone: row.Phone,
                rsvpStatus: row.RSVP_Status,
                dietaryRestrictions: row.Dietary_Restrictions,
              }))

            this.guests = newGuests
            this.runAssignmentAlgorithm()
            this.persistState()
            resolve()
          },
          error: (error) => {
            reject(error)
          },
        })
      })
    },

    /**
     * Run the guest assignment algorithm
     * Currently uses random assignment, but can be replaced with optimization algorithm
     */
    runAssignmentAlgorithm(): void {
      // Get all unassigned guests
      const unassigned = this.guests.filter(g => g.tableId === null)

      if (unassigned.length === 0 || this.tables.length === 0) {
        return
      }

      // TODO: Replace this with sophisticated optimization algorithm
      // For now: shuffle guests and assign in round-robin fashion
      const shuffled = [...unassigned].sort(() => Math.random() - 0.5)

      // Assign to tables in round-robin fashion
      let tableIndex = 0
      shuffled.forEach(guest => {
        const table = this.tables[tableIndex % this.tables.length]

        // Only assign if table has space
        const currentGuests = this.guests.filter(g => g.tableId === table.id).length
        if (currentGuests < table.seatCount) {
          guest.tableId = table.id
          tableIndex++
        } else {
          // Try next table with space
          for (let i = 0; i < this.tables.length; i++) {
            const nextTable = this.tables[(tableIndex + i) % this.tables.length]
            const nextTableGuests = this.guests.filter(g => g.tableId === nextTable.id).length
            if (nextTableGuests < nextTable.seatCount) {
              guest.tableId = nextTable.id
              tableIndex = (tableIndex + i + 1) % this.tables.length
              break
            }
          }
        }
      })

      this.persistState()
    },

    /**
     * Assign a guest to a table
     */
    assignGuestToTable(guestId: string, tableId: string | null): void {
      const guest = this.guests.find(g => g.id === guestId)
      if (guest) {
        // Check if table has space
        if (tableId) {
          const table = this.tables.find(t => t.id === tableId)
          if (table) {
            const currentGuests = this.guests.filter(g => g.tableId === tableId).length
            if (currentGuests >= table.seatCount) {
              console.warn('Table is full')
              return
            }
          }
        }

        guest.tableId = tableId
        this.persistState()
      }
    },

    /**
     * Highlight a guest
     */
    highlightGuest(guestId: string | null): void {
      this.highlightedGuestId = guestId
      // Don't persist - it's transient UI state
    },

    /**
     * Persist current state to localStorage
     */
    persistState(): void {
      saveStateToLocalStorage({
        tables: this.tables,
        guests: this.guests,
        selectedTableId: null, // Don't persist selection
        highlightedGuestId: null, // Don't persist highlight
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
