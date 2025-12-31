<script setup lang="ts">
import { ref, onMounted } from 'vue'

interface Props {
  modelValue: number
  min?: number
  max?: number
}

const props = withDefaults(defineProps<Props>(), {
  min: 2,
  max: 20,
})

const emit = defineEmits<{
  'update:modelValue': [value: number]
}>()

const inputRef = ref<HTMLInputElement>()
const localValue = ref(props.modelValue)

onMounted(() => {
  inputRef.value?.focus()
  inputRef.value?.select()
})

function handleInput(event: Event) {
  const target = event.target as HTMLInputElement
  const value = parseInt(target.value, 10)

  if (!isNaN(value)) {
    localValue.value = value
  }
}

function handleBlur() {
  // Validate and emit the final value
  const clampedValue = Math.max(props.min, Math.min(props.max, localValue.value))
  emit('update:modelValue', clampedValue)
}

function handleKeydown(event: KeyboardEvent) {
  if (event.key === 'Enter') {
    inputRef.value?.blur()
  } else if (event.key === 'Escape') {
    // Reset to original value and blur
    localValue.value = props.modelValue
    inputRef.value?.blur()
  }
}
</script>

<template>
  <input
    ref="inputRef"
    type="number"
    :value="localValue"
    :min="min"
    :max="max"
    @input="handleInput"
    @blur="handleBlur"
    @keydown="handleKeydown"
    class="seat-count-editor"
  />
</template>

<style scoped>
.seat-count-editor {
  font-size: 1.5rem;
  width: 70px;
  background: var(--parchment-light);
  border: 2px solid var(--gold);
  box-shadow:
    0 0 0 3px rgba(212, 175, 55, 0.3),
    inset 0 1px 3px var(--shadow-brown);
}
</style>
