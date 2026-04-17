<template>
  <div v-if="visible" class="fixed inset-0 z-50 flex items-center justify-center p-4">
    <div class="absolute inset-0 bg-black/50 backdrop-blur-sm" @click="handleClose"></div>
    <div class="relative bg-surface rounded-2xl shadow-2xl max-w-lg w-full p-6 md:p-8 animate-in fade-in zoom-in duration-200">
      <div class="flex items-center gap-3 mb-4">
        <div class="w-12 h-12 bg-primary-container rounded-xl flex items-center justify-center">
          <span class="material-symbols-outlined text-primary text-2xl">psychology</span>
        </div>
        <div>
          <h3 class="text-xl font-bold text-on-surface">ReAct 多步推理模式</h3>
          <p class="text-sm text-on-surface-variant">已启用</p>
        </div>
      </div>
      
      <div class="space-y-4 mb-6">
        <div class="bg-surface-container-low rounded-xl p-4">
          <h4 class="font-semibold text-on-surface mb-2 flex items-center gap-2">
            <span class="material-symbols-outlined text-primary text-base">info</span>
            什么是 ReAct 模式？
          </h4>
          <p class="text-sm text-on-surface-variant leading-relaxed">
            ReAct（Reasoning and Acting）模式让 AI 能够像人类一样思考：
            先分析问题 → 决定使用什么工具 → 执行工具获取信息 → 基于结果继续推理，直到得出最终答案。
          </p>
        </div>
        
        <div class="grid grid-cols-1 sm:grid-cols-3 gap-3">
          <div class="bg-surface-container rounded-lg p-3 text-center">
            <span class="material-symbols-outlined text-primary mb-1">lightbulb</span>
            <p class="text-xs font-medium text-on-surface">思考</p>
          </div>
          <div class="bg-surface-container rounded-lg p-3 text-center">
            <span class="material-symbols-outlined text-primary mb-1">build</span>
            <p class="text-xs font-medium text-on-surface">行动</p>
          </div>
          <div class="bg-surface-container rounded-lg p-3 text-center">
            <span class="material-symbols-outlined text-primary mb-1">visibility</span>
            <p class="text-xs font-medium text-on-surface">观察</p>
          </div>
        </div>
      </div>
      
      <div class="flex items-center gap-3">
        <label class="flex items-center gap-2 cursor-pointer flex-1">
          <input 
            type="checkbox" 
            v-model="dontShowAgain" 
            class="w-4 h-4 rounded border-outline text-primary focus:ring-primary"
          />
          <span class="text-sm text-on-surface-variant">不再显示此提示</span>
        </label>
      </div>
      
      <div class="flex gap-3 mt-6">
        <button 
          @click="handleClose"
          class="flex-1 py-3 bg-surface-container-high text-on-surface rounded-xl font-semibold hover:bg-surface-container transition-colors"
        >
          知道了
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close'])

const dontShowAgain = ref(false)

const handleClose = () => {
  if (dontShowAgain.value) {
    localStorage.setItem('react_prompt_dismissed', 'true')
  }
  emit('close')
}

const checkShouldShow = () => {
  return localStorage.getItem('react_prompt_dismissed') !== 'true'
}

defineExpose({
  checkShouldShow
})
</script>

<style scoped>
@keyframes fade-in {
  from { opacity: 0; }
  to { opacity: 1; }
}

@keyframes zoom-in {
  from { transform: scale(0.95); }
  to { transform: scale(1); }
}

.animate-in {
  animation: fade-in 0.2s ease-out, zoom-in 0.2s ease-out;
}
</style>
