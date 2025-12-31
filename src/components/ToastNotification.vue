<script setup lang="ts">
import { useToast, type ToastType } from '../composables/useToast'

const { toasts, dismissToast } = useToast()

function getIcon(type: ToastType): string {
  switch (type) {
    case 'success':
      return '✓'
    case 'error':
      return '✕'
    case 'warning':
      return '⚠'
    case 'info':
      return 'ℹ'
  }
}
</script>

<template>
  <Teleport to="body">
    <div class="toast-container">
      <TransitionGroup name="toast">
        <div
          v-for="toast in toasts"
          :key="toast.id"
          :class="['toast', `toast--${toast.type}`]"
          @click="dismissToast(toast.id)"
        >
          <span class="toast-icon">{{ getIcon(toast.type) }}</span>
          <span class="toast-message">{{ toast.message }}</span>
          <button class="toast-close" aria-label="Dismiss">✕</button>
        </div>
      </TransitionGroup>
    </div>
  </Teleport>
</template>

<style scoped>
.toast-container {
  position: fixed;
  bottom: var(--spacing-xl);
  right: var(--spacing-xl);
  z-index: 9999;
  display: flex;
  flex-direction: column;
  gap: var(--spacing-sm);
  max-width: 400px;
  pointer-events: none;
}

.toast {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-md) var(--spacing-lg);
  background: linear-gradient(135deg, var(--parchment-light) 0%, var(--parchment-medium) 100%);
  border: 3px solid var(--ornate-border);
  border-radius: 8px;
  box-shadow:
    0 4px 12px var(--shadow-brown),
    inset 0 1px 0 rgba(255, 255, 255, 0.6);
  cursor: pointer;
  pointer-events: auto;
  font-family: var(--font-body);
  color: var(--ink-black);
  transition: transform var(--transition-fast), opacity var(--transition-fast);
}

.toast:hover {
  transform: translateX(-4px);
}

.toast-icon {
  flex-shrink: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  font-size: 1rem;
  font-weight: bold;
}

.toast--success .toast-icon {
  background: var(--forest-green);
  color: white;
}

.toast--error .toast-icon {
  background: var(--deep-red);
  color: white;
}

.toast--warning .toast-icon {
  background: var(--antique-gold);
  color: var(--ink-black);
}

.toast--info .toast-icon {
  background: var(--burgundy);
  color: white;
}

.toast--success {
  border-color: var(--forest-green);
}

.toast--error {
  border-color: var(--deep-red);
}

.toast--warning {
  border-color: var(--antique-gold);
}

.toast--info {
  border-color: var(--burgundy);
}

.toast-message {
  flex: 1;
  font-size: 0.95rem;
  line-height: 1.4;
}

.toast-close {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  padding: 0;
  border: none;
  background: transparent;
  color: var(--faded-text);
  font-size: 1rem;
  cursor: pointer;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color var(--transition-fast), background var(--transition-fast);
}

.toast-close:hover {
  color: var(--deep-red);
  background: rgba(139, 26, 26, 0.1);
}

/* Transition animations */
.toast-enter-active {
  animation: slideIn 0.3s ease;
}

.toast-leave-active {
  animation: slideOut 0.3s ease;
}

@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(100%);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

@keyframes slideOut {
  from {
    opacity: 1;
    transform: translateX(0);
  }
  to {
    opacity: 0;
    transform: translateX(100%);
  }
}

/* Mobile responsiveness */
@media (max-width: 480px) {
  .toast-container {
    left: var(--spacing-md);
    right: var(--spacing-md);
    bottom: var(--spacing-md);
    max-width: none;
  }
}
</style>
