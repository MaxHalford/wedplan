/**
 * Toast notification composable.
 * Provides a reactive toast system for displaying notifications.
 */

import { ref } from 'vue'

export type ToastType = 'success' | 'error' | 'warning' | 'info'

export interface Toast {
    id: number
    message: string
    type: ToastType
}

// Shared reactive state for toasts (singleton pattern)
const toasts = ref<Toast[]>([])
let nextId = 0

/**
 * Composable for managing toast notifications.
 *
 * Returns:
 *   toasts: Reactive array of current toasts.
 *   showToast: Function to display a new toast.
 *   dismissToast: Function to manually dismiss a toast.
 */
export function useToast() {
    /**
     * Display a toast notification.
     *
     * Args:
     *   message: The message to display.
     *   type: Toast type (success, error, warning, info). Defaults to 'info'.
     *   duration: Auto-dismiss duration in ms. Defaults to 4000ms.
     */
    function showToast(message: string, type: ToastType = 'info', duration = 4000): void {
        const id = nextId++
        toasts.value.push({ id, message, type })

        setTimeout(() => {
            dismissToast(id)
        }, duration)
    }

    /**
     * Dismiss a toast by ID.
     *
     * Args:
     *   id: The toast ID to dismiss.
     */
    function dismissToast(id: number): void {
        toasts.value = toasts.value.filter(t => t.id !== id)
    }

    return { toasts, showToast, dismissToast }
}
