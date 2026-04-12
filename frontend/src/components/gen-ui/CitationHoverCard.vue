<template>
  <div 
    v-if="visible" 
    class="absolute z-50 bg-white rounded-xl shadow-xl border border-outline-variant/20 p-4 max-w-md"
    :style="positionStyle"
  >
    <div class="flex items-start gap-3">
      <span class="material-symbols-outlined text-primary shrink-0">description</span>
      <div class="flex-1 min-w-0">
        <p class="font-semibold text-on-surface text-sm truncate">
          {{ source?.source || source?.filename || '文档' }}
        </p>
        <p v-if="source?.text" class="text-on-surface-variant text-xs mt-1 line-clamp-4 leading-relaxed">
          {{ source.text }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  source: {
    type: Object,
    default: null
  },
  position: {
    type: Object,
    default: () => ({ x: 0, y: 0 })
  }
})

const positionStyle = computed(() => ({
  left: `${props.position.x}px`,
  top: `${props.position.y}px`,
  transform: 'translateY(8px)'
}))
</script>

<style scoped>
.line-clamp-4 {
  display: -webkit-box;
  -webkit-line-clamp: 4;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
