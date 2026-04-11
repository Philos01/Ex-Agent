<template>
  <div class="px-4 md:px-12 py-6 md:py-8 max-w-7xl mx-auto space-y-6 md:space-y-8">
    <div class="space-y-2">
      <h1 class="text-2xl md:text-4xl font-black text-on-surface tracking-tight">知识库</h1>
      <p class="text-on-surface-variant text-base md:text-lg">管理和维护驱动 Ex-Agent 推理引擎的通用数据和科学文档。</p>
    </div>

    <!-- 统计卡片 -->
    <div class="grid gap-4 md:gap-6 grid-cols-1 md:grid-cols-2">
      <div class="bg-surface rounded-xl md:rounded-2xl p-4 md:p-6 shadow-sm border border-outline-variant/10">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs md:text-sm font-bold text-on-surface-variant uppercase tracking-wide mb-1">向量化文档</p>
            <p class="text-3xl md:text-4xl font-black text-primary">{{ Math.round(vectorData.docCount/100) }}</p>
            <p class="text-xs text-outline mt-1 flex items-center gap-1">
              <span class="material-symbols-outlined text-[14px]">trending_up</span>
              自上次更新
            </p>
          </div>
          <div class="w-12 h-12 md:w-16 md:h-16 rounded-full bg-primary-container/40 flex items-center justify-center">
            <span class="material-symbols-outlined text-2xl md:text-3xl text-primary">widgets</span>
          </div>
        </div>
      </div>
      
      <div class="bg-surface rounded-xl md:rounded-2xl p-4 md:p-6 shadow-sm border border-outline-variant/10">
        <div class="flex items-start justify-between">
          <div>
            <p class="text-xs md:text-sm font-bold text-on-surface-variant uppercase tracking-wide mb-1">内存占用</p>
            <p class="text-3xl md:text-4xl font-black text-tertiary">{{ (vectorData.memoryUsage / 1024).toFixed(2) }} GB</p>
            <p class="text-xs text-outline mt-1">占用率: {{ Math.min(100, Math.round((vectorData.memoryUsage / 1024 / 10) * 100)) }}%</p>
          </div>
          <div class="w-12 h-12 md:w-16 md:h-16 rounded-full bg-tertiary-container/40 flex items-center justify-center">
            <span class="material-symbols-outlined text-2xl md:text-3xl text-tertiary">memory</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 上传区域 -->
    <div class="bg-surface rounded-xl md:rounded-2xl p-6 md:p-8 shadow-sm border border-outline-variant/10 border-dashed text-center">
      <div class="w-16 h-16 md:w-20 md:h-20 mx-auto bg-surface-container rounded-full flex items-center justify-center mb-4 md:mb-6">
        <span class="material-symbols-outlined text-3xl md:text-[40px] text-primary">cloud_upload</span>
      </div>
      <h3 class="text-lg md:text-xl font-black text-on-surface mb-2">当前知识库</h3>
      <p class="text-on-surface-variant max-w-md mx-auto mb-6 md:mb-8 text-sm md:text-base">拖放 PDF、CSV 或 XML 实验报告。Luminary AI 将自动为知识图谱向量化内容。</p>
      
      <div class="flex flex-col sm:flex-row items-center justify-center gap-3 md:gap-4">
        <input 
          ref="fileInputRef"
          type="file" 
          multiple 
          accept=".pdf,.docx,.doc,.pptx,.txt,.csv,.md"
          @change="handleFileSelect"
          class="hidden"
        />
        <button 
          @click="$refs.fileInputRef.click()" 
          :disabled="uploading"
          class="w-full sm:w-auto px-4 md:px-6 py-2.5 bg-surface-container-high text-on-surface rounded-xl font-bold hover:bg-surface-container transition-colors disabled:opacity-50"
        >
          选择文件
        </button>
        <button 
          @click="upload" 
          :disabled="uploading || selectedFiles.length === 0"
          class="w-full sm:w-auto px-4 md:px-6 py-2.5 bg-primary text-on-primary rounded-xl font-bold hover:bg-primary/90 transition-colors disabled:opacity-50 flex items-center justify-center gap-2"
        >
          <span v-if="uploading" class="material-symbols-outlined animate-spin text-base">progress_activity</span>
          {{ uploading ? '处理中...' : '同步知识库' }}
        </button>
      </div>
      
      <div v-if="selectedFiles.length > 0" class="mt-4">
        <p class="text-sm text-on-surface-variant mb-2">已选择 {{ selectedFiles.length }} 个文件</p>
        <div class="max-h-32 overflow-y-auto space-y-1">
          <p v-for="(file, i) in selectedFiles" :key="i" class="text-xs text-on-surface truncate">{{ file.name }}</p>
        </div>
      </div>
      
      <div v-if="uploading" class="mt-4 md:mt-6">
        <div class="w-full bg-surface-container-high rounded-full h-2">
          <div class="bg-primary h-2 rounded-full transition-all" :style="{ width: '100%' }"></div>
        </div>
        <p class="text-xs text-outline mt-2">上传中 100%</p>
      </div>
    </div>

    <!-- 文档列表 -->
    <div class="bg-surface rounded-xl md:rounded-2xl shadow-sm border border-outline-variant/10 overflow-hidden">
      <div class="p-4 md:p-6 border-b border-outline-variant/10 flex items-center justify-between">
        <h3 class="text-lg md:text-xl font-black text-on-surface">当前知识库</h3>
        <div class="flex items-center gap-1 md:gap-2">
          <button class="p-2 hover:bg-surface-container rounded-lg transition-colors" @click="refreshData">
            <span class="material-symbols-outlined text-on-surface-variant">refresh</span>
          </button>
          <button class="p-2 hover:bg-surface-container rounded-lg transition-colors hidden md:block">
            <span class="material-symbols-outlined text-on-surface-variant">filter_list</span>
          </button>
          <button class="p-2 hover:bg-surface-container rounded-lg transition-colors hidden md:block">
            <span class="material-symbols-outlined text-on-surface-variant">more_vert</span>
          </button>
        </div>
      </div>
      
      <div class="overflow-x-auto">
        <table class="w-full min-w-[600px]">
          <thead class="bg-surface-container-low">
            <tr>
              <th class="text-left p-3 md:p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wide">文件名</th>
              <th class="text-right p-3 md:p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wide">大小</th>
              <th class="text-right p-3 md:p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wide hidden sm:table-cell">上传日期</th>
              <th class="text-center p-3 md:p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wide">状态</th>
              <th class="text-center p-3 md:p-4 text-xs font-bold text-on-surface-variant uppercase tracking-wide">操作</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-outline-variant/10">
            <tr v-for="(doc, index) in docs" :key="index" class="hover:bg-surface-container-low transition-colors">
              <td class="p-3 md:p-4">
                <div class="flex items-center gap-2 md:gap-3">
                  <span class="material-symbols-outlined text-xl md:text-2xl text-primary">description</span>
                  <span class="font-medium text-on-surface text-sm md:text-base">{{ doc.filename }}</span>
                </div>
              </td>
              <td class="p-3 md:p-4 text-right text-on-surface-variant text-sm">{{ formatFileSize(doc.size) }} MB</td>
              <td class="p-3 md:p-4 text-right text-on-surface-variant text-sm hidden sm:table-cell">{{ formatDate(doc.upload_time) }}</td>
              <td class="p-3 md:p-4 text-center">
                <span class="px-2 py-1 bg-primary-container/50 text-primary rounded-full text-xs font-bold inline-flex items-center gap-1">
                  <span class="material-symbols-outlined text-[14px] md:text-[16px]">check_circle</span>
                  <span class="hidden sm:inline">已向量化</span>
                </span>
              </td>
              <td class="p-3 md:p-4 text-center">
                <div class="flex items-center justify-center gap-1 md:gap-2">
                  <button class="p-1.5 hover:bg-surface-container rounded-lg transition-colors" @click="viewDocument(doc)">
                    <span class="material-symbols-outlined text-primary text-base">visibility</span>
                  </button>
                  <button class="p-1.5 hover:bg-surface-container rounded-lg transition-colors" @click="remove(doc.filename)">
                    <span class="material-symbols-outlined text-error text-base">delete</span>
                  </button>
                </div>
              </td>
            </tr>
            <tr v-if="docs.length === 0">
              <td colspan="5" class="p-6 md:p-8 text-center text-on-surface-variant">
                暂无上传的文档
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      
      <div class="p-3 md:p-4 border-t border-outline-variant/10 flex items-center justify-between text-xs text-outline">
        <span>显示 {{ docs.length }} 份文档</span>
        <div class="flex items-center gap-1 md:gap-2">
          <button disabled class="p-1 opacity-30">
            <span class="material-symbols-outlined">chevron_left</span>
          </button>
          <button disabled class="p-1">
            <span class="material-symbols-outlined">chevron_right</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import api from '../services/api'

