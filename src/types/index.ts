/**
 * Represents a guest
 */
export interface Guest {
  /** Unique identifier for the guest */
  id: string

  /** Guest's first name */
  firstName: string

  /** Guest's last name */
  lastName: string

  /** Table assignment (null if unassigned) */
  tableId: string | null

  /** Email address */
  email?: string

  /** Phone number */
  phone?: string

  /** RSVP status */
  rsvpStatus?: string

  /** Dietary restrictions */
  dietaryRestrictions?: string
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

  /** Array of all guests */
  guests: Guest[]

  /** ID of currently selected table (if any) */
  selectedTableId: string | null

  /** ID of currently highlighted guest (if any) */
  highlightedGuestId: string | null

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
