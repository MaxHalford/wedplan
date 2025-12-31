<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { useTablePlannerStore } from '../stores/tablePlanner'
import { MatchPreference } from '../types'
import type { GuestGroup } from '../types'

const emit = defineEmits<{
  close: []
}>()

const store = useTablePlannerStore()
const currentPairIndex = ref(0)

// Search functionality
const search1 = ref('')
const search2 = ref('')
const showDropdown1 = ref(false)
const showDropdown2 = ref(false)
const selectedGroup1 = ref<GuestGroup | null>(null)
const selectedGroup2 = ref<GuestGroup | null>(null)
const isManualMode = ref(false)

// Get all unconstrained pairs
const pairs = computed(() => store.unconstrainedPairs)

// Filter groups based on search query
function filterGroups(query: string, excludeGroup?: GuestGroup | null): GuestGroup[] {
  if (!query.trim()) return []

  const lowerQuery = query.toLowerCase()
  return store.groups.filter(group => {
    // Exclude the other selected group
    if (excludeGroup && group.id === excludeGroup.id) return false

    // Search in guest names
    return group.guestNames.some(name =>
      name.toLowerCase().includes(lowerQuery)
    )
  }).slice(0, 5) // Limit to 5 results
}

const filteredGroups1 = computed(() => filterGroups(search1.value, selectedGroup2.value))
const filteredGroups2 = computed(() => filterGroups(search2.value, selectedGroup1.value))

// Check if selected groups already have a constraint
const hasExistingConstraint = computed(() => {
  if (!selectedGroup1.value || !selectedGroup2.value) return false
  return store.hasConstraintBetween(selectedGroup1.value.id, selectedGroup2.value.id)
})

function selectGroup1(group: GuestGroup) {
  selectedGroup1.value = group
  search1.value = ''
  showDropdown1.value = false
  isManualMode.value = true
}

function selectGroup2(group: GuestGroup) {
  selectedGroup2.value = group
  search2.value = ''
  showDropdown2.value = false
  isManualMode.value = true
}

function clearGroup1() {
  selectedGroup1.value = null
  search1.value = ''
}

function clearGroup2() {
  selectedGroup2.value = null
  search2.value = ''
}

function switchToAutoMode() {
  isManualMode.value = false
  selectedGroup1.value = null
  selectedGroup2.value = null
  search1.value = ''
  search2.value = ''
}

const currentPair = computed(() => {
  // If in manual mode, only return pair when both groups are selected
  if (isManualMode.value) {
    if (selectedGroup1.value && selectedGroup2.value) {
      return [selectedGroup1.value, selectedGroup2.value] as [GuestGroup, GuestGroup]
    }
    return null // Don't fall through to auto pairs in manual mode
  }

  // Auto mode: use unconstrained pairs
  if (currentPairIndex.value >= pairs.value.length) {
    return null
  }
  return pairs.value[currentPairIndex.value]
})

const progress = computed(() => {
  if (pairs.value.length === 0) return 100
  return Math.round((currentPairIndex.value / pairs.value.length) * 100)
})

// Count total preference constraints (excluding SAME_TABLE)
const totalConstraints = computed(() => {
  return store.constraints.filter(c => c.type !== 'SAME_TABLE').length
})

