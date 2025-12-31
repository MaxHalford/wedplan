<script setup lang="ts">
import { computed } from 'vue'
import { useTablePlannerStore } from '../stores/tablePlanner'

const store = useTablePlannerStore()

const sortedGuests = computed(() => {
  return [...store.guests].sort((a, b) => {
    const nameA = `${a.lastName} ${a.firstName}`.toLowerCase()
    const nameB = `${b.lastName} ${b.firstName}`.toLowerCase()
    return nameA.localeCompare(nameB)
  })
})

const guestsByTable = computed(() => {
  const grouped: Record<string, typeof sortedGuests.value> = {}

  sortedGuests.value.forEach(guest => {
    const key = guest.tableId || 'unassigned'
    if (!grouped[key]) {
      grouped[key] = []
    }
    grouped[key].push(guest)
  })

  return grouped
})

function handleGuestClick(guestId: string) {
  store.highlightGuest(guestId)
}

function getTableLabel(tableId: string): string {
  const table = store.tables.find(t => t.id === tableId)
  const tableIndex = store.tables.findIndex(t => t.id === tableId)
  return table ? `Table ${tableIndex + 1}` : 'Unknown'
}

function getGuestInitials(firstName: string, lastName: string): string {
  return `${firstName.charAt(0)}${lastName.charAt(0)}`.toUpperCase()
}
</script>

<template>
  <div class="guest-list">
    <div class="guest-list-header">
      <h2><span class="drop-cap">G</span>uests</h2>
      <div class="guest-count">
        {{ store.guests.length }} total
      </div>
    </div>

    <div v-if="store.guests.length === 0" class="empty-state">
      <p>No guests yet</p>
      <p class="hint">Import a CSV file to get started</p>
    </div>

    <div v-else class="guest-groups">
      <!-- Unassigned guests first -->
      <div v-if="guestsByTable.unassigned" class="guest-group">
        <h3 class="group-title unassigned">
          Unassigned ({{ guestsByTable.unassigned.length }})
        </h3>
        <div class="guest-items">
          <div
            v-for="guest in guestsByTable.unassigned"
            :key="guest.id"
            class="guest-item"
            :class="{ highlighted: guest.id === store.highlightedGuestId }"
            @click="handleGuestClick(guest.id)"
          >
            <div class="guest-initials">
              {{ getGuestInitials(guest.firstName, guest.lastName) }}
            </div>
            <div class="guest-info">
              <div class="guest-name">
                {{ guest.firstName }} {{ guest.lastName }}
              </div>
              <div v-if="guest.dietaryRestrictions" class="guest-dietary">
                {{ guest.dietaryRestrictions }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Guests by table -->
      <div
        v-for="(guests, tableId) in guestsByTable"
        :key="tableId"
        class="guest-group"
      >
        <template v-if="tableId !== 'unassigned'">
          <h3 class="group-title">
            {{ getTableLabel(tableId) }} ({{ guests.length }})
          </h3>
          <div class="guest-items">
            <div
              v-for="guest in guests"
              :key="guest.id"
              class="guest-item"
              :class="{ highlighted: guest.id === store.highlightedGuestId }"
              @click="handleGuestClick(guest.id)"
            >
              <div class="guest-initials">
                {{ getGuestInitials(guest.firstName, guest.lastName) }}
              </div>
              <div class="guest-info">
                <div class="guest-name">
                  {{ guest.firstName }} {{ guest.lastName }}
                </div>
                <div v-if="guest.dietaryRestrictions" class="guest-dietary">
                  {{ guest.dietaryRestrictions }}
                </div>
              </div>
            </div>
          </div>
        </template>
      </div>
    </div>
  </div>
</template>

<style scoped>
.guest-list {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--parchment-light);
  border-right: 4px double var(--ornate-border);
  box-shadow: inset -2px 0 4px rgba(139, 105, 20, 0.1);
}

.guest-list-header {
  padding: var(--spacing-lg);
  border-bottom: 3px solid var(--ornate-border);
  background:
    linear-gradient(to bottom, var(--parchment-light), var(--parchment-medium)),
    repeating-linear-gradient(
      0deg,
      transparent,
      transparent 2px,
      rgba(139, 105, 20, 0.03) 2px,
      rgba(139, 105, 20, 0.03) 4px
    );
  box-shadow: 0 2px 4px var(--shadow-brown);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.guest-list-header h2 {
  margin: 0;
  font-size: 1.75rem;
  color: var(--burgundy);
  display: flex;
  align-items: center;
  gap: 0.1em;
}

.drop-cap {
  font-family: var(--font-decorative);
  font-size: 2.5rem;
  color: var(--deep-red);
  text-shadow:
    1px 1px 0 var(--gold),
    0 0 6px rgba(212, 175, 55, 0.3);
  line-height: 1;
  font-weight: 700;
  margin-right: -0.05em;
}

.guest-count {
  font-family: var(--font-elegant);
  color: var(--faded-text);
  font-size: 0.85rem;
  background: rgba(212, 197, 170, 0.3);
  padding: var(--spacing-xs) var(--spacing-sm);
  border-radius: 3px;
  border: 1px solid var(--parchment-dark);
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: var(--spacing-xl);
  text-align: center;
}

.empty-state p {
  margin: var(--spacing-xs) 0;
  color: var(--faded-text);
}

.empty-state .hint {
  font-size: 0.9rem;
  font-style: italic;
}

.guest-groups {
  flex: 1;
  overflow-y: auto;
  padding: var(--spacing-md);
}

.guest-group {
  margin-bottom: var(--spacing-lg);
}

.group-title {
  font-family: var(--font-elegant);
  font-size: 1rem;
  font-weight: 600;
  color: var(--burgundy);
  margin: 0 0 var(--spacing-sm) 0;
  padding: var(--spacing-xs) var(--spacing-sm);
  background: linear-gradient(to right, var(--parchment-medium), var(--parchment-light));
  border-left: 4px solid var(--gold);
  border-top: 1px solid rgba(212, 175, 55, 0.2);
  border-bottom: 1px solid rgba(212, 175, 55, 0.2);
  box-shadow: 0 1px 2px rgba(139, 105, 20, 0.1);
  position: relative;
}

.group-title::before {
  content: '✦';
  position: absolute;
  left: -2px;
  top: 50%;
  transform: translateY(-50%);
  color: var(--gold);
  font-size: 0.6rem;
}

.group-title.unassigned {
  border-left-color: var(--faded-text);
  color: var(--faded-text);
}

.group-title.unassigned::before {
  color: var(--faded-text);
}

.guest-items {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.guest-item {
  display: flex;
  align-items: center;
  gap: var(--spacing-sm);
  padding: var(--spacing-sm);
  background: white;
  border: 2px solid var(--parchment-dark);
  border-radius: 4px;
  cursor: pointer;
  transition: all var(--transition-fast);
}

.guest-item:hover {
  border-color: var(--gold);
  background: var(--parchment-light);
  transform: translateX(4px);
}

.guest-item.highlighted {
  border-color: var(--gold);
  background: var(--parchment-light);
  box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.3);
}

.guest-initials {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--burgundy), var(--deep-red));
  color: var(--parchment-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-elegant);
  font-size: 0.9rem;
  font-weight: 600;
  flex-shrink: 0;
}

.guest-info {
  flex: 1;
  min-width: 0;
}

.guest-name {
  font-family: var(--font-body);
  font-weight: 600;
  color: var(--ink-black);
  font-size: 0.95rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.guest-dietary {
  font-size: 0.8rem;
  color: var(--faded-text);
  font-style: italic;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-top: 2px;
}
</style>
