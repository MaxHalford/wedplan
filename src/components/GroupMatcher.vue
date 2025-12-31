<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useTablePlannerStore } from '../stores/tablePlanner'
import { MatchPreference } from '../types'

const emit = defineEmits<{
  close: []
}>()

const store = useTablePlannerStore()
const currentPairIndex = ref(0)

// Get all unconstrained pairs
const pairs = computed(() => store.unconstrainedPairs)

const currentPair = computed(() => {
  if (currentPairIndex.value >= pairs.value.length) {
    return null
  }
  return pairs.value[currentPairIndex.value]
})

const progress = computed(() => {
  if (pairs.value.length === 0) return 100
  return Math.round((currentPairIndex.value / pairs.value.length) * 100)
})

function handlePreference(preference: MatchPreference) {
  if (!currentPair.value) return

  const [group1, group2] = currentPair.value

  // Add constraint to store
  store.addPreferenceConstraint(group1.id, group2.id, preference)

  // Move to next pair
  currentPairIndex.value++

  // Close modal if no more pairs
  if (currentPairIndex.value >= pairs.value.length) {
    setTimeout(() => emit('close'), 500)
  }
}

function handleKeyDown(event: KeyboardEvent) {
  if (event.key === 'Escape') {
    emit('close')
  } else if (event.key === 'ArrowLeft') {
    handlePreference(MatchPreference.DISLIKE)
  } else if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
    handlePreference(MatchPreference.NEUTRAL)
  } else if (event.key === 'ArrowRight') {
    handlePreference(MatchPreference.LIKE)
  }
}

onMounted(() => {
  window.addEventListener('keydown', handleKeyDown)
})

onUnmounted(() => {
  window.removeEventListener('keydown', handleKeyDown)
})

function getGroupDisplay(guestNames: string[]): string {
  return guestNames.join(', ')
}
</script>

<template>
  <div class="matcher-overlay" @click.self="$emit('close')">
    <div class="matcher-modal">
      <div class="matcher-header">
        <h2>Match Groups</h2>
        <button @click="$emit('close')" class="close-button">✕</button>
      </div>

      <div class="matcher-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
        </div>
        <div class="progress-text">
          {{ currentPairIndex }} / {{ pairs.length }}
        </div>
      </div>

      <div v-if="currentPair" class="matcher-content">
        <div class="group-card">
          <div class="group-label">Group 1</div>
          <div class="group-names">
            {{ getGroupDisplay(currentPair[0].guestNames) }}
          </div>
          <div class="group-size-badge">{{ currentPair[0].size }} people</div>
        </div>

        <div class="vs-divider">
          <span class="vs-text">with</span>
        </div>

        <div class="group-card">
          <div class="group-label">Group 2</div>
          <div class="group-names">
            {{ getGroupDisplay(currentPair[1].guestNames) }}
          </div>
          <div class="group-size-badge">{{ currentPair[1].size }} people</div>
        </div>
      </div>

      <div v-else class="matcher-complete">
        <div class="complete-icon">✓</div>
        <h3>All Done!</h3>
        <p>You've matched all available group pairs</p>
      </div>

      <div v-if="currentPair" class="matcher-actions">
        <button
          @click="handlePreference(MatchPreference.DISLIKE)"
          class="action-button dislike"
          title="Keep apart (Left Arrow)"
        >
          <span class="button-icon">👎</span>
          <span class="button-label">Dislike</span>
          <span class="button-hint">←</span>
        </button>

        <button
          @click="handlePreference(MatchPreference.NEUTRAL)"
          class="action-button neutral"
          title="No preference (Up/Down Arrow)"
        >
          <span class="button-icon">😐</span>
          <span class="button-label">Neutral</span>
          <span class="button-hint">↑↓</span>
        </button>

        <button
          @click="handlePreference(MatchPreference.LIKE)"
          class="action-button like"
          title="Seat nearby (Right Arrow)"
        >
          <span class="button-icon">👍</span>
          <span class="button-label">Like</span>
          <span class="button-hint">→</span>
        </button>
      </div>

      <div class="matcher-help">
        <p><strong>Dislike:</strong> Keep these groups at different tables</p>
        <p><strong>Neutral:</strong> No preference (skip)</p>
        <p><strong>Like:</strong> Seat these groups close together</p>
      </div>
    </div>
  </div>
</template>

<style scoped>
.matcher-overlay {
  position: fixed;
  inset: 0;
  background: rgba(44, 24, 16, 0.85);
  backdrop-filter: blur(4px);
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  animation: fadeIn 0.2s ease;
}

