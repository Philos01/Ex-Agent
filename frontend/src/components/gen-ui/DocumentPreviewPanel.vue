<template>
  <div>
    <!-- 遮罩层 - 点击外部关闭 -->
    <div 
      v-if="visible" 
      class="fixed inset-0 bg-black/20 z-30"
      @click="close"
    ></div>
    
    <!-- 文档预览面板 -->
    <div 
      v-if="visible" 
      class="fixed right-0 top-16 bottom-0 w-96 bg-surface border-l border-outline-variant/20 shadow-2xl z-40 flex flex-col"
    >
      <!-- 头部 -->
      <div class="p-4 border-b border-outline-variant/20 flex items-center justify-between bg-surface-container">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-primary">description</span>
          <h3 class="font-bold text-on-surface truncate max-w-[200px]">
            {{ documentData?.filename || '文档预览' }}
          </h3>
        </div>
        <button 
          @click="close"
          class="p-2 hover:bg-surface-container-high rounded-lg transition-colors"
        >
          <span class="material-symbols-outlined text-on-surface-variant">close</span>
        </button>
      </div>

      <!-- 加载状态 -->
      <div v-if="loading" class="flex-1 flex items-center justify-center">
        <div class="flex flex-col items-center gap-3">
          <span class="material-symbols-outlined text-primary text-4xl animate-spin">progress_activity</span>
          <p class="text-on-surface-variant text-sm">加载文档...</p>
        </div>
      </div>

      <!-- 错误状态 -->
      <div v-else-if="error" class="flex-1 flex items-center justify-center p-4">
        <div class="text-center">
          <span class="material-symbols-outlined text-error text-4xl mb-2">error</span>
          <p class="text-error text-sm">{{ error }}</p>
        </div>
      </div>

      <!-- 文档内容 -->
      <div v-else class="flex-1 overflow-y-auto p-4 space-y-4">
        <!-- 检索到的内容（高亮显示） -->
        <div v-if="sourceText">
          <div class="flex items-center gap-2 mb-2">
            <span class="material-symbols-outlined text-primary text-[18px]">search</span>
            <h4 class="font-semibold text-primary text-sm">检索内容</h4>
          </div>
          <div class="bg-primary-container/30 p-3 rounded-lg border border-primary/20">
            <p class="text-on-surface text-sm whitespace-pre-wrap leading-relaxed">
              {{ sourceText }}
            </p>
          </div>
        </div>
        
        <!-- Chunk 高亮显示（如果有） -->
        <div v-if="documentData?.chunk_content">
          <div class="flex items-center gap-2 mb-2">
            <span class="material-symbols-outlined text-tertiary text-[18px]">highlight</span>
            <h4 class="font-semibold text-tertiary text-sm">匹配 Chunk</h4>
          </div>
          <div class="bg-tertiary-container/30 p-3 rounded-lg border border-tertiary/20">
            <p class="text-on-surface text-sm whitespace-pre-wrap leading-relaxed">
              {{ documentData.chunk_content }}
            </p>
          </div>
        </div>
        
        <!-- 完整文档 -->
        <div v-if="documentData?.full_text">
          <div class="flex items-center gap-2 mb-2">
            <span class="material-symbols-outlined text-on-surface-variant text-[18px]">article</span>
            <h4 class="font-semibold text-on-surface-variant text-sm">完整文档</h4>
          </div>
          <div class="bg-surface-container-low p-3 rounded-lg border border-outline-variant/10">
            <p class="text-on-surface text-xs whitespace-pre-wrap leading-relaxed opacity-80">
              {{ documentData.full_text }}
            </p>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import api from '../../services/api'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  filename: {
    type: String,
    default: null
  },
  chunkIndex: {
    type: Number,
    default: null
  },
  sourceText: {
    type: String,
    default: null
  }
})

const emit = defineEmits(['close'])

const loading = ref(false)
const error = ref(null)
const documentData = ref(null)

const loadDocument = async () => {
  if (!props.filename) {
    // 如果没有文件名，但有 sourceText，至少显示 sourceText
    if (props.sourceText) {
      documentData.value = {
        filename: props.filename || '文档',
        chunk_content: null,
        full_text: null
      }
    }
    return
  }

  loading.value = true
  error.value = null
  documentData.value = null

  try {
    const params = { filename: props.filename }
    if (props.chunkIndex !== null) {
      params.chunk_index = props.chunkIndex
    }

    const response = await api.get('/document/preview', { params })
    documentData.value = response.data
  } catch (e) {
    console.error('加载文档失败:', e)
    error.value = e.response?.data?.detail || '加载文档失败，请重试'
  } finally {
    loading.value = false
  }
}

const close = () => {
  emit('close')
}

watch(() => [props.visible, props.filename, props.chunkIndex, props.sourceText], () => {
  if (props.visible) {
    loadDocument()
  }
}, { immediate: true })
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
