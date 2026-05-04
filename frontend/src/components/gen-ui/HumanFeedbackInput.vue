<template>
  <div class="terminate-button">
    <button
      @click="handleTerminate"
      class="px-4 py-2 bg-error text-white rounded-lg text-sm font-bold hover:bg-error/90 transition-colors flex items-center gap-2"
    >
      <span class="material-symbols-outlined text-sm">stop_circle</span>
      终止执行
    </button>
  </div>
</template>

<script setup>
const props = defineProps({
  sessionId: { type: String, default: '' },
})

const emit = defineEmits(['submit'])

const handleTerminate = () => {
  const feedbackData = {
    session_id: props.sessionId,
    feedback_type: 'execution_termination',
    content: '用户终止执行'
  }
  emit('submit', feedbackData)
}
</script>
