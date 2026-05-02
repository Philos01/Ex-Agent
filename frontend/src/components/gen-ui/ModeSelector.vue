<template>
  <div class="relative" ref="selectorRef">
    <!-- Toggle 按钮 -->
    <button
      @click="togglePanel"
      :disabled="disabled"
      :class="[
        'flex items-center gap-2 px-3 py-2 rounded-lg transition-all',
        disabled 
          ? 'bg-surface-container-high text-on-surface-variant opacity-50 cursor-not-allowed'
          : 'bg-surface-container-high text-on-surface-variant hover:bg-surface-container-high/80 active:scale-95'
      ]"
    >
      <span class="material-symbols-outlined text-base md:text-lg" style="font-variation-settings: 'FILL' 1">
        tune
      </span>
      <span class="text-xs font-semibold">模式</span>
      <span class="material-symbols-outlined text-sm transition-transform duration-200" :class="{ 'rotate-180': showPanel }">
        expand_more
      </span>
    </button>

    <!-- 弹出面板 -->
    <transition
      enter-active-class="transition ease-out duration-200"
      enter-from-class="opacity-0 scale-95 translate-y-1"
      enter-to-class="opacity-100 scale-100 translate-y-0"
      leave-active-class="transition ease-in duration-150"
      leave-from-class="opacity-100 scale-100 translate-y-0"
      leave-to-class="opacity-0 scale-95 translate-y-1"
    >
      <div
        v-if="showPanel && !disabled"
        class="absolute bottom-full left-0 mb-2 w-80 bg-surface rounded-xl shadow-2xl border border-outline-variant/20 overflow-hidden z-50"
      >
        <!-- 面板标题 -->
        <div class="px-4 py-3 border-b border-outline-variant/10 flex items-center justify-between">
          <h4 class="text-sm font-bold text-on-surface">模式设置</h4>
          <button
            @click="closePanel"
            class="p-1 hover:bg-surface-container rounded-lg transition-colors"
          >
            <span class="material-symbols-outlined text-lg text-on-surface-variant">close</span>
          </button>
        </div>

        <!-- 选项列表 -->
        <div class="p-2 space-y-1">
          <!-- 思考模式选项 -->
          <button
            @click="toggleThinkingMode"
            :class="[
              'w-full flex items-center gap-3 px-3 py-3 rounded-lg text-left transition-all',
              localEnableThinking
                ? 'bg-primary/10 text-primary hover:bg-primary/15'
                : 'hover:bg-surface-container-high text-on-surface'
            ]"
          >
            <span class="material-symbols-outlined text-xl" style="font-variation-settings: 'FILL' 1">
              {{ localEnableThinking ? 'psychology' : 'psychology_alt' }}
            </span>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold">{{ localEnableThinking ? '思考模式已启用' : '思考模式' }}</p>
              <p class="text-xs mt-0.5" :class="localEnableThinking ? 'text-primary/70' : 'text-on-surface-variant'">
                {{ localEnableThinking ? '模型将在回答前进行深度推理' : '点击启用思考模式以提升复杂问题的回答质量' }}
              </p>
            </div>
            <span v-if="localEnableThinking" class="material-symbols-outlined text-primary">check_circle</span>
          </button>

          <!-- 工作量（思考强度）选项 -->
          <div class="px-3 py-2">
            <p class="text-xs font-bold text-on-surface-variant mb-2">思考强度</p>
            <div class="grid grid-cols-2 gap-1.5">
              <button
                v-for="option in effortOptions"
                :key="option.value"
                @click="selectEffort(option.value)"
                :disabled="!localEnableThinking"
                :class="[
                  'flex items-center gap-2 px-2.5 py-2 rounded-lg text-left transition-all text-xs font-medium',
                  localReasoningEffort === option.value && localEnableThinking
                    ? 'bg-primary text-on-primary shadow-sm'
                    : !localEnableThinking
                    ? 'bg-surface-container text-on-surface-variant cursor-not-allowed opacity-50'
                    : 'bg-surface-container-high text-on-surface hover:bg-surface-container-high/80'
                ]"
              >
                <span class="material-symbols-outlined text-base" :style="localReasoningEffort === option.value && localEnableThinking ? 'font-variation-settings: \'FILL\' 1' : ''">
                  {{ option.icon }}
                </span>
                <span>{{ option.label }}</span>
              </button>
            </div>
          </div>

          <!-- 图结构检索选项 -->
          <button
            @click="toggleGraphSearch"
            :class="[
              'w-full flex items-center gap-3 px-3 py-3 rounded-lg text-left transition-all',
              localUseGraph
                ? 'bg-secondary/10 text-secondary hover:bg-secondary/15'
                : 'hover:bg-surface-container-high text-on-surface'
            ]"
          >
            <span class="material-symbols-outlined text-xl" style="font-variation-settings: 'FILL' 1">
              account_tree
            </span>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold">{{ localUseGraph ? '图结构检索已启用' : '图结构检索' }}</p>
              <p class="text-xs mt-0.5" :class="localUseGraph ? 'text-secondary/70' : 'text-on-surface-variant'">
                {{ localUseGraph ? '自动发现文档间实体关联和关系网络' : '启用后可跨文档追溯实体关系（如"用了X数据集有哪些论文"）' }}
              </p>
            </div>
            <span v-if="localUseGraph" class="material-symbols-outlined text-secondary">check_circle</span>
          </button>

          <!-- ReAct 模式选项 -->
          <button
            @click="toggleReActMode"
            :class="[
              'w-full flex items-center gap-3 px-3 py-3 rounded-lg text-left transition-all',
              localUseReAct
                ? 'bg-tertiary/10 text-tertiary hover:bg-tertiary/15'
                : 'hover:bg-surface-container-high text-on-surface'
            ]"
          >
            <span class="material-symbols-outlined text-xl" style="font-variation-settings: 'FILL' 1">
              hub
            </span>
            <div class="flex-1 min-w-0">
              <p class="text-sm font-semibold">{{ localUseReAct ? 'ReAct 多步推理已启用' : 'ReAct 多步推理' }}</p>
              <p class="text-xs mt-0.5" :class="localUseReAct ? 'text-tertiary/70' : 'text-on-surface-variant'">
                {{ localUseReAct ? '模型将使用工具进行多步推理和验证' : '启用后可调用工具进行复杂任务分解' }}
              </p>
            </div>
            <span v-if="localUseReAct" class="material-symbols-outlined text-tertiary">check_circle</span>
          </button>
        </div>

        <!-- 底部提示 -->
        <div class="px-4 py-2 bg-surface-container-lowest border-t border-outline-variant/10">
          <p class="text-[10px] text-on-surface-variant text-center">
            按 ESC 或点击外部区域关闭
          </p>
        </div>
      </div>
    </transition>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue'

