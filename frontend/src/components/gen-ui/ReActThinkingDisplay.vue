<template>
  <div class="react-thinking-display bg-white rounded-2xl p-5 border border-outline-variant/15 shadow-sm">
    <!-- Header -->
    <div class="flex items-center justify-between mb-4">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-lg bg-primary/10 flex items-center justify-center">
          <span class="material-symbols-outlined text-primary text-lg">psychology</span>
        </div>
        <div>
          <h4 class="font-bold text-on-surface text-sm leading-tight">ReAct 推理链</h4>
          <p class="text-xs text-on-surface-variant">
            {{ isRunning ? `执行中 · ${steps.length} 步` : `共 ${steps.length} 步` }}
          </p>
        </div>
        <span v-if="isRunning" class="ml-1 flex items-center gap-1 px-2 py-0.5 rounded-full bg-primary/10 text-primary text-[10px] font-bold">
          <span class="w-1.5 h-1.5 bg-primary rounded-full animate-pulse"></span>
          LIVE
        </span>
      </div>
      <button
        @click="collapsed = !collapsed"
        class="p-1.5 hover:bg-surface-container rounded-lg transition-colors"
      >
        <span class="material-symbols-outlined text-on-surface-variant text-lg">
          {{ collapsed ? 'expand_more' : 'expand_less' }}
        </span>
      </button>
    </div>

    <!-- Steps timeline -->
    <div v-if="!collapsed" class="relative">
      <!-- Empty state -->
      <div v-if="steps.length === 0 && !isRunning" class="py-6 text-center">
        <span class="material-symbols-outlined text-3xl text-outline/30 mb-2">psychology_alt</span>
        <p class="text-sm text-on-surface-variant">暂无推理记录</p>
      </div>
      <div v-else-if="steps.length === 0 && isRunning" class="py-6 flex items-center justify-center gap-2">
        <span class="w-4 h-4 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
        <span class="text-sm text-on-surface-variant">等待推理开始...</span>
      </div>

      <!-- Step list with connecting line -->
      <div v-else class="relative pl-7">
        <!-- Continuous vertical timeline line -->
        <div class="absolute left-[14px] top-2 bottom-2 w-0.5 bg-outline-variant/15 rounded-full"></div>

        <div
          v-for="(step, index) in displayedSteps"
          :key="index"
          class="relative mb-3 last:mb-0"
        >
          <!-- Step dot on timeline -->
          <div
            class="absolute -left-[22px] top-2 z-10 w-3.5 h-3.5 rounded-full border-2 border-white shadow-sm transition-all duration-300"
            :class="getStepDotClass(step)"
          >
            <div v-if="step.active" class="absolute inset-0 rounded-full animate-ping opacity-50" :class="getStepDotBg(step)"></div>
          </div>

          <!-- Step card -->
          <div
            class="rounded-xl border transition-all duration-300"
            :class="[
              step.active
                ? 'shadow-sm border-opacity-50'
                : 'border-outline-variant/10',
              getStepCardBorder(step),
              getStepCardBg(step),
            ]"
          >
            <!-- Step header bar -->
            <div class="flex items-center justify-between px-3.5 py-2.5">
              <div class="flex items-center gap-2">
                <span class="material-symbols-outlined text-sm" :class="getStepIconColor(step)">
                  {{ getStepIcon(step) }}
                </span>
                <span class="text-xs font-bold uppercase tracking-wider" :class="getStepLabelColor(step)">
                  {{ step.type === 'final_answer' ? '最终答案' : getStepLabel(step) }}
                </span>
                <span class="text-[10px] text-outline/60">{{ step.timestamp }}</span>
              </div>
              <button
                v-if="stepHasExpandableContent(step)"
                @click="toggleStepExpand(index)"
                class="p-1 hover:bg-surface-container/50 rounded-md transition-colors"
              >
                <span class="material-symbols-outlined text-xs text-outline">
                  {{ expandedSteps.has(index) ? 'expand_less' : 'expand_more' }}
                </span>
              </button>
            </div>

            <!-- Step body -->
            <div v-if="expandedSteps.has(index) || step.active || !stepHasExpandableContent(step)" class="px-3.5 pb-3.5 pt-0">
              <!-- Reasoning content (DeepSeek thinking) -->
              <div
                v-if="step.type === 'thought' && step.reasoning"
                class="mb-2.5 rounded-lg bg-amber-50/70 border border-amber-200/30 p-3"
              >
                <div class="flex items-center gap-1.5 mb-1.5">
                  <span class="material-symbols-outlined text-amber-600 text-xs">psychology</span>
                  <span class="text-[10px] font-bold text-amber-700 uppercase tracking-wide">推理过程</span>
                </div>
                <p class="text-xs text-amber-900/70 whitespace-pre-wrap leading-relaxed">
                  {{ step.reasoning }}
                </p>
              </div>

              <!-- Thought content -->
              <div v-if="step.type === 'thought'" class="text-sm text-on-surface/80 leading-relaxed">
                <span v-if="step.active" class="inline-block w-1.5 h-3.5 bg-primary rounded-sm animate-pulse mr-1 align-middle"></span>
                {{ step.content }}
              </div>

              <!-- Action content -->
              <template v-else-if="step.type === 'action'">
                <div class="flex items-center gap-2 mb-2">
                  <span class="px-2 py-0.5 rounded-md bg-tertiary/10 text-tertiary text-xs font-bold font-mono">
                    {{ step.name }}
                  </span>
                </div>
                <div v-if="step.input && Object.keys(step.input).length > 0" class="rounded-lg bg-surface-container/50 p-2.5">
                  <JsonDisplay
                    v-if="step.hasJson"
                    :value="step.input"
                    :default-expand-level="1"
                  />
                  <code v-else class="text-xs text-on-surface-variant break-all">{{ formatInput(step.input) }}</code>
                </div>
                <p v-else class="text-xs text-on-surface-variant/60 italic">无参数</p>
              </template>

              <!-- Observation content -->
              <template v-else-if="step.type === 'observation'">
                <template v-if="step.hasJson">
                  <JsonDisplay
                    :value="tryParseJson(step.content)"
                    :default-expand-level="1"
                  />
                </template>
                <div v-else class="text-xs text-on-surface/70 whitespace-pre-wrap leading-relaxed max-h-40 overflow-y-auto">
                  {{ step.content }}
                </div>
              </template>

              <!-- Final answer summary -->
              <template v-else-if="step.type === 'final_answer'">
                <div class="flex items-center gap-2 py-1">
                  <span class="w-1.5 h-1.5 rounded-full bg-success"></span>
                  <span class="text-sm text-on-surface font-medium">已在正文区展示完整答案</span>
                </div>
              </template>
            </div>
          </div>
        </div>

        <!-- Pulsing placeholder for next step -->
        <div v-if="isRunning" class="relative mb-0">
          <div class="absolute -left-[22px] top-2 z-10 w-3.5 h-3.5 rounded-full border-2 border-white shadow-sm bg-primary/40">
            <div class="absolute inset-0 rounded-full animate-ping opacity-60 bg-primary/30"></div>
          </div>
          <div class="rounded-xl border border-dashed border-outline-variant/20 px-3.5 py-2.5">
            <div class="flex items-center gap-2">
              <span class="w-3 h-3 border-2 border-primary/40 border-t-transparent rounded-full animate-spin"></span>
              <span class="text-xs text-on-surface-variant/60">等待下一步...</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <div v-else class="text-center py-2 text-sm text-on-surface-variant/60 cursor-pointer" @click="collapsed = false">
      已收起 — 点击查看 {{ steps.length }} 步推理链
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import JsonDisplay from './JsonDisplay.vue'