@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.matcher-modal {
  background: linear-gradient(135deg, var(--parchment-light) 0%, var(--parchment-medium) 100%);
  border: 4px double var(--ornate-border);
  border-radius: 12px;
  box-shadow:
    0 8px 32px var(--shadow-brown),
    inset 0 2px 0 rgba(255, 255, 255, 0.6);
  max-width: 600px;
  width: 100%;
  max-height: 90vh;
  overflow-y: auto;
  animation: slideUp 0.3s ease;
}

@keyframes slideUp {
  from {
    transform: translateY(30px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}

.matcher-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-lg) var(--spacing-xl);
  border-bottom: 3px solid var(--ornate-border);
  background: linear-gradient(to bottom, var(--parchment-light), transparent);
}

.matcher-header h2 {
  margin: 0;
  color: var(--burgundy);
  font-size: 1.75rem;
}

.close-button {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  color: var(--faded-text);
}

.close-button:hover {
  color: var(--burgundy);
}

.matcher-progress {
  padding: var(--spacing-md) var(--spacing-xl);
  border-bottom: 2px solid var(--parchment-dark);
}

.progress-bar {
  height: 8px;
  background: var(--parchment-dark);
  border-radius: 4px;
  overflow: hidden;
  margin-bottom: var(--spacing-xs);
}

.progress-fill {
  height: 100%;
  background: linear-gradient(90deg, var(--burgundy), var(--gold));
  transition: width 0.3s ease;
  border-radius: 4px;
}

.progress-text {
  text-align: center;
  font-family: var(--font-elegant);
  font-size: 0.9rem;
  color: var(--faded-text);
}

.matcher-content {
  padding: var(--spacing-xl);
  display: flex;
  flex-direction: column;
  gap: var(--spacing-lg);
}

.group-card {
  background: white;
  border: 3px solid var(--ornate-border);
  border-radius: 8px;
  padding: var(--spacing-lg);
  box-shadow: 0 4px 8px var(--shadow-brown);
  position: relative;
}

.group-label {
  font-family: var(--font-elegant);
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--burgundy);
  text-transform: uppercase;
  letter-spacing: 0.05em;
  margin-bottom: var(--spacing-sm);
}

.group-names {
  font-family: var(--font-body);
  font-size: 1.25rem;
  font-weight: 600;
  color: var(--ink-black);
  line-height: 1.5;
  margin-bottom: var(--spacing-sm);
}

.group-size-badge {
  display: inline-block;
  background: var(--gold);
  color: var(--ink-black);
  font-family: var(--font-elegant);
  font-size: 0.85rem;
  font-weight: 600;
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: 12px;
}

.vs-divider {
  text-align: center;
  position: relative;
  height: 1px;
  background: var(--parchment-dark);
}

.vs-text {
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  background: var(--parchment-medium);
  padding: 0 var(--spacing-md);
  font-family: var(--font-decorative);
  font-size: 1rem;
  color: var(--faded-text);
}

.matcher-complete {
  padding: var(--spacing-xl);
  text-align: center;
}

.complete-icon {
  font-size: 4rem;
  color: var(--gold);
  margin-bottom: var(--spacing-md);
}

.matcher-complete h3 {
  margin: 0 0 var(--spacing-sm) 0;
  color: var(--burgundy);
}

.matcher-complete p {
  margin: 0;
  color: var(--faded-text);
}

.matcher-actions {
  display: flex;
  gap: var(--spacing-md);
  padding: var(--spacing-md) var(--spacing-xl);
  border-top: 2px solid var(--parchment-dark);
}

.action-button {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: var(--spacing-xs);
  padding: var(--spacing-lg) var(--spacing-md);
  font-size: 1rem;
  border-width: 3px;
  transition: all var(--transition-medium);
}

.action-button .button-icon {
  font-size: 2rem;
  line-height: 1;
}

.action-button .button-label {
  font-family: var(--font-elegant);
  font-weight: 600;
  font-size: 0.95rem;
}

.action-button .button-hint {
  font-family: var(--font-elegant);
  font-size: 0.75rem;
  opacity: 0.6;
}

.action-button.dislike {
  border-color: var(--deep-red);
}

.action-button.dislike:hover {
  background: var(--deep-red);
  color: white;
}

.action-button.neutral {
  border-color: var(--faded-text);
}

.action-button.neutral:hover {
  background: var(--faded-text);
  color: white;
}

.action-button.like {
  border-color: var(--forest-green);
}

.action-button.like:hover {
  background: var(--forest-green);
  color: white;
}

.matcher-help {
  padding: var(--spacing-md) var(--spacing-xl);
  background: rgba(139, 105, 20, 0.1);
  border-top: 2px solid var(--parchment-dark);
}

.matcher-help p {
  margin: var(--spacing-xs) 0;
  font-size: 0.85rem;
  color: var(--brown-text);
  line-height: 1.4;
}

.matcher-help strong {
  font-family: var(--font-elegant);
  color: var(--burgundy);
}
</style>
