/**
 * Tests for tablePlanner store - multi-table creation and optimization triggers.
 */
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useTablePlannerStore } from './tablePlanner'
import { TABLE_DEFAULTS } from '../types'

// Mock the optimize API
vi.mock('../api/optimize', () => ({
  buildOptimizeRequest: vi.fn(),
  optimizeSeating: vi.fn().mockResolvedValue({
    status: 'OPTIMAL',
    objective_value: 0,
    tables: [],
    solver_stats: { conflicts: 0, branches: 0, wall_time_seconds: 0 },
  }),
}))

describe('tablePlanner store', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    // Clear localStorage
    localStorage.clear()
    // Reset timers
    vi.useFakeTimers()
  })

  describe('addMultipleTables', () => {
    it('creates the correct number of tables', () => {
      const store = useTablePlannerStore()

      store.addMultipleTables(5, 8)

      expect(store.tables.length).toBe(5)
    })

    it('sets correct seat count for all tables', () => {
      const store = useTablePlannerStore()

      store.addMultipleTables(3, 10)

      store.tables.forEach((table) => {
        expect(table.seatCount).toBe(10)
      })
    })

    it('clamps table count to valid range (1-20)', () => {
      const store = useTablePlannerStore()

      store.addMultipleTables(25, 8)
      expect(store.tables.length).toBe(20)

      store.tables = []
      store.addMultipleTables(-5, 8)
      expect(store.tables.length).toBe(1)
    })

    it('clamps seat count to valid range', () => {
      const store = useTablePlannerStore()

      store.addMultipleTables(1, 50)
      expect(store.tables[0].seatCount).toBe(TABLE_DEFAULTS.MAX_SEAT_COUNT)

      store.tables = []
      store.addMultipleTables(1, 1)
      expect(store.tables[0].seatCount).toBe(TABLE_DEFAULTS.MIN_SEAT_COUNT)
    })

    it('positions tables in a grid layout', () => {
      const store = useTablePlannerStore()

      store.addMultipleTables(4, 8)

      // With 4 tables, should be 2x2 grid
      const positions = store.tables.map((t) => ({ x: t.x, y: t.y }))
      const uniquePositions = new Set(positions.map((p) => `${p.x},${p.y}`))

      // All tables should have unique positions
      expect(uniquePositions.size).toBe(4)
    })
  })

  describe('seat capacity getters', () => {
    it('calculates totalSeatCount correctly', () => {
      const store = useTablePlannerStore()

      store.addMultipleTables(3, 8)

      expect(store.totalSeatCount).toBe(24)
    })

    it('hasEnoughSeats returns true when seats >= guests', () => {
      const store = useTablePlannerStore()

      // Add some guest groups
      store.groups = [
        { id: '1', guestNames: ['Alice', 'Bob'], size: 2, tableId: null },
        { id: '2', guestNames: ['Charlie'], size: 1, tableId: null },
      ]

      // Add enough tables
      store.addMultipleTables(1, 8)

      expect(store.hasEnoughSeats).toBe(true)
    })

    it('hasEnoughSeats returns false when seats < guests', () => {
      const store = useTablePlannerStore()

      // Add many guest groups
      store.groups = [
        { id: '1', guestNames: ['A', 'B', 'C', 'D', 'E'], size: 5, tableId: null },
        { id: '2', guestNames: ['F', 'G', 'H', 'I', 'J'], size: 5, tableId: null },
      ]

      // Add insufficient tables
      store.addMultipleTables(1, 4)

      expect(store.hasEnoughSeats).toBe(false)
    })

    it('suggestedTableCount calculates correctly', () => {
      const store = useTablePlannerStore()

      // 16 guests / 8 seats per table = 2 tables
      store.groups = [
        { id: '1', guestNames: Array(8).fill('Guest'), size: 8, tableId: null },
        { id: '2', guestNames: Array(8).fill('Guest'), size: 8, tableId: null },
      ]

      expect(store.suggestedTableCount).toBe(2)
    })
  })

  describe('optimization triggers', () => {
    it('does not trigger optimization when hasEnoughSeats is false', async () => {
      const store = useTablePlannerStore()
      const triggerSpy = vi.spyOn(store, 'optimizeAssignments')

      // Add guests but insufficient seats
      store.groups = [
        { id: '1', guestNames: Array(20).fill('Guest'), size: 20, tableId: null },
      ]

      // Add single small table (not enough seats)
      store.addMultipleTables(1, 4)

      // Fast forward past debounce
      vi.advanceTimersByTime(600)

      expect(triggerSpy).not.toHaveBeenCalled()
    })

    it('triggers optimization when hasEnoughSeats is true', async () => {
      const store = useTablePlannerStore()
      const triggerSpy = vi.spyOn(store, 'optimizeAssignments')

      // Add guests
      store.groups = [
        { id: '1', guestNames: ['Alice', 'Bob'], size: 2, tableId: null },
      ]

      // Add enough tables
      store.addMultipleTables(1, 8)

      // Fast forward past debounce
      vi.advanceTimersByTime(600)

      expect(triggerSpy).toHaveBeenCalled()
    })

    it('triggers optimization when preference constraint is added with enough seats', async () => {
      const store = useTablePlannerStore()
      const triggerSpy = vi.spyOn(store, 'optimizeAssignments')

      // Setup: groups with enough seats
      store.groups = [
        { id: 'g1', guestNames: ['Alice'], size: 1, tableId: null },
        { id: 'g2', guestNames: ['Bob'], size: 1, tableId: null },
      ]
      store.addMultipleTables(1, 8)

      // Clear previous calls
      triggerSpy.mockClear()

      // Add preference constraint
      store.addPreferenceConstraint('g1', 'g2', 'LIKE' as never)

      // Fast forward past debounce
      vi.advanceTimersByTime(600)

      expect(triggerSpy).toHaveBeenCalled()
    })
  })
})
