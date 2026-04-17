<template>
  <div class="react-thinking-display bg-surface-container-low rounded-xl p-4 border border-outline-variant/20">
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-primary">psychology_alt</span>
        <h4 class="font-bold text-on-surface text-sm">ReAct 思考过程</h4>
        <span v-if="isRunning" class="text-xs text-primary flex items-center gap-1">
          <span class="w-1.5 h-1.5 bg-primary rounded-full animate-pulse"></span>
          运行中
        </span>
      </div>
      <div class="flex items-center gap-2">
        <button 
          @click="togglePause"
          v-if="isRunning"
          class="p-2 hover:bg-surface-container rounded-lg transition-colors"
          :title="isPaused ? '继续' : '暂停'"
        >
          <span class="material-symbols-outlined text-on-surface-variant text-base">
            {{ isPaused ? 'play_arrow' : 'pause' }}
          </span>
        </button>
        <button 
          @click="toggleCollapse"
          class="p-2 hover:bg-surface-container rounded-lg transition-colors"
          :title="collapsed ? '展开' : '收起'"
        >
          <span class="material-symbols-outlined text-on-surface-variant text-base">
            {{ collapsed ? 'expand_more' : 'expand_less' }}
          </span>
        </button>
      </div>
    </div>
    
    <div v-if="!collapsed" class="space-y-3">
      <div 
        v-for="(step, index) in displayedSteps" 
        :key="index"
        class="flex items-start gap-3"
      >
        <div 
          class="step-indicator flex-shrink-0 w-7 h-7 rounded-full flex items-center justify-center mt-0.5"
          :class="getStepClass(step)"
        >
          <span v-if="step.type === 'thought'" class="material-symbols-outlined text-white text-[14px]">lightbulb</span>
          <span v-else-if="step.type === 'action'" class="material-symbols-outlined text-white text-[14px]">build</span>
          <span v-else-if="step.type === 'observation'" class="material-symbols-outlined text-white text-[14px]">visibility</span>
          <span v-else-if="step.type === 'final_answer'" class="material-symbols-outlined text-white text-[14px]">check_circle</span>
          <span v-else class="material-symbols-outlined text-white text-[14px]">circle</span>
        </div>
        
        <div class="flex-1 min-w-0">
          <div class="flex items-center gap-2 mb-1">
            <span class="text-xs font-semibold" :class="getStepLabelClass(step)">
              {{ getStepLabel(step) }}
            </span>
            <span v-if="step.timestamp" class="text-[10px] text-outline">{{ step.timestamp }}</span>
          </div>
          
          <div class="text-sm text-on-surface">
            <template v-if="step.type === 'thought'">
              {{ step.content }}
            </template>
            
            <template v-else-if="step.type === 'action'">
              <div class="flex flex-col gap-2">
                <span class="font-medium text-primary">{{ step.name }}</span>
                <template v-if="step.input">
                  <JsonDisplay 
                    v-if="step.hasJson" 
                    :value="step.input" 
                    :default-expand-level="1"
                  />
                  <span 
                    v-else
                    class="text-xs text-on-surface-variant bg-surface-container px-2 py-0.5 rounded"
                  >
                    {{ formatInput(step.input) }}
                  </span>
                </template>
              </div>
            </template>
            
            <template v-else-if="step.type === 'observation'">
              <template v-if="step.hasJson">
                <div 
                  v-if="!step.expanded"
                  class="text-on-surface-variant"
                >
                  JSON 数据
                  <button 
                    @click="toggleStepExpand(index)"
                    class="text-primary text-xs font-medium ml-1 hover:underline"
                  >
                    展开
                  </button>
                </div>
                <div v-else>
                  <JsonDisplay 
                    :value="tryParseJson(step.content)" 
                    :default-expand-level="1"
                  />
                  <button 
                    @click="toggleStepExpand(index)"
                    class="text-primary text-xs font-medium ml-1 hover:underline"
                  >
                    收起
                  </button>
                </div>
              </template>
              <template v-else>
                <div 
                  v-if="!step.expanded && step.content.length > 200"
                  class="text-on-surface-variant"
                >
                  {{ step.content.substring(0, 200) }}...
                  <button 
                    @click="toggleStepExpand(index)"
                    class="text-primary text-xs font-medium ml-1 hover:underline"
                  >
                    展开
                  </button>
                </div>
                <div v-else class="whitespace-pre-wrap">
                  {{ step.content }}
                  <button 
                    v-if="step.content.length > 200"
                    @click="toggleStepExpand(index)"
                    class="text-primary text-xs font-medium ml-1 hover:underline"
                  >
                    收起
                  </button>
                </div>
              </template>
            </template>
            
            <template v-else>
              {{ step.content }}
            </template>
          </div>
        </div>
      </div>
      
      <div v-if="steps.length === 0 && isRunning" class="py-4 text-center">
        <div class="flex items-center justify-center gap-2 text-on-surface-variant text-sm">
          <span class="material-symbols-outlined animate-spin">progress_activity</span>
          思考中...
        </div>
      </div>
      
      <div v-if="steps.length === 0 && !isRunning" class="py-4 text-center text-on-surface-variant text-sm">
        暂无思考记录
      </div>
    </div>
    
    <div v-else class="text-center py-2 text-sm text-on-surface-variant">
      已收起，点击展开查看思考过程
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import JsonDisplay from './JsonDisplay.vue'

