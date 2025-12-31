import { ref, computed, watch } from 'vue'
import { useTablePlannerStore } from '../stores/tablePlanner'

const ONBOARDING_STORAGE_KEY = 'wedding-planner-onboarding'

export enum OnboardingStep {
  IMPORT_GUESTS = 'import',
  ADD_TABLES = 'tables',
  SET_PREFERENCES = 'preferences',
  COMPLETE = 'complete',
}

interface OnboardingState {
  currentStep: OnboardingStep
  isActive: boolean
  completedAt: number | null
  hasSeenCSVHelper: boolean
}

function loadOnboardingState(): OnboardingState {
  try {
    const stored = localStorage.getItem(ONBOARDING_STORAGE_KEY)
    if (stored) {
      return JSON.parse(stored)
    }
  } catch (error) {
    console.error('Failed to load onboarding state:', error)
  }
  return {
    currentStep: OnboardingStep.IMPORT_GUESTS,
    isActive: true,
    completedAt: null,
    hasSeenCSVHelper: false,
  }
}

function saveOnboardingState(state: OnboardingState): void {
  try {
    localStorage.setItem(ONBOARDING_STORAGE_KEY, JSON.stringify(state))
  } catch (error) {
    console.error('Failed to save onboarding state:', error)
  }
}

// Singleton state for the composable
const state = ref<OnboardingState>(loadOnboardingState())

// Track if CSV helper modal is currently open
const showCSVHelper = ref(false)