const fileInputRef = ref(null)
const selectedFiles = ref([])
const uploading = ref(false)
const docs = ref([])
const vectorData = ref({
  docCount: 0,
  memoryUsage: 0
})

const formatDate = (dateStr) => {
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0'
  const sizeInMB = parseFloat(bytes) / (1024 * 1024)
  return sizeInMB.toFixed(2)
}

const loadList = async () => {
  try {
    const res = await api.get('/documents')
    docs.value = res.data.documents || []
    loadVectorData(docs.value)
  } catch (e) {
    console.error('Failed to load documents:', e)
  }
}

const loadVectorData = (documents = docs.value) => {
  const chunkSize = 100 // 假设平均每个文档100个chunk
  
  let totalChunks = 0
  let totalSizeInMB = 0
  
  documents.forEach(doc => {
    totalChunks += chunkSize
    // 将字节转换为MB
    const sizeInBytes = parseFloat(doc.size) || 0
    const sizeInMB = sizeInBytes / (1024 * 1024)
    totalSizeInMB += sizeInMB
  })
  
  vectorData.value = {
    docCount: totalChunks,
    memoryUsage: totalSizeInMB
  }
}

const handleFileSelect = (e) => {
  selectedFiles.value = Array.from(e.target.files)
}

const upload = async () => {
  if (selectedFiles.value.length === 0) return
  
  uploading.value = true
  
  try {
    const formData = new FormData()
    selectedFiles.value.forEach(file => {
      formData.append('files', file)
    })
    
    const response = await api.post('/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
    
    const result = response.data
    selectedFiles.value = []
    
    // 显示结果提示
    let message = `成功处理 ${result.files?.length || 0} 个文件`
    if (result.failed?.length > 0) {
      message += `，失败 ${result.failed.length} 个文件\n\n失败文件：\n`
      result.failed.forEach(item => {
        message += `- ${item.filename}: ${item.reason}\n`
      })
    }
    
    alert(message)
    await refreshData()
  } catch (e) {
    console.error('Upload failed:', e)
    // 显示更详细的错误信息
    const errorMsg = e.response?.data?.detail || e.message || '上传失败，请重试'
    alert('上传失败: ' + errorMsg)
  } finally {
    uploading.value = false
  }
}

const remove = async (filename) => {
  if (!confirm('确定要删除这个文档吗？')) return
  
  try {
    await api.delete('/documents', {
      params: { file: filename }
    })
    await refreshData()
  } catch (e) {
    console.error('Delete failed:', e)
    alert('删除失败，请重试')
  }
}

const viewDocument = (doc) => {
  alert('查看文档: ' + doc.filename)
}

const refreshData = async () => {
  await loadList()
}

onMounted(() => {
  loadList()
})
</script>
