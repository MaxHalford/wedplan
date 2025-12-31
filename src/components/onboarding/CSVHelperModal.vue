<script setup lang="ts">
import { ref, computed } from 'vue'

const emit = defineEmits<{
  close: []
  skipAll: []
}>()

const isClosing = ref(false)

// Example CSV data for preview
const exampleRows = [
  { content: 'Alice, Bob', names: ['Alice', 'Bob'] },
  { content: 'Carol', names: ['Carol'] },
  { content: 'Dave, Eve, Frank', names: ['Dave', 'Eve', 'Frank'] },
]

function formatRowContent(content: string) {
  // Highlight commas
  return content.replace(/,/g, '<span class="comma">,</span>')
}

function formatGroupLabel(names: string[]) {
  if (names.length === 1) return names[0]
  if (names.length === 2) return `${names[0]} & ${names[1]}`
  return `${names.slice(0, -1).join(', ')} & ${names[names.length - 1]}`
}

function handleClose() {
  isClosing.value = true
  setTimeout(() => {
    emit('close')
  }, 200)
}

function handleSkipAll() {
  isClosing.value = true
  setTimeout(() => {
    emit('skipAll')
  }, 200)
}

function downloadTemplate() {
  const csvContent = `John Smith, Jane Smith
Michael Johnson
Sarah Williams, Tom Williams, Emma Williams
David Brown
Lisa Davis, Mark Davis`

  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  link.href = URL.createObjectURL(blob)
  link.download = 'guest-list-template.csv'
  link.click()
  URL.revokeObjectURL(link.href)
}
</script>

<template>
  <div class="csv-helper-modal" :class="{ closing: isClosing }">
    <div class="csv-modal-header">
      <h2>How to Format Your Guest List</h2>
      <button @click="handleSkipAll" class="csv-modal-close csv-modal-close-prominent" aria-label="Skip tutorial">
        &times;
      </button>
    </div>

    <div class="csv-modal-content">
      <p class="csv-instruction">
        Each row in your CSV represents a <strong>group of guests</strong> who must sit together at the same table.
      </p>

      <div class="csv-preview">
        <p class="csv-preview-title">Example CSV File</p>
        <div
          v-for="(row, index) in exampleRows"
          :key="index"
          class="csv-row"
        >
          <span class="csv-row-number">{{ index + 1 }}</span>
          <span class="csv-row-content" v-html="formatRowContent(row.content)"></span>
          <span class="csv-row-arrow">-></span>
          <span class="csv-row-group">{{ formatGroupLabel(row.names) }}</span>
        </div>
      </div>

      <p class="csv-instruction">
        Names in the same row will be seated together. Create a new row for each separate group.
      </p>
    </div>

    <div class="csv-modal-actions">
      <button @click="downloadTemplate" class="csv-btn-secondary">
        Download Template
      </button>
      <button @click="handleClose" class="csv-btn-primary">
        Got It, Let's Start!
      </button>
    </div>
  </div>
</template>

<style scoped>
/* Styles are in onboarding.css, this is just for scoping any overrides */
</style>