const props = defineProps({
  steps: { type: Array, default: () => [] },
  isRunning: { type: Boolean, default: false },
})

const collapsed = ref(false)
const expandedSteps = ref(new Set())

const displayedSteps = computed(() => {
  return props.steps.map((step, index) => ({
    ...step,
    expanded: step.type === 'thought' || step.type === 'action' || expandedSteps.value.has(index),
    active: index === props.steps.length - 1 && props.isRunning,
    timestamp: formatTime(step.timestamp),
    hasJson: checkHasJson(step),
  }))
})

const checkHasJson = (step) => {
  if (step.type === 'action' && step.input) {
    const t = typeof step.input
    return (t === 'object' && step.input !== null && !Array.isArray(step.input)) || Array.isArray(step.input)
  }
  if (step.type === 'observation' && step.content) {
    const c = step.content
    return (c.trim().startsWith('{') || c.trim().startsWith('[')) && (c.trim().endsWith('}') || c.trim().endsWith(']'))
  }
  return false
}

const stepHasExpandableContent = (step) => {
  if (step.type === 'observation') return step.content && step.content.length > 100
  if (step.type === 'action') return step.input && Object.keys(step.input).length > 0
  if (step.type === 'thought' && step.reasoning) return true
  return false
}

const tryParseJson = (content) => {
  try { return JSON.parse(content) } catch { return content }
}

