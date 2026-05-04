<template>
  <div class="feedback-history">
    <div v-if="loading" class="flex items-center justify-center py-8">
      <span class="w-5 h-5 border-2 border-primary border-t-transparent rounded-full animate-spin"></span>
      <span class="ml-2 text-sm text-on-surface-variant">加载中...</span>
    </div>
    <div v-else-if="feedbackList.length === 0" class="py-8 text-center">
      <span class="material-symbols-outlined text-3xl text-outline/30 mb-2">stop_circle</span>
      <p class="text-sm text-on-surface-variant">暂无终止记录</p>
    </div>
    <div v-else class="space-y-3">
      <div
        v-for="item in feedbackList"
        :key="item.id"
        class="p-4 bg-surface-container-low rounded-xl border border-outline-variant/10"
      >
        <div class="flex items-center justify-between mb-2">
          <div class="flex items-center gap-2">
            <span class="material-symbols-outlined text-sm text-red-600">stop_circle</span>
            <span class="text-xs font-bold text-red-600">终止执行</span>
          </div>
          <span class="text-[10px] text-outline">{{ formatTime(item.created_at) }}</span>
        </div>
        <p v-if="item.content" class="text-sm text-on-surface/80">{{ item.content }}</p>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  feedbackList: { type: Array, default: () => [] },
  loading: { type: Boolean, default: false },
})

const formatTime = (ts) => {
  if (!ts) return ''
  try { return new Date(ts).toLocaleString('zh-CN') } catch { return ts }
}
</script>
