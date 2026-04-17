<template>
  <div class="json-display-wrapper bg-surface-container-low rounded-xl overflow-hidden border border-outline-variant/30">
    <div class="flex items-center justify-between px-4 py-2 bg-surface-container border-b border-outline-variant/20">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-primary text-base">data_object</span>
        <span class="text-xs font-semibold text-on-surface-variant">JSON</span>
      </div>
      <button 
        @click="toggleExpandAll"
        class="p-1.5 hover:bg-surface-container-high rounded-lg transition-colors"
        :title="allExpanded ? '全部收起' : '全部展开'"
      >
        <span class="material-symbols-outlined text-on-surface-variant text-base">
          {{ allExpanded ? 'unfold_less' : 'unfold_more' }}
        </span>
      </button>
    </div>
    <div class="json-display p-4 overflow-x-auto">
      <JsonNode 
        :value="parsedValue" 
        :key-name="null"
        :depth="0"
        :expand-level="expandLevel"
        @toggle="handleNodeToggle"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import JsonNode from './JsonNode.vue'

const props = defineProps({
  value: {
    type: [String, Object, Array],
    required: true
  },
  defaultExpandLevel: {
    type: Number,
    default: 2
  }
})

const emit = defineEmits(['toggle'])

const expandedNodes = ref(new Set())
const expandLevel = ref(props.defaultExpandLevel)

const parsedValue = computed(() => {
  if (typeof props.value === 'string') {
    try {
      return JSON.parse(props.value)
    } catch (e) {
      return props.value
    }
  }
  return props.value
})

const allExpanded = computed(() => {
  return expandLevel.value === Infinity
})

const toggleExpandAll = () => {
  if (allExpanded.value) {
    expandLevel.value = props.defaultExpandLevel
  } else {
    expandLevel.value = Infinity
  }
}

const handleNodeToggle = (path, isExpanded) => {
  if (isExpanded) {
    expandedNodes.value.add(path)
  } else {
    expandedNodes.value.delete(path)
  }
  emit('toggle', { path, isExpanded })
}

watch(() => props.value, () => {
  expandedNodes.value.clear()
  expandLevel.value = props.defaultExpandLevel
}, { deep: true })
</script>

<style scoped>
.json-display-wrapper {
  font-family: 'JetBrains Mono', 'Fira Code', 'Consolas', monospace;
  font-size: 13px;
  line-height: 1.6;
}

.json-display {
  min-height: 40px;
}
</style>
