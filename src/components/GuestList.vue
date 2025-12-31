<script setup lang="ts">
import { computed } from 'vue'
import { useTablePlannerStore } from '../stores/tablePlanner'

const store = useTablePlannerStore()

const sortedGroups = computed(() => {
  return [...store.groups].sort((a, b) => {
    const nameA = a.guestNames[0]?.toLowerCase() || ''
    const nameB = b.guestNames[0]?.toLowerCase() || ''
    return nameA.localeCompare(nameB)
  })
})

const groupsByTable = computed(() => {
  const grouped: Record<string, typeof sortedGroups.value> = {}

  sortedGroups.value.forEach(group => {
    const key = group.tableId || 'unassigned'
    if (!grouped[key]) {
      grouped[key] = []
    }
    grouped[key].push(group)
  })

  return grouped
})

function handleGroupClick(groupId: string) {
  store.highlightGroup(groupId)
}

function getTableLabel(tableId: string): string {
  const table = store.tables.find(t => t.id === tableId)
  const tableIndex = store.tables.findIndex(t => t.id === tableId)
  return table ? `Table ${tableIndex + 1}` : 'Unknown'
}

function getGroupInitials(guestNames: string[]): string {
  if (guestNames.length === 0) return '??'
  const firstName = guestNames[0]
  const nameParts = firstName.trim().split(/\s+/)
  return nameParts.length >= 2
    ? `${nameParts[0].charAt(0)}${nameParts[nameParts.length - 1].charAt(0)}`.toUpperCase()
    : firstName.substring(0, 2).toUpperCase()
}
</script>

<template>
  <div class="guest-list">
    <div class="guest-list-header">
      <h2><span class="drop-cap">G</span>uests</h2>
      <div class="guest-count">
        {{ store.totalGuestCount }} total
      </div>
    </div>

    <div v-if="store.groups.length === 0" class="empty-state">
      <p>No guests yet</p>
      <p class="hint">Import a CSV file to get started</p>
    </div>

    <div v-else class="guest-groups">
      <!-- Unassigned groups first -->
      <div v-if="groupsByTable.unassigned" class="guest-group">
        <h3 class="group-title unassigned">
          Unassigned ({{ groupsByTable.unassigned.reduce((sum, g) => sum + g.size, 0) }})
        </h3>
        <div class="group-items">
          <div
            v-for="group in groupsByTable.unassigned"
            :key="group.id"
            class="group-item"
            :class="{ highlighted: group.id === store.highlightedGroupId }"
            @click="handleGroupClick(group.id)"
          >
            <div class="group-badge">
              <div class="group-initials">
                {{ getGroupInitials(group.guestNames) }}
              </div>
              <div class="group-size">{{ group.size }}</div>
            </div>
            <div class="group-info">
              <div class="group-names">
                {{ group.guestNames.join(', ') }}
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Groups by table -->
      <div
        v-for="(groups, tableId) in groupsByTable"
        :key="tableId"
        class="guest-group"
      >
        <template v-if="tableId !== 'unassigned'">
          <h3 class="group-title">
            {{ getTableLabel(tableId) }} ({{ groups.reduce((sum, g) => sum + g.size, 0) }})
          </h3>
          <div class="group-items">
            <div
              v-for="group in groups"
              :key="group.id"
              class="group-item"
              :class="{ highlighted: group.id === store.highlightedGroupId }"
              @click="handleGroupClick(group.id)"
            >
              <div class="group-badge">
                <div class="group-initials">
                  {{ getGroupInitials(group.guestNames) }}
                </div>
                <div class="group-size">{{ group.size }}</div>
              </div>
              <div class="group-info">
                <div class="group-names">
                  {{ group.guestNames.join(', ') }}
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

.group-items {
  display: flex;
  flex-direction: column;
  gap: var(--spacing-xs);
}

.group-item {
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

.group-item:hover {
  border-color: var(--gold);
  background: var(--parchment-light);
  transform: translateX(4px);
}

.group-item.highlighted {
  border-color: var(--gold);
  background: var(--parchment-light);
  box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.3);
}

.group-badge {
  position: relative;
  flex-shrink: 0;
}

.group-initials {
  width: 38px;
  height: 38px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--burgundy), var(--deep-red));
  color: var(--parchment-light);
  display: flex;
  align-items: center;
  justify-content: center;
  font-family: var(--font-elegant);
  font-size: 0.95rem;
  font-weight: 600;
}

.group-size {
  position: absolute;
  bottom: -4px;
  right: -4px;
  width: 18px;
  height: 18px;
  border-radius: 50%;
  background: var(--gold);
  color: var(--ink-black);
  font-family: var(--font-elegant);
  font-size: 0.7rem;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid white;
}

.group-info {
  flex: 1;
  min-width: 0;
}

.group-names {
  font-family: var(--font-body);
  font-weight: 600;
  color: var(--ink-black);
  font-size: 0.9rem;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}
</style>