function handlePreference(preference: MatchPreference) {
  if (!currentPair.value) return

  const [group1, group2] = currentPair.value

  // Add constraint to store
  store.addPreferenceConstraint(group1.id, group2.id, preference)

  if (isManualMode.value) {
    // In manual mode, clear selections after setting preference
    selectedGroup1.value = null
    selectedGroup2.value = null
    search1.value = ''
    search2.value = ''
  } else {
    // Move to next pair in auto mode
    currentPairIndex.value++

    // Close modal if no more pairs
    if (currentPairIndex.value >= pairs.value.length) {
      setTimeout(() => emit('close'), 500)
    }
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

      <!-- Progress bar for auto mode -->
      <div v-if="!isManualMode" class="matcher-progress">
        <div class="progress-bar">
          <div class="progress-fill" :style="{ width: `${progress}%` }"></div>
        </div>
        <div class="progress-text">
          {{ currentPairIndex }} / {{ pairs.length }} pairs matched
        </div>
      </div>

      <!-- Stats for manual/search mode -->
      <div v-else class="matcher-progress matcher-progress-manual">
        <div class="progress-text">
          {{ totalConstraints }} preferences set
        </div>
      </div>

      <!-- Mode toggle -->
      <div class="mode-toggle">
        <button
          :class="{ active: !isManualMode }"
          @click="switchToAutoMode"
        >
          Auto ({{ pairs.length }} pairs)
        </button>
        <button
          :class="{ active: isManualMode }"
          @click="isManualMode = true"
        >
          Search
        </button>
      </div>

      <div v-if="currentPair || isManualMode" class="matcher-content">
        <!-- Group 1 -->
        <div class="group-card">
          <div class="group-label">Group 1</div>

          <!-- Search input for group 1 (manual mode, no selection) -->
          <div v-if="isManualMode && !selectedGroup1" class="group-search">
            <input
              v-model="search1"
              type="text"
              placeholder="Search guest name..."
              class="search-input"
              @focus="showDropdown1 = true"
              @blur="setTimeout(() => showDropdown1 = false, 200)"
            />
            <div v-if="showDropdown1 && filteredGroups1.length > 0" class="search-dropdown">
              <div
                v-for="group in filteredGroups1"
                :key="group.id"
                class="search-result"
                @mousedown="selectGroup1(group)"
              >
                <span class="result-names">{{ getGroupDisplay(group.guestNames) }}</span>
                <span class="result-size">{{ group.size }}</span>
              </div>
            </div>
            <div v-if="showDropdown1 && search1 && filteredGroups1.length === 0" class="search-dropdown">
              <div class="search-no-results">No groups found</div>
            </div>
          </div>

          <!-- Selected group display (manual mode) -->
          <template v-else-if="isManualMode && selectedGroup1">
            <div class="group-names">
              {{ getGroupDisplay(selectedGroup1.guestNames) }}
            </div>
            <div class="group-meta">
              <div class="group-size-badge">{{ selectedGroup1.size }} people</div>
              <button @click="clearGroup1" class="clear-btn">Change</button>
            </div>
          </template>

          <!-- Auto mode display -->
          <template v-else-if="currentPair">
            <div class="group-names">
              {{ getGroupDisplay(currentPair[0].guestNames) }}
            </div>
            <div class="group-meta">
              <div class="group-size-badge">{{ currentPair[0].size }} people</div>
            </div>
          </template>
        </div>

        <div class="vs-divider">
          <span class="vs-text">with</span>
        </div>

        <!-- Group 2 -->
        <div class="group-card">
          <div class="group-label">Group 2</div>

          <!-- Search input for group 2 (manual mode, no selection) -->
          <div v-if="isManualMode && !selectedGroup2" class="group-search">
            <input
              v-model="search2"
              type="text"
              placeholder="Search guest name..."
              class="search-input"
              @focus="showDropdown2 = true"
              @blur="setTimeout(() => showDropdown2 = false, 200)"
            />
            <div v-if="showDropdown2 && filteredGroups2.length > 0" class="search-dropdown">
              <div
                v-for="group in filteredGroups2"
                :key="group.id"
                class="search-result"
                @mousedown="selectGroup2(group)"
              >
                <span class="result-names">{{ getGroupDisplay(group.guestNames) }}</span>
                <span class="result-size">{{ group.size }}</span>
              </div>
            </div>
            <div v-if="showDropdown2 && search2 && filteredGroups2.length === 0" class="search-dropdown">
              <div class="search-no-results">No groups found</div>
            </div>
          </div>

          <!-- Selected group display (manual mode) -->
          <template v-else-if="isManualMode && selectedGroup2">
            <div class="group-names">
              {{ getGroupDisplay(selectedGroup2.guestNames) }}
            </div>
            <div class="group-meta">
              <div class="group-size-badge">{{ selectedGroup2.size }} people</div>
              <button @click="clearGroup2" class="clear-btn">Change</button>
            </div>
          </template>

          <!-- Auto mode display -->
          <template v-else-if="currentPair">
            <div class="group-names">
              {{ getGroupDisplay(currentPair[1].guestNames) }}
            </div>
            <div class="group-meta">
              <div class="group-size-badge">{{ currentPair[1].size }} people</div>
            </div>
          </template>
        </div>

        <!-- Warning if constraint already exists -->
        <div v-if="hasExistingConstraint" class="constraint-warning">
          These groups already have a preference set.
        </div>
      </div>

      <div v-else class="matcher-complete">
        <div class="complete-icon">✓</div>
        <h3>All Done!</h3>
        <p>You've matched all available group pairs</p>
      </div>

      <div v-if="currentPair || isManualMode" class="matcher-actions">
        <button
          @click="handlePreference(MatchPreference.DISLIKE)"
          class="action-button dislike"
          :disabled="!currentPair || hasExistingConstraint"
          title="Keep apart (Left Arrow)"
        >
          <span class="button-icon">👎</span>
          <span class="button-label">Dislike</span>
          <span v-if="!isManualMode" class="button-hint">←</span>
        </button>

        <button
          @click="handlePreference(MatchPreference.NEUTRAL)"
          class="action-button neutral"
          :disabled="!currentPair || hasExistingConstraint"
          title="No preference (Up/Down Arrow)"
        >
          <span class="button-icon">😐</span>
          <span class="button-label">Neutral</span>
          <span v-if="!isManualMode" class="button-hint">↑↓</span>
        </button>

        <button
          @click="handlePreference(MatchPreference.LIKE)"
          class="action-button like"
          :disabled="!currentPair || hasExistingConstraint"
          title="Seat nearby (Right Arrow)"
        >
          <span class="button-icon">👍</span>
          <span class="button-label">Like</span>
          <span v-if="!isManualMode" class="button-hint">→</span>
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

.matcher-progress-manual {
  padding: var(--spacing-md) var(--spacing-xl);
  text-align: center;
}

.matcher-progress-manual .progress-text {
  font-size: 1rem;
  color: var(--burgundy);
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

/* Mode toggle */
.mode-toggle {
  display: flex;
  gap: 2px;
  padding: var(--spacing-sm) var(--spacing-xl);
  background: var(--parchment-dark);
}

.mode-toggle button {
  flex: 1;
  padding: var(--spacing-sm) var(--spacing-md);
  font-size: 0.85rem;
  background: transparent;
  border: none;
  color: var(--faded-text);
  border-radius: 4px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.mode-toggle button:hover {
  background: var(--parchment-medium);
  color: var(--brown-text);
}

.mode-toggle button.active {
  background: var(--parchment-light);
  color: var(--burgundy);
  font-weight: 600;
  box-shadow: 0 2px 4px var(--shadow-brown);
}

/* Group search */
.group-search {
  position: relative;
}

.search-input {
  width: 100%;
  padding: var(--spacing-sm) var(--spacing-md);
  font-family: var(--font-body);
  font-size: 1rem;
  border: 2px solid var(--parchment-dark);
  border-radius: 6px;
  background: white;
  color: var(--ink-black);
  transition: border-color var(--transition-fast);
}

.search-input:focus {
  outline: none;
  border-color: var(--gold);
  box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.2);
}

.search-input::placeholder {
  color: var(--faded-text);
}

.search-dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  background: white;
  border: 2px solid var(--ornate-border);
  border-top: none;
  border-radius: 0 0 6px 6px;
  box-shadow: 0 4px 12px var(--shadow-brown);
  z-index: 10;
  max-height: 200px;
  overflow-y: auto;
}

.search-result {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: var(--spacing-sm) var(--spacing-md);
  cursor: pointer;
  transition: background var(--transition-fast);
}

.search-result:hover {
  background: var(--parchment-light);
}

.result-names {
  font-family: var(--font-body);
  font-size: 0.9rem;
  color: var(--ink-black);
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.result-size {
  font-family: var(--font-elegant);
  font-size: 0.75rem;
  color: var(--parchment-light);
  background: var(--burgundy);
  padding: 2px 8px;
  border-radius: 10px;
  margin-left: var(--spacing-sm);
}

.search-no-results {
  padding: var(--spacing-md);
  text-align: center;
  color: var(--faded-text);
  font-style: italic;
}

/* Group meta with change button */
.group-meta {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
}

.clear-btn {
  padding: var(--spacing-xs) var(--spacing-sm);
  font-size: 0.75rem;
  background: transparent;
  border: 1px solid var(--faded-text);
  color: var(--faded-text);
  border-radius: 4px;
}

.clear-btn:hover {
  border-color: var(--burgundy);
  color: var(--burgundy);
}

/* Constraint warning */
.constraint-warning {
  text-align: center;
  padding: var(--spacing-sm);
  background: rgba(139, 26, 26, 0.1);
  border: 1px solid var(--deep-red);
  border-radius: 4px;
  color: var(--deep-red);
  font-family: var(--font-body);
  font-size: 0.85rem;
}

/* Disabled action buttons */
.action-button:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.action-button:disabled:hover {
  background: linear-gradient(to bottom, var(--parchment-light), var(--parchment-medium));
  color: var(--brown-text);
}
</style>
