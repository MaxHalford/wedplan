/**
 * API service for wedding seating optimization.
 * Communicates with the Python backend at /v1/optimize.
 */

import type { Table, GuestGroup, Constraint } from '../types'
import { ConstraintType } from '../types'

// =============================================================================
// Request Types (matching backend models)
// =============================================================================

interface TableIn {
    id: string
    capacity: number
    label?: string
}

interface GuestIn {
    id: string
    name: string
}

interface GroupIn {
    id: string
    guest_ids: string[]
}

interface AffinityEdgeIn {
    a: string
    b: string
    score: -1 | 0 | 1
}

interface SolveOptions {
    time_limit_seconds?: number
    num_workers?: number
    allow_empty_seats?: boolean
}

interface OptimizeRequest {
    tables: TableIn[]
    guests: GuestIn[]
    groups: GroupIn[]
    affinities: AffinityEdgeIn[]
    options?: SolveOptions
}

// =============================================================================
// Response Types (matching backend models)
// =============================================================================

export type SolverStatus = 'OPTIMAL' | 'FEASIBLE' | 'INFEASIBLE' | 'UNKNOWN' | 'MODEL_INVALID'

export interface SeatAssignment {
    seat_index: number
    guest_id: string | null
    guest_name: string | null
}

export interface TableAssignment {
    table_id: string
    seats: SeatAssignment[]
}

interface SolverStats {
    conflicts: number
    branches: number
    wall_time_seconds: number
}

export interface OptimizeResponse {
    status: SolverStatus
    objective_value: number | null
    tables: TableAssignment[]
    solver_stats: SolverStats
}

// =============================================================================
// API Configuration
// =============================================================================

// In production (Railway), use relative paths since frontend and backend are same origin.
// In development, set VITE_API_BASE to point to the local backend server.
const API_BASE = import.meta.env.VITE_API_BASE ?? ''

// =============================================================================
// Data Mapping Functions
// =============================================================================

/**
 * Build an OptimizeRequest from frontend store data.
 *
 * Maps frontend types to backend request format:
 * - Table.seatCount -> TableIn.capacity
 * - GuestGroup.guestNames -> Individual GuestIn entries
 * - Constraint NEARBY -> AffinityEdgeIn (score: +1)
 * - Constraint DIFFERENT_TABLES -> AffinityEdgeIn (score: -1)
 */
export function buildOptimizeRequest(
    tables: Table[],
    groups: GuestGroup[],
    constraints: Constraint[]
): OptimizeRequest {
    // 1. Map tables
    const tablesIn: TableIn[] = tables.map(t => ({
        id: t.id,
        capacity: t.seatCount,
        label: t.label,
    }))

    // 2. Flatten guests from all groups, generate unique IDs
    const guestsIn: GuestIn[] = []
    const groupsIn: GroupIn[] = []

    for (const group of groups) {
        const guestIds: string[] = []
        for (let i = 0; i < group.guestNames.length; i++) {
            const name = group.guestNames[i]
            // Generate unique guest ID using group ID and index to avoid name collisions
            const guestId = `${group.id}:${i}`
            guestsIn.push({ id: guestId, name })
            guestIds.push(guestId)
        }
        groupsIn.push({ id: group.id, guest_ids: guestIds })
    }

    // 3. Map constraints to affinities (skip SAME_TABLE as it's implicit in groups)
    const affinities: AffinityEdgeIn[] = constraints
        .filter(c => c.type !== ConstraintType.SAME_TABLE && c.groupIds.length === 2)
        .map(c => ({
            a: c.groupIds[0],
            b: c.groupIds[1],
            score: c.type === ConstraintType.NEARBY ? 1 : -1,
        }))

    return {
        tables: tablesIn,
        guests: guestsIn,
        groups: groupsIn,
        affinities,
    }
}

// =============================================================================
// API Call Function
// =============================================================================

/**
 * Call the optimization endpoint.
 *
 * Args:
 *   request: The optimization request with tables, guests, groups, and affinities.
 *
 * Returns:
 *   The optimization response with status and table assignments.
 *
 * Throws:
 *   Error if the API call fails or returns an error status.
 */
export async function optimizeSeating(request: OptimizeRequest): Promise<OptimizeResponse> {
    const response = await fetch(`${API_BASE}/v1/optimize`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(request),
    })

    if (!response.ok) {
        let errorMessage = 'Optimization failed'
        try {
            const error = await response.json()
            errorMessage = error.detail || errorMessage
        } catch {
            // Response wasn't JSON, use status text
            errorMessage = response.statusText || errorMessage
        }
        throw new Error(errorMessage)
    }

    return response.json()
}