const formatTime = (ts) => {
  if (!ts) return ''
  return new Date(ts).toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
}

const formatInput = (input) => {
  if (!input) return ''
  if (typeof input === 'string') return input
  try { return JSON.stringify(input) } catch { return String(input) }
}

const getStepDotClass = (step) => {
  const base = 'shadow-sm'
  if (step.active) return `${base} bg-primary ring-2 ring-primary/20`
  switch (step.type) {
    case 'thought': return `${base} bg-amber-400`
    case 'action': return `${base} bg-blue-400`
    case 'observation': return `${base} bg-emerald-400`
    case 'final_answer': return `${base} bg-green-500`
    default: return `${base} bg-outline/30`
  }
}

const getStepDotBg = (step) => {
  switch (step.type) {
    case 'thought': return 'bg-amber-400'
    case 'action': return 'bg-blue-400'
    case 'observation': return 'bg-emerald-400'
    default: return 'bg-primary'
  }
}

const getStepCardBorder = (step) => {
  if (step.active) return 'border-primary/40'
  switch (step.type) {
    case 'thought': return 'border-amber-200/60'
    case 'action': return 'border-blue-200/60'
    case 'observation': return 'border-emerald-200/60'
    case 'final_answer': return 'border-green-200/60'
    default: return ''
  }
}

const getStepCardBg = (step) => {
  if (step.active) return 'bg-blue-50/30'
  return 'bg-surface-container-low/30'
}

const getStepIcon = (step) => {
  switch (step.type) {
    case 'thought': return 'lightbulb'
    case 'action': return 'build'
    case 'observation': return 'visibility'
    case 'final_answer': return 'check_circle'
    default: return 'circle'
  }
}

const getStepIconColor = (step) => {
  switch (step.type) {
    case 'thought': return 'text-amber-600'
    case 'action': return 'text-blue-600'
    case 'observation': return 'text-emerald-600'
    case 'final_answer': return 'text-green-600'
    default: return 'text-outline'
  }
}

const getStepLabelColor = (step) => {
  switch (step.type) {
    case 'thought': return 'text-amber-700'
    case 'action': return 'text-blue-700'
    case 'observation': return 'text-emerald-700'
    case 'final_answer': return 'text-green-700'
    default: return 'text-on-surface-variant'
  }
}

const getStepLabel = (step) => {
  switch (step.type) {
    case 'thought': return '推理'
    case 'action': return '行动'
    case 'observation': return '观察'
    case 'final_answer': return '完成'
    default: return '步骤'
  }
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
  animation: spin 0.8s linear infinite;
}
@keyframes ping {
  0% { transform: scale(1); opacity: 0.5; }
  100% { transform: scale(2.5); opacity: 0; }
}
.animate-ping {
  animation: ping 1.5s cubic-bezier(0, 0, 0.2, 1) infinite;
}
</style>
