<template>
  <div class="thinking-steps bg-surface-container-low rounded-xl p-4 border border-outline-variant/20">
    <div class="flex items-center gap-2 mb-4">
      <span class="material-symbols-outlined text-primary">psychology</span>
      <h4 class="font-bold text-on-surface text-sm">思考链路</h4>
    </div>
    
    <div class="space-y-3">
      <div 
        v-for="(step, index) in steps" 
        :key="index"
        class="flex items-start gap-3"
      >
        <div 
          class="step-indicator flex-shrink-0 w-6 h-6 rounded-full flex items-center justify-center"
          :class="getStepClass(index)"
        >
          <span v-if="step.status === 'active'" class="material-symbols-outlined text-white text-[14px] animate-spin">progress_activity</span>
          <span v-else-if="step.status === 'completed'" class="material-symbols-outlined text-white text-[14px]">check</span>
          <span v-else class="material-symbols-outlined text-outline text-[14px]">circle</span>
        </div>
        
        <div class="flex-1 pt-0.5">
          <p class="text-sm" :class="getStepTextClass(index)">
            {{ step.message }}
          </p>
          
          <!-- 进度条 -->
          <div v-if="step.status === 'active' && step.progress !== undefined" class="mt-2">
            <div class="w-full h-1.5 bg-surface-container rounded-full overflow-hidden">
              <div 
                class="h-full bg-primary transition-all duration-300"
                :style="{ width: step.progress + '%' }"
              ></div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  currentState: {
    type: Object,
    default: null
  }
})

const steps = computed(() => {
  const baseSteps = [
    { phase: 'retrieving', message: '正在连接 Chroma 向量库...', status: 'pending' },
    { phase: 'retrieving', message: '检索到相关文献', status: 'pending' },
    { phase: 'analyzing', message: '正在分析检索结果...', status: 'pending' },
    { phase: 'generating', message: '正在生成回答...', status: 'pending' },
    { phase: 'done', message: '生成完毕', status: 'pending' }
  ]

  if (!props.currentState) {
    return baseSteps
  }

  const phaseOrder = ['retrieving', 'analyzing', 'generating', 'done']
  const currentPhaseIndex = phaseOrder.indexOf(props.currentState.phase)

  return baseSteps.map((step, index) => {
    let status = 'pending'
    let message = step.message
    let progress = undefined

    // 处理检索阶段（有两个步骤）
    if (step.phase === 'retrieving') {
      if (props.currentState.phase === 'retrieving') {
        if (index === 0) {
          status = 'completed'
        } else if (index === 1) {
          status = 'active'
          message = props.currentState.message
          progress = props.currentState.progress
        }
      } else if (currentPhaseIndex > phaseOrder.indexOf('retrieving')) {
        status = 'completed'
      }
    } 
    // 处理其他阶段
    else {
      const stepPhaseIndex = phaseOrder.indexOf(step.phase)
      if (props.currentState.phase === 'done') {
        // 如果是 done 阶段，所有步骤都完成
        status = 'completed'
      } else if (stepPhaseIndex < currentPhaseIndex) {
        status = 'completed'
      } else if (stepPhaseIndex === currentPhaseIndex) {
        status = 'active'
        message = props.currentState.message
        progress = props.currentState.progress
      }
    }

    return { ...step, message, status, progress }
  })
})

const getStepClass = (index) => {
  const step = steps.value[index]
  if (step.status === 'completed') {
    return 'bg-primary'
  } else if (step.status === 'active') {
    return 'bg-primary'
  }
  return 'bg-surface-container'
}

const getStepTextClass = (index) => {
  const step = steps.value[index]
  if (step.status === 'completed') {
    return 'text-on-surface'
  } else if (step.status === 'active') {
    return 'text-primary font-medium'
  }
  return 'text-outline'
}
</script>

<style scoped>
@keyframes spin {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.animate-spin {
  animation: spin 1s linear infinite;
}
</style>
