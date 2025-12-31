import { defineStore } from 'pinia'
import type { Table, GuestGroup, Constraint, CanvasSettings } from '../types'
import { TABLE_DEFAULTS, CANVAS_DEFAULTS, ConstraintType, MatchPreference } from '../types'
import {
  buildOptimizeRequest,
  optimizeSeating,
  type SolverStatus,
  type TableAssignment,
} from '../api/optimize'
import Papa from 'papaparse'

const STORAGE_KEY = 'wedding-planner-state'
const DEBOUNCE_DELAY = 300 // milliseconds
const OPTIMIZE_DEBOUNCE_DELAY = 500 // milliseconds

interface TablePlannerState {
  tables: Table[]
  groups: GuestGroup[]
  constraints: Constraint[]
  selectedTableId: string | null
  highlightedGroupId: string | null
  canvasSettings: CanvasSettings
  isOptimizing: boolean
  lastOptimizationStatus: SolverStatus | null
  /** Maps tableId to ordered array of guest identifiers (format: "groupId:guestIndex") */
  seatOrders: Record<string, string[]>
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

// Debounced save function to prevent excessive localStorage writes
let saveTimeout: ReturnType<typeof setTimeout> | null = null
function debouncedSaveStateToLocalStorage(state: TablePlannerState): void {
  if (saveTimeout) {
    clearTimeout(saveTimeout)
  }
  saveTimeout = setTimeout(() => {
    saveStateToLocalStorage(state)
    saveTimeout = null
  }, DEBOUNCE_DELAY)
}

// Immediate save function for critical operations
function immediateSaveStateToLocalStorage(state: TablePlannerState): void {
  if (saveTimeout) {
    clearTimeout(saveTimeout)
    saveTimeout = null
  }
  saveStateToLocalStorage(state)
}

// Debounce timeout for optimization API calls
let optimizeTimeout: ReturnType<typeof setTimeout> | null = null

export const useTablePlannerStore = defineStore('tablePlanner', {
  state: (): TablePlannerState => {
    const savedState = loadStateFromLocalStorage()
    return {
      tables: savedState.tables || [],
      groups: savedState.groups || [],
      constraints: savedState.constraints || [],
      selectedTableId: savedState.selectedTableId || null,
      highlightedGroupId: savedState.highlightedGroupId || null,
      canvasSettings: savedState.canvasSettings || {
        width: CANVAS_DEFAULTS.WIDTH,
        height: CANVAS_DEFAULTS.HEIGHT,
      },
      isOptimizing: false,
      lastOptimizationStatus: null,
      seatOrders: savedState.seatOrders || {},
    }
  },

  getters: {
    /**
     * Get groups assigned to a specific table
     */
    getGroupsForTable: (state) => (tableId: string) => {
      return state.groups.filter(group => group.tableId === tableId)
    },

    /**
     * Get all guest names for a specific table (flattened from groups)
     */
    getGuestNamesForTable: (state) => (tableId: string) => {
      const groups = state.groups.filter(group => group.tableId === tableId)
      return groups.flatMap(group => group.guestNames)
    },

    /**
     * Get ordered guest identifiers for a table.
     * Returns custom seat order if set, otherwise generates default order from groups.
     * Guest ID format: "groupId:guestIndex"
     */
    getSeatOrderForTable: (state) => (tableId: string): string[] => {
      const customOrder = state.seatOrders[tableId]
      if (customOrder && customOrder.length > 0) {
        return customOrder
      }
      // Generate default order from groups assigned to this table
      const groups = state.groups.filter(group => group.tableId === tableId)
      const defaultOrder: string[] = []
      for (const group of groups) {
        for (let i = 0; i < group.guestNames.length; i++) {
          defaultOrder.push(`${group.id}:${i}`)
        }
      }
      return defaultOrder
    },

    /**
     * Get unassigned groups
     */
    unassignedGroups: (state) => {
      return state.groups.filter(group => group.tableId === null)
    },

    /**
     * Get total number of guests
     */
    totalGuestCount: (state) => {
      return state.groups.reduce((sum, group) => sum + group.size, 0)
    },

    /**
     * Get suggested number of tables based on guest count
     */
    suggestedTableCount: (state) => {
      const totalGuests = state.groups.reduce((sum, group) => sum + group.size, 0)
      const avgSeatsPerTable = TABLE_DEFAULTS.DEFAULT_SEAT_COUNT
      return Math.max(1, Math.ceil(totalGuests / avgSeatsPerTable))
    },

    /**
     * Get total available seats across all tables
     */
    totalSeatCount: (state) => {
      return state.tables.reduce((sum, table) => sum + table.seatCount, 0)
    },

    /**
     * Check if we have enough seats for all guests
     */
    hasEnoughSeats: (state) => {
      const totalGuests = state.groups.reduce((sum, group) => sum + group.size, 0)
      const totalSeats = state.tables.reduce((sum, table) => sum + table.seatCount, 0)
      return totalSeats >= totalGuests
    },

    /**
     * Get constraints for optimization algorithm
     */
    sameTableConstraints: (state) => {
      return state.constraints.filter(c => c.type === ConstraintType.SAME_TABLE)
    },

    /**
     * Check if two groups have any constraint between them
     */
    hasConstraintBetween: (state) => (groupId1: string, groupId2: string) => {
      return state.constraints.some(c => {
        const hasGroup1 = c.groupIds.includes(groupId1)
        const hasGroup2 = c.groupIds.includes(groupId2)
        return hasGroup1 && hasGroup2 && c.type !== ConstraintType.SAME_TABLE
      })
    },

    /**
     * Get pairs of groups that don't have constraints yet
     * Excludes single-group constraints (SAME_TABLE)
     */
    unconstrainedPairs: (state) => {
      const pairs: Array<[GuestGroup, GuestGroup]> = []

      for (let i = 0; i < state.groups.length; i++) {
        for (let j = i + 1; j < state.groups.length; j++) {
          const group1 = state.groups[i]
          const group2 = state.groups[j]

          // Check if these groups already have a constraint
          const hasConstraint = state.constraints.some(c => {
            if (c.type === ConstraintType.SAME_TABLE) return false // Skip SAME_TABLE
            const hasGroup1 = c.groupIds.includes(group1.id)
            const hasGroup2 = c.groupIds.includes(group2.id)
            return hasGroup1 && hasGroup2
          })

          if (!hasConstraint) {
            pairs.push([group1, group2])
          }
        }
      }

      return pairs
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
      }
      this.tables.push(newTable)

      // Automatically optimize assignments when a new table is added
      if (this.groups.length > 0 && this.hasEnoughSeats) {
        this.triggerOptimization()
      }

      this.persistState(true) // Immediate save for table creation
    },

    /**
     * Add multiple tables at once with specified seat count.
     * Tables are positioned in a grid layout on the canvas.
     *
     * Args:
     *   count: Number of tables to create (1-20).
     *   seatsPerTable: Number of seats per table (2-20).
     */
    addMultipleTables(count: number, seatsPerTable: number): void {
      const clampedCount = Math.max(1, Math.min(20, count))
      const clampedSeats = Math.max(
        TABLE_DEFAULTS.MIN_SEAT_COUNT,
        Math.min(TABLE_DEFAULTS.MAX_SEAT_COUNT, seatsPerTable)
      )

      // Calculate grid dimensions
      const cols = Math.ceil(Math.sqrt(clampedCount))
      const tableSpacingX = TABLE_DEFAULTS.WIDTH + 40
      const tableSpacingY = TABLE_DEFAULTS.HEIGHT + 60

      // Calculate starting position to center the grid
      const gridWidth = cols * tableSpacingX
      const gridHeight = Math.ceil(clampedCount / cols) * tableSpacingY
      const startX = Math.max(20, (this.canvasSettings.width - gridWidth) / 2)
      const startY = Math.max(20, (this.canvasSettings.height - gridHeight) / 2)

      for (let i = 0; i < clampedCount; i++) {
        const col = i % cols
        const row = Math.floor(i / cols)

        const newTable: Table = {
          id: crypto.randomUUID(),
          x: startX + col * tableSpacingX,
          y: startY + row * tableSpacingY,
          seatCount: clampedSeats,
          createdAt: Date.now(),
        }
        this.tables.push(newTable)
      }

      // Trigger optimization after all tables are added if we have enough seats
      if (this.groups.length > 0 && this.hasEnoughSeats) {
        this.triggerOptimization()
      }

      this.persistState(true) // Immediate save for table creation
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

        // Re-optimize when capacity changes if we have enough seats
        if (this.groups.length > 0 && this.hasEnoughSeats) {
          this.triggerOptimization()
        }
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
        // Unassign all groups from this table
        const table = this.tables[index]
        this.groups.forEach(group => {
          if (group.tableId === table.id) {
            group.tableId = null
          }
        })

        this.tables.splice(index, 1)
        if (this.selectedTableId === id) {
          this.selectedTableId = null
        }
        this.persistState(true) // Immediate save for table deletion
      }
    },

    /**
     * Import guests from CSV (new format: each row is a group)
     * Columns in each row are guest names that must sit together
     */
    async importGuestsFromCSV(file: File): Promise<void> {
      return new Promise((resolve, reject) => {
        Papa.parse(file, {
          header: false, // No headers - just comma-separated names
          complete: (results) => {
            const newGroups: GuestGroup[] = []
            const newConstraints: Constraint[] = []

            // Each row is a group of people who must sit together
            results.data.forEach((row: any) => {
              if (!Array.isArray(row)) return

              // Filter out empty values
              const guestNames = row.filter((name: string) => name && name.trim())

              if (guestNames.length > 0) {
                const groupId = crypto.randomUUID()

                // Create the group
                newGroups.push({
                  id: groupId,
                  guestNames,
                  size: guestNames.length,
                  tableId: null,
                })

                // Create SAME_TABLE constraint for this group
                newConstraints.push({
                  id: crypto.randomUUID(),
                  type: ConstraintType.SAME_TABLE,
                  groupIds: [groupId],
                  weight: 1, // High priority - must be satisfied
                })
              }
            })

            // Clear all existing state when importing new CSV
            this.tables = []
            this.groups = newGroups
            this.constraints = newConstraints
            this.selectedTableId = null
            this.highlightedGroupId = null
            this.seatOrders = {}

            // Note: Optimization will run when user adds tables
            this.persistState(true) // Immediate save for CSV import
            resolve()

            // If tables exist and we have enough seats, trigger optimization
            if (this.tables.length > 0 && this.hasEnoughSeats) {
              this.triggerOptimization()
            }
          },
          error: (error) => {
            reject(error)
          },
        })
      })
    },

    /**
     * Trigger optimization with debouncing to avoid spamming the API.
     */
    triggerOptimization(): void {
      if (optimizeTimeout) {
        clearTimeout(optimizeTimeout)
      }
      optimizeTimeout = setTimeout(() => {
        this.optimizeAssignments()
        optimizeTimeout = null
      }, OPTIMIZE_DEBOUNCE_DELAY)
    },

    /**
     * Run the optimization algorithm via backend API.
     * Replaces the old random assignment with CP-SAT solver optimization.
     */
    async optimizeAssignments(): Promise<void> {
      if (this.tables.length === 0 || this.groups.length === 0) {
        return
      }

      this.isOptimizing = true

      try {
        const request = buildOptimizeRequest(this.tables, this.groups, this.constraints)
        const response = await optimizeSeating(request)

        this.lastOptimizationStatus = response.status

        if (response.status === 'INFEASIBLE') {
          // Toast will be shown by component watching this state
          return
        }

        if (response.status === 'OPTIMAL' || response.status === 'FEASIBLE') {
          this.applyAssignments(response.tables)
        }
      } catch (error) {
        console.error('Optimization failed:', error)
        this.lastOptimizationStatus = 'UNKNOWN'
      } finally {
        this.isOptimizing = false
        this.persistState(true)
      }
    },

    /**
     * Apply solver assignments to groups.
     * Maps guest IDs back to groups and updates their tableId.
     */
    applyAssignments(tableAssignments: TableAssignment[]): void {
      // Build map: guestId -> tableId
      const guestToTable = new Map<string, string>()
      for (const ta of tableAssignments) {
        for (const seat of ta.seats) {
          if (seat.guest_id) {
            guestToTable.set(seat.guest_id, ta.table_id)
          }
        }
      }

      // Update each group's tableId based on first guest
      for (const group of this.groups) {
        // Guest ID format: `${group.id}:${index}`
        const firstGuestId = `${group.id}:0`
        const tableId = guestToTable.get(firstGuestId)
        group.tableId = tableId ?? null
      }
    },

    /**
     * Assign a group to a table
     */
    assignGroupToTable(groupId: string, tableId: string | null): void {
      const group = this.groups.find(g => g.id === groupId)
      if (group) {
        // Check if table has space for the entire group
        if (tableId) {
          const table = this.tables.find(t => t.id === tableId)
          if (table) {
            const currentGuestCount = this.groups
              .filter(g => g.tableId === tableId)
              .reduce((sum, g) => sum + g.size, 0)

            if (currentGuestCount + group.size > table.seatCount) {
              console.warn('Table does not have enough space for this group')
              return
            }
          }
        }

        group.tableId = tableId
        this.persistState()
      }
    },

    /**
     * Highlight a group
     */
    highlightGroup(groupId: string | null): void {
      this.highlightedGroupId = groupId
      // Don't persist - it's transient UI state
    },

    /**
     * Swap the seat positions of two guests at the same table.
     * Updates the seatOrders record to persist the new arrangement.
     *
     * Args:
     *   tableId: The table where both guests are seated.
     *   guestIdA: First guest identifier (format: "groupId:guestIndex").
     *   guestIdB: Second guest identifier (format: "groupId:guestIndex").
     */
    swapGuestSeats(tableId: string, guestIdA: string, guestIdB: string): void {
      if (guestIdA === guestIdB) {
        return
      }

      // Get current seat order (or default)
      const currentOrder = this.getSeatOrderForTable(tableId)
      const indexA = currentOrder.indexOf(guestIdA)
      const indexB = currentOrder.indexOf(guestIdB)

      if (indexA === -1 || indexB === -1) {
        console.warn('One or both guests not found in seat order')
        return
      }

      // Create new order with swapped positions
      const newOrder = [...currentOrder]
      newOrder[indexA] = guestIdB
      newOrder[indexB] = guestIdA

      // Update the seat order for this table
      this.seatOrders[tableId] = newOrder
      this.persistState()
    },

    /**
     * Add a preference constraint between two groups
     */
    addPreferenceConstraint(group1Id: string, group2Id: string, preference: MatchPreference): void {
      // Don't add constraint for neutral preference
      if (preference === MatchPreference.NEUTRAL) {
        return
      }

      // Check if constraint already exists
      const existingConstraint = this.constraints.find(c => {
        if (c.type === ConstraintType.SAME_TABLE) return false
        return c.groupIds.includes(group1Id) && c.groupIds.includes(group2Id)
      })

      if (existingConstraint) {
        console.warn('Constraint already exists between these groups')
        return
      }

      // Map preference to constraint type
      const constraintType = preference === MatchPreference.LIKE
        ? ConstraintType.NEARBY
        : ConstraintType.DIFFERENT_TABLES

      // Create new constraint
      this.constraints.push({
        id: crypto.randomUUID(),
        type: constraintType,
        groupIds: [group1Id, group2Id],
        weight: 0.5, // Lower priority than SAME_TABLE
      })

      this.persistState()

      // Re-optimize when constraints change if we have enough seats
      if (this.tables.length > 0 && this.hasEnoughSeats) {
        this.triggerOptimization()
      }
    },

    /**
     * Persist current state to localStorage
     * @param immediate - If true, saves immediately. Otherwise, debounces the save.
     */
    persistState(immediate = false): void {
      const state = {
        tables: this.tables,
        groups: this.groups,
        constraints: this.constraints,
        selectedTableId: null, // Don't persist selection
        highlightedGroupId: null, // Don't persist highlight
        canvasSettings: this.canvasSettings,
        seatOrders: this.seatOrders,
      }

      if (immediate) {
        immediateSaveStateToLocalStorage(state)
      } else {
        debouncedSaveStateToLocalStorage(state)
      }
    },

    /**
     * Clear all tables and reset state
     */
    clearAll(): void {
      this.tables = []
      this.groups = []
      this.constraints = []
      this.selectedTableId = null
      this.highlightedGroupId = null
      this.seatOrders = {}
      this.persistState(true) // Immediate save for clearing state
    },
  },
})
