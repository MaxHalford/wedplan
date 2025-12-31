/**
 * Represents a guest group (people who must sit together)
 */
export interface GuestGroup {
  /** Unique identifier for the group */
  id: string

  /** Names of all guests in this group */
  guestNames: string[]

  /** Number of guests in the group */
  size: number

  /** Table assignment (null if unassigned) */
  tableId: string | null
}

/**
 * Represents a guest (simplified - just part of a group)
 */
export interface Guest {
  /** Guest's name */
  name: string

  /** ID of the group this guest belongs to */
  groupId: string

  /** Table assignment (derived from group) */
  tableId: string | null
}

/**
 * Seating constraint types
 */
export enum ConstraintType {
  /** Group must sit together at same table */
  SAME_TABLE = 'SAME_TABLE',
  /** Groups should sit at different tables */
  DIFFERENT_TABLES = 'DIFFERENT_TABLES',
  /** Group should be close to another group */
  NEARBY = 'NEARBY',
}

/**
 * Represents a seating constraint
 */
export interface Constraint {
  /** Unique identifier */
  id: string

  /** Type of constraint */
  type: ConstraintType

  /** IDs of groups involved in this constraint */
  groupIds: string[]

  /** Optional weight/priority (higher = more important) */
  weight?: number
}

/**
 * Represents a single table on the canvas
 */
export interface Table {
  /** Unique identifier for the table */
  id: string

  /** X coordinate position on canvas (in pixels) */
  x: number

  /** Y coordinate position on canvas (in pixels) */
  y: number

  /** Number of seats at this table */
  seatCount: number

  /** Optional custom label for the table */
  label?: string

  /** Creation timestamp */
  createdAt: number

  /** IDs of guests assigned to this table */
  guestIds: string[]
}

/**
 * Canvas dimensions and settings
 */
export interface CanvasSettings {
  /** Canvas width in pixels */
  width: number

  /** Canvas height in pixels */
  height: number

  /** Optional: Zoom level (1 = 100%) */
  zoom?: number
}

/**
 * Complete planner state
 */
export interface PlannerState {
  /** Array of all tables on the canvas */
  tables: Table[]

  /** Array of all guest groups */
  groups: GuestGroup[]

  /** Array of seating constraints */
  constraints: Constraint[]

  /** ID of currently selected table (if any) */
  selectedTableId: string | null

  /** ID of currently highlighted group (if any) */
  highlightedGroupId: string | null

  /** Canvas configuration */
  canvasSettings: CanvasSettings
}

/**
 * Position update payload
 */
export interface PositionUpdate {
  /** Table ID being moved */
  id: string

  /** New X coordinate */
  x: number

  /** New Y coordinate */
  y: number
}

/**
 * Seat count update payload
 */
export interface SeatCountUpdate {
  /** Table ID being updated */
  id: string

  /** New seat count */
  seatCount: number
}

/**
 * Default table dimensions and constraints
 */
export const TABLE_DEFAULTS = {
  WIDTH: 120,
  HEIGHT: 80,
  DEFAULT_SEAT_COUNT: 8,
  MIN_SEAT_COUNT: 2,
  MAX_SEAT_COUNT: 20,
} as const

/**
 * Default canvas settings
 */
export const CANVAS_DEFAULTS = {
  WIDTH: 1200,
  HEIGHT: 800,
} as const