const props = defineProps({
  enableThinking: { type: Boolean, default: false },
  reasoningEffort: { type: String, default: 'high' },
  useReAct: { type: Boolean, default: false },
  useGraph: { type: Boolean, default: true },
  disabled: { type: Boolean, default: false }
})

// 维护本地状态副本（解决响应式丢失问题）
const localEnableThinking = ref(props.enableThinking)
const localReasoningEffort = ref(props.reasoningEffort)
const localUseReAct = ref(props.useReAct)
const localUseGraph = ref(props.useGraph)

// 同步 props 到本地状态
watch(() => props.enableThinking, (val) => { localEnableThinking.value = val })
watch(() => props.reasoningEffort, (val) => { localReasoningEffort.value = val })
watch(() => props.useReAct, (val) => { localUseReAct.value = val })
watch(() => props.useGraph, (val) => { localUseGraph.value = val })

const emit = defineEmits([
  'update:enable-thinking',
  'update:reasoning-effort',
  'update:use-react',
  'update:use-graph',
  'show-react-prompt'
])

const showPanel = ref(false)
const selectorRef = ref(null)

const effortOptions = [
  { value: 'low', label: '低', icon: 'speed' },
  { value: 'medium', label: '中', icon: 'tune' },
  { value: 'high', label: '高', icon: 'psychology' },
  { value: 'max', label: '最大', icon: 'auto_awesome' }
]

const togglePanel = () => {
  if (!props.disabled) {
    showPanel.value = !showPanel.value
  }
}

const closePanel = () => {
  showPanel.value = false
}

const toggleThinkingMode = () => {
  const newValue = !localEnableThinking.value
  localEnableThinking.value = newValue
  emit('update:enable-thinking', newValue)
}

const selectEffort = (value) => {
  localReasoningEffort.value = value
  emit('update:reasoning-effort', value)
}

const toggleGraphSearch = () => {
  const newValue = !localUseGraph.value
  localUseGraph.value = newValue
  emit('update:use-graph', newValue)
}

const toggleReActMode = () => {
  const newValue = !localUseReAct.value
  localUseReAct.value = newValue
  emit('update:use-react', newValue)

  if (newValue) {
    emit('show-react-prompt')
  }
}

// ESC 键关闭
const handleEscape = (e) => {
  if (e.key === 'Escape' && showPanel.value) {
    closePanel()
  }
}

// 点击外部关闭
const handleClickOutside = (e) => {
  const target = e.target
  
  // 排除模态弹窗区域的点击（防止关闭 ReAct 提示弹窗时误触发表板收起）
  // 检测常见的模态弹窗特征：
  // 1. fixed 定位的全屏遮罩层（如 .fixed.inset-0）
  // 2. 包含 backdrop 类名的元素
  // 3. 包含 modal 类名的元素
  // 4. z-index 很高的绝对定位弹窗
  const isModalClick = target.closest('.fixed.inset-0') || 
                       target.closest('[class*="backdrop"]') ||
                       target.closest('[class*="modal"]') ||
                       (target.closest('.absolute') && target.closest('[class*="z-50"]'))
  
  // 如果点击的是模态弹窗区域，不关闭面板
  if (isModalClick) return
  
  // 正常的外部点击检测：点击不在 selector 内部的元素时关闭面板
  if (selectorRef.value && !selectorRef.value.contains(target)) {
    closePanel()
  }
}

onMounted(() => {
  document.addEventListener('keydown', handleEscape)
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('keydown', handleEscape)
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
/* 确保动画流畅 */
.transition-all {
  transition-property: all;
  transition-timing-function: cubic-bezier(0.4, 0, 0.2, 1);
}
</style>