export function useOnboarding() {
  const store = useTablePlannerStore()

  const currentStep = computed(() => state.value.currentStep)
  const isActive = computed(() => state.value.isActive)

  // Step descriptions and hints
  const stepInfo = computed(() => {
    switch (state.value.currentStep) {
      case OnboardingStep.IMPORT_GUESTS:
        return {
          number: 1,
          total: 3,
          title: 'Import Your Guest List',
          description: 'Start by importing a CSV file with your guests. Each row represents a group that must sit together.',
          hint: 'Format: Each line = one group. Names separated by commas.',
          example: 'Alice, Bob\nCarol\nDave, Eve, Frank',
          targetSelector: '.import-button',
        }
      case OnboardingStep.ADD_TABLES:
        return {
          number: 2,
          total: 3,
          title: 'Add Your Tables',
          description: `Add tables to seat your ${store.totalGuestCount} guests.`,
          hint: 'Click to add tables, then drag them to arrange your layout.',
          targetSelector: '.add-table-button',
          // Progress tracking for this step
          showProgress: true,
          currentSeats: totalSeats.value,
          requiredSeats: store.totalGuestCount,
          canContinue: hasEnoughTables.value,
          continueLabel: 'Continue to Preferences',
          skipLabel: 'Skip to Preferences',
        }
      case OnboardingStep.SET_PREFERENCES:
        return {
          number: 3,
          total: 3,
          title: 'Set Seating Preferences',
          description: 'Optional: Tell us which groups should sit together or apart.',
          hint: 'Like = sit nearby, Dislike = keep apart, Skip = no preference.',
          targetSelector: '.match-button',
          isOptional: true,
        }
      case OnboardingStep.COMPLETE:
        return {
          number: 3,
          total: 3,
          title: 'All Set!',
          description: 'Your seating plan is ready. You can download it as a PDF.',
          targetSelector: '.download-button',
        }
    }
  })

  // Calculate suggested table count
  const suggestedTableCount = computed(() => {
    const avgSeatsPerTable = 8
    return Math.max(1, Math.ceil(store.totalGuestCount / avgSeatsPerTable))
  })

  // Calculate total seats across all tables
  const totalSeats = computed(() => {
    return store.tables.reduce((sum, t) => sum + t.seatCount, 0)
  })

  // Check if we have enough tables
  const hasEnoughTables = computed(() => {
    return totalSeats.value >= store.totalGuestCount
  })

  // Should show CSV helper modal (first time on step 1)
  const shouldShowCSVHelper = computed(() => {
    return state.value.isActive &&
           state.value.currentStep === OnboardingStep.IMPORT_GUESTS &&
           !state.value.hasSeenCSVHelper
  })

  // Watch store changes to auto-advance steps
  // Auto-advance from Import to Add Tables when guests are imported
  watch(
    () => store.groups.length,
    (count, oldCount) => {
      if (count > 0 && oldCount === 0 && state.value.currentStep === OnboardingStep.IMPORT_GUESTS) {
        advanceStep(OnboardingStep.ADD_TABLES)
      }
    }
  )

  // NOTE: We do NOT auto-advance from Add Tables to Set Preferences
  // User must manually click "Continue" when they have enough seats

  // Watch for constraints being added (user engaged with preferences)
  watch(
    () => store.constraints.filter(c => c.type !== 'SAME_TABLE').length,
    (count, oldCount) => {
      if (count > oldCount && state.value.currentStep === OnboardingStep.SET_PREFERENCES) {
        // User has set at least one preference, can mark as complete
        advanceStep(OnboardingStep.COMPLETE)
      }
    }
  )

  function advanceStep(step: OnboardingStep): void {
    state.value.currentStep = step
    if (step === OnboardingStep.COMPLETE) {
      state.value.completedAt = Date.now()
    }
    saveOnboardingState(state.value)
  }

  function skipStep(): void {
    switch (state.value.currentStep) {
      case OnboardingStep.ADD_TABLES:
        advanceStep(OnboardingStep.SET_PREFERENCES)
        break
      case OnboardingStep.SET_PREFERENCES:
        advanceStep(OnboardingStep.COMPLETE)
        break
      default:
        // Can't skip required steps
        break
    }
  }

  function continueToNextStep(): void {
    switch (state.value.currentStep) {
      case OnboardingStep.ADD_TABLES:
        advanceStep(OnboardingStep.SET_PREFERENCES)
        break
      case OnboardingStep.SET_PREFERENCES:
        advanceStep(OnboardingStep.COMPLETE)
        break
      default:
        break
    }
  }

  function skipOnboarding(): void {
    state.value.isActive = false
    state.value.completedAt = Date.now()
    saveOnboardingState(state.value)
  }

  function dismissOnboarding(): void {
    state.value.isActive = false
    saveOnboardingState(state.value)
  }

  function openCSVHelper(): void {
    showCSVHelper.value = true
  }

  function closeCSVHelper(): void {
    showCSVHelper.value = false
    state.value.hasSeenCSVHelper = true
    saveOnboardingState(state.value)
  }

  function completeOnboarding(): void {
    state.value.isActive = false
    state.value.completedAt = Date.now()
    state.value.currentStep = OnboardingStep.COMPLETE
    showCSVHelper.value = false
    saveOnboardingState(state.value)
  }

  function restart(): void {
    state.value = {
      currentStep: OnboardingStep.IMPORT_GUESTS,
      isActive: true,
      completedAt: null,
      hasSeenCSVHelper: false,
    }
    showCSVHelper.value = false
    saveOnboardingState(state.value)
  }

  // Determine initial step based on existing data
  function initializeStep(): void {
    // If onboarding was completed, don't restart
    if (state.value.completedAt && !state.value.isActive) {
      return
    }

    // Auto-detect current state and set appropriate step
    if (store.groups.length === 0) {
      state.value.currentStep = OnboardingStep.IMPORT_GUESTS
    } else if (store.tables.length === 0) {
      state.value.currentStep = OnboardingStep.ADD_TABLES
    } else {
      // User has data, mark onboarding as inactive
      state.value.isActive = false
    }
    saveOnboardingState(state.value)
  }

  // Initialize on first use
  initializeStep()

  return {
    currentStep,
    isActive,
    stepInfo,
    suggestedTableCount,
    totalSeats,
    hasEnoughTables,
    shouldShowCSVHelper,
    showCSVHelper,
    advanceStep,
    skipStep,
    continueToNextStep,
    skipOnboarding,
    dismissOnboarding,
    openCSVHelper,
    closeCSVHelper,
    completeOnboarding,
    restart,
    OnboardingStep,
  }
}
