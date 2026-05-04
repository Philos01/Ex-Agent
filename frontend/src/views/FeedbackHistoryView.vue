<template>
  <div class="flex-1 flex flex-col h-[calc(100vh-4rem)]">
    <div class="px-4 md:px-12 py-6">
      <div class="max-w-4xl mx-auto">
        <div class="flex items-center justify-between mb-6">
          <div class="flex items-center gap-3">
            <span class="material-symbols-outlined text-2xl text-primary">feedback</span>
            <h2 class="text-xl font-bold text-on-surface">反馈历史</h2>
          </div>
          <button @click="loadFeedback" class="px-3 py-1.5 bg-surface-container rounded-lg text-sm text-on-surface-variant hover:bg-surface-container-high transition-colors">
            刷新
          </button>
        </div>

        <div v-if="statistics" class="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div class="p-3 bg-surface-container-low rounded-xl text-center">
            <p class="text-2xl font-black text-primary">{{ statistics.total || 0 }}</p>
            <p class="text-xs text-on-surface-variant">总反馈数</p>
          </div>
          <div class="p-3 bg-surface-container-low rounded-xl text-center">
            <p class="text-2xl font-black text-green-600">{{ statistics.applied || 0 }}</p>
            <p class="text-xs text-on-surface-variant">已应用</p>
          </div>
          <div class="p-3 bg-surface-container-low rounded-xl text-center">
            <p class="text-2xl font-black text-amber-600">{{ ((statistics.application_rate || 0) * 100).toFixed(0) }}%</p>
            <p class="text-xs text-on-surface-variant">应用率</p>
          </div>
          <div class="p-3 bg-surface-container-low rounded-xl text-center">
            <p class="text-2xl font-black text-blue-600">{{ Object.keys(statistics.by_session || {}).length }}</p>
            <p class="text-xs text-on-surface-variant">涉及会话</p>
          </div>
        </div>

        <div v-if="sessionIds.length > 0" class="mb-4">
          <select v-model="selectedSession" @change="loadSessionFeedback" class="w-full md:w-64 px-3 py-2 bg-surface-container rounded-lg text-sm text-on-surface border border-outline-variant/20 focus:border-primary/40 focus:outline-none">
            <option value="">全部会话</option>
            <option v-for="sid in sessionIds" :key="sid" :value="sid">{{ sid }}</option>
          </select>
        </div>

        <FeedbackHistory :feedback-list="feedbackList" :loading="loading" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import FeedbackHistory from '../components/gen-ui/FeedbackHistory.vue'

const feedbackList = ref([])
const statistics = ref(null)
const loading = ref(false)
const selectedSession = ref('')
const sessionIds = ref([])

const loadFeedback = async () => {
  loading.value = true
  try {
    const res = await fetch('/api/human-feedback-statistics')
    if (res.ok) {
      const data = await res.json()
      statistics.value = data.statistics
      sessionIds.value = Object.keys(data.statistics?.by_session || {})
    }
    if (selectedSession.value) {
      await loadSessionFeedback()
    }
  } catch (e) {
    console.error('Failed to load feedback statistics:', e)
  } finally {
    loading.value = false
  }
}

const loadSessionFeedback = async () => {
  if (!selectedSession.value) {
    feedbackList.value = []
    return
  }
  loading.value = true
  try {
    const res = await fetch(`/api/human-feedback/${selectedSession.value}`)
    if (res.ok) {
      const data = await res.json()
      feedbackList.value = data.feedback || []
    }
  } catch (e) {
    console.error('Failed to load session feedback:', e)
  } finally {
    loading.value = false
  }
}

onMounted(() => { loadFeedback() })
</script>