const props = defineProps({
  steps: {
    type: Array,
    default: () => []
  },
  isRunning: {
    type: Boolean,
    default: false
  }
})

const collapsed = ref(false)
const isPaused = ref(false)
const expandedSteps = ref(new Set())

const displayedSteps = computed(() => {
  return props.steps.map((step, index) => ({
    ...step,
    expanded: expandedSteps.value.has(index),
    timestamp: formatTime(step.timestamp),
    hasJson: checkHasJson(step)
  }))
})

const checkHasJson = (step) => {
  console.log('[DEBUG] checkHasJson called for step:', step)
  if (step.type === 'action' && step.input) {
    const isObject = typeof step.input === 'object' && step.input !== null && !Array.isArray(step.input)
    const isArray = Array.isArray(step.input)
    console.log('[DEBUG] Action step - isObject:', isObject, 'isArray:', isArray, 'input:', step.input)
    return isObject || isArray
  }
  if (step.type === 'observation' && step.content) {
    const content = step.content
    const isJsonStr = (content.trim().startsWith('{') || content.trim().startsWith('[')) && 
                      (content.trim().endsWith('}') || content.trim().endsWith(']'))
    console.log('[DEBUG] Observation step - isJsonStr:', isJsonStr, 'content:', content.substring(0, 50))
    return isJsonStr
  }
  console.log('[DEBUG] No JSON for step')
  return false
}

const tryParseJson = (content) => {
  try {
    return JSON.parse(content)
  } catch {
    return content
  }
}

const formatTime = (ts) => {
  if (!ts) return ''
  const date = new Date(ts)
  return date.toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const formatInput = (input) => {
  if (!input) return ''
  if (typeof input === 'string') return input
  try {
    return JSON.stringify(input)
  } catch {
    return String(input)
  }
}

const getStepClass = (step) => {
  switch (step.type) {
    case 'thought':
      return 'bg-primary'
    case 'action':
      return 'bg-tertiary'
    case 'observation':
      return 'bg-secondary'
    case 'final_answer':
      return 'bg-success'
    default:
      return 'bg-surface-container'
  }
}

const getStepLabelClass = (step) => {
  switch (step.type) {
    case 'thought':
      return 'text-primary'
    case 'action':
      return 'text-tertiary'
    case 'observation':
      return 'text-secondary'
    case 'final_answer':
      return 'text-success'
    default:
      return 'text-on-surface-variant'
  }
}

const getStepLabel = (step) => {
  switch (step.type) {
    case 'thought':
      return '思考'
    case 'action':
      return '行动'
    case 'observation':
      return '观察'
    case 'final_answer':
      return '最终答案'
    default:
      return '步骤'
  }
}

const toggleCollapse = () => {
  collapsed.value = !collapsed.value
}

const togglePause = () => {
  isPaused.value = !isPaused.value
}

const toggleStepExpand = (index) => {
  if (expandedSteps.value.has(index)) {
    expandedSteps.value.delete(index)
  } else {
    expandedSteps.value.add(index)
  }
}
</script>

<style scoped>
@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.animate-pulse {
  animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
}

@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
