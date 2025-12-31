import { defineStore } from 'pinia'
import type { Table, GuestGroup, Constraint, CanvasSettings } from '../types'
import { TABLE_DEFAULTS, CANVAS_DEFAULTS, ConstraintType, MatchPreference } from '../types'
import Papa from 'papaparse'

const STORAGE_KEY = 'wedding-planner-state'

interface TablePlannerState {
  tables: Table[]
  groups: GuestGroup[]
  constraints: Constraint[]
  selectedTableId: string | null
  highlightedGroupId: string | null
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
      groups: savedState.groups || [],
      constraints: savedState.constraints || [],
      selectedTableId: savedState.selectedTableId || null,
      highlightedGroupId: savedState.highlightedGroupId || null,
      canvasSettings: savedState.canvasSettings || {
        width: CANVAS_DEFAULTS.WIDTH,
        height: CANVAS_DEFAULTS.HEIGHT,
      },
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
        guestIds: [],
      }
      this.tables.push(newTable)

      // Automatically assign unassigned groups when a new table is added
      if (this.groups.length > 0) {
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
        this.persistState()
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

            // Note: Assignment algorithm will run when user adds tables
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
     * Currently uses random assignment, but respects group constraints
     * TODO: Replace with sophisticated optimization algorithm
     */
    runAssignmentAlgorithm(): void {
      // Get all unassigned groups
      const unassigned = this.groups.filter(g => g.tableId === null)

      if (unassigned.length === 0 || this.tables.length === 0) {
        return
      }

      // TODO: Replace this with sophisticated optimization algorithm
      // For now: shuffle groups and assign in round-robin fashion
      // IMPORTANT: Groups must stay together (SAME_TABLE constraint)
      const shuffled = [...unassigned].sort(() => Math.random() - 0.5)

      // Assign to tables in round-robin fashion
      let tableIndex = 0
      shuffled.forEach(group => {
        let assigned = false

        // Try to find a table with enough space for the entire group
        for (let i = 0; i < this.tables.length; i++) {
          const table = this.tables[(tableIndex + i) % this.tables.length]

          // Count current guests at this table
          const currentGuestCount = this.groups
            .filter(g => g.tableId === table.id)
            .reduce((sum, g) => sum + g.size, 0)

          // Check if group fits at this table
          if (currentGuestCount + group.size <= table.seatCount) {
            group.tableId = table.id
            tableIndex = (tableIndex + i + 1) % this.tables.length
            assigned = true
            break
          }
        }

        // If group couldn't be assigned, leave it unassigned
        // (This means table is too small for the group)
        if (!assigned) {
          console.warn(`Group of ${group.size} (${group.guestNames.join(', ')}) could not be assigned - no table has enough space`)
        }
      })

      this.persistState()
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
    },

    /**
     * Persist current state to localStorage
     */
    persistState(): void {
      saveStateToLocalStorage({
        tables: this.tables,
        groups: this.groups,
        constraints: this.constraints,
        selectedTableId: null, // Don't persist selection
        highlightedGroupId: null, // Don't persist highlight
        canvasSettings: this.canvasSettings,
      })
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
      this.persistState()
    },
  },
})
