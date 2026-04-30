<template>
  <div v-if="thinkingText || isStreaming" class="deepseek-thinking-preview bg-white rounded-2xl p-5 border border-outline-variant/15 shadow-sm">
    <!-- Header -->
    <div class="flex items-center justify-between mb-3">
      <div class="flex items-center gap-2.5">
        <div class="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center">
          <span class="material-symbols-outlined text-amber-600 text-lg">psychology</span>
        </div>
        <div>
          <h4 class="font-bold text-on-surface text-sm leading-tight">思考预览</h4>
          <p class="text-xs text-on-surface-variant">
            {{ isStreaming ? '正在推理中...' : '推理完成' }}
          </p>
        </div>
        <span v-if="isStreaming" class="ml-1 flex items-center gap-1 px-2 py-0.5 rounded-full bg-amber-100 text-amber-700 text-[10px] font-bold">
          <span class="w-1.5 h-1.5 bg-amber-500 rounded-full animate-pulse"></span>
          LIVE
        </span>
      </div>
      <button @click="collapsed = !collapsed" class="p-1.5 hover:bg-surface-container rounded-lg transition-colors">
        <span class="material-symbols-outlined text-on-surface-variant text-lg">
          {{ collapsed ? 'expand_more' : 'expand_less' }}
        </span>
      </button>
    </div>

    <!-- Content -->
    <div v-if="!collapsed" class="relative">
      <div v-if="thinkingText" class="rounded-xl bg-amber-50/60 border border-amber-200/40 p-4">
        <div class="text-sm text-amber-900/80 whitespace-pre-wrap leading-relaxed max-h-80 overflow-y-auto">
          {{ thinkingText }}
        </div>
        <div v-if="isStreaming" class="mt-2 flex items-center gap-1.5">
          <span class="w-1 h-3.5 bg-amber-400 rounded-sm animate-pulse"></span>
          <span class="text-xs text-amber-600/70">继续推理中...</span>
        </div>
      </div>
      <div v-else-if="isStreaming" class="py-6 flex items-center justify-center gap-2">
        <span class="w-4 h-4 border-2 border-amber-400 border-t-transparent rounded-full animate-spin"></span>
        <span class="text-sm text-on-surface-variant">等待思考内容...</span>
      </div>
    </div>
    <div v-else class="text-center py-2 text-sm text-on-surface-variant/60 cursor-pointer" @click="collapsed = false">
      已收起 — 点击展开思考过程
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'

defineProps({
  thinkingText: { type: String, default: '' },
  isStreaming: { type: Boolean, default: false },
})

const collapsed = ref(false)
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
</style>
