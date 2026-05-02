<template>
  <div class="thinking-effort-selector relative" ref="selectorRef">
    <button
      @click="togglePanel"
      :disabled="disabled"
      class="effort-toggle-btn flex items-center gap-2 px-4 py-2 bg-surface-container-high rounded-xl shadow-sm border border-outline-variant/20 text-on-surface font-medium text-sm transition-all hover:shadow-md hover:bg-surface-container disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-sm"
    >
      <span class="material-symbols-outlined text-base">{{ currentOption.icon }}</span>
      <span>工作量 ({{ currentOption.label }})</span>
      <span class="material-symbols-outlined text-base transition-transform duration-200" :class="{ 'rotate-180': isOpen }">expand_more</span>
    </button>

    <Transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 scale-95"
      enter-to-class="opacity-100 scale-100"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 scale-100"
      leave-to-class="opacity-0 scale-95"
    >
      <div
        v-if="isOpen"
        class="absolute bottom-full left-0 mb-2 w-72 bg-surface rounded-2xl shadow-xl border border-outline-variant/10 overflow-hidden z-50"
      >
        <div class="p-2">
          <button
            v-for="option in options"
            :key="option.value"
            @click="selectOption(option.value)"
            class="effort-option w-full flex items-start gap-3 p-3 rounded-xl transition-all hover:bg-surface-container"
            :class="{ 'bg-primary/10 hover:bg-primary/15': modelValue === option.value }"
          >
            <div
              class="w-10 h-10 rounded-lg flex items-center justify-center shrink-0 transition-colors"
              :class="modelValue === option.value ? 'bg-primary text-on-primary' : 'bg-surface-container text-on-surface-variant'"
            >
              <span class="material-symbols-outlined text-xl">{{ option.icon }}</span>
            </div>
            <div class="flex-1 min-w-0 text-left">
              <p
                class="font-semibold text-sm mb-0.5 transition-colors"
                :class="modelValue === option.value ? 'text-primary' : 'text-on-surface'"
              >
                {{ option.title }}
              </p>
              <p class="text-xs text-on-surface-variant leading-relaxed">{{ option.desc }}</p>
            </div>
            <div
              v-if="modelValue === option.value"
              class="w-5 h-5 rounded-full bg-primary flex items-center justify-center shrink-0 mt-0.5"
            >
              <span class="material-symbols-outlined text-white text-sm">check</span>
            </div>
          </button>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'

const props = defineProps({
  modelValue: {
    type: String,
    default: 'high',
    validator: (value) => ['low', 'medium', 'high', 'max'].includes(value)
  },
  disabled: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['update:modelValue'])

const isOpen = ref(false)
const selectorRef = ref(null)

const options = [
  {
    value: 'low',
    icon: 'speed',
    title: '低强度',
    desc: '快速响应，适合简单问题',
    label: 'Low'
  },
  {
    value: 'medium',
    icon: 'tune',
    title: '中等',
    desc: '平衡模式',
    label: 'Medium'
  },
  {
    value: 'high',
    icon: 'psychology',
    title: '高强度',
    desc: '深度思考，适合复杂问题',
    label: 'High'
  },
  {
    value: 'max',
    icon: 'auto_awesome',
    title: '最大',
    desc: '最大思考强度，消耗更多资源',
    label: 'Max'
  }
]

const currentOption = computed(() => {
  return options.find(opt => opt.value === props.modelValue) || options[2]
})

const togglePanel = () => {
  if (!props.disabled) {
    isOpen.value = !isOpen.value
  }
}

const selectOption = (value) => {
  emit('update:modelValue', value)
  isOpen.value = false
}

const closePanel = () => {
  isOpen.value = false
}

const handleClickOutside = (event) => {
  if (selectorRef.value && !selectorRef.value.contains(event.target)) {
    closePanel()
  }
}

const handleEscapeKey = (event) => {
  if (event.key === 'Escape') {
    closePanel()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
  document.addEventListener('keydown', handleEscapeKey)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
  document.removeEventListener('keydown', handleEscapeKey)
})
</script>

<style scoped>
.thinking-effort-selector {
  user-select: none;
}

.effort-toggle-btn:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: 2px;
}

.effort-option:focus-visible {
  outline: 2px solid var(--color-primary);
  outline-offset: -2px;
}
</style>
