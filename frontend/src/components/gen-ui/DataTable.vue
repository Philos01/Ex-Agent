<template>
  <div class="data-table bg-surface rounded-xl border border-outline-variant/10 overflow-hidden">
    <div class="p-3 md:p-4 border-b border-outline-variant/10 bg-surface-container-low">
      <div class="flex items-center justify-between">
        <div class="flex items-center gap-2">
          <span class="material-symbols-outlined text-primary">table_chart</span>
          <h4 class="font-semibold text-on-surface text-sm">数据表格</h4>
        </div>
        <button 
          v-if="exportable"
          @click="exportData"
          class="p-1.5 hover:bg-surface-container rounded-lg transition-colors"
          title="导出为 CSV"
        >
          <span class="material-symbols-outlined text-on-surface-variant text-[18px]">download</span>
        </button>
      </div>
    </div>
    
    <div class="overflow-x-auto">
      <table class="w-full min-w-[300px]">
        <thead class="bg-surface-container">
          <tr>
            <th 
              v-for="(col, index) in columns" 
              :key="index"
              class="px-3 py-2 text-left text-xs font-bold text-on-surface-variant uppercase tracking-wide"
            >
              {{ col }}
            </th>
          </tr>
        </thead>
        <tbody class="divide-y divide-outline-variant/10">
          <tr 
            v-for="(row, rowIndex) in data" 
            :key="rowIndex"
            class="hover:bg-surface-container-low/50 transition-colors"
          >
            <td 
              v-for="(cell, cellIndex) in row" 
              :key="cellIndex"
              class="px-3 py-2 text-sm text-on-surface"
            >
              {{ cell }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
    
    <div v-if="data.length > 0" class="px-3 py-2 border-t border-outline-variant/10 bg-surface-container-lowest">
      <p class="text-xs text-outline">共 {{ data.length }} 条数据</p>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  columns: {
    type: Array,
    default: () => []
  },
  data: {
    type: Array,
    default: () => []
  },
  exportable: {
    type: Boolean,
    default: true
  }
})

const exportData = () => {
  if (!props.columns || !props.data) return
  
  // 构建 CSV 内容
  const csvContent = [
    props.columns.join(','),
    ...props.data.map(row => row.map(cell => `"${String(cell).replace(/"/g, '""')}"`).join(','))
  ].join('\n')
  
  // 创建下载链接
  const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
  const link = document.createElement('a')
  const url = URL.createObjectURL(blob)
  link.setAttribute('href', url)
  link.setAttribute('download', `data-table-${Date.now()}.csv`)
  link.style.visibility = 'hidden'
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
}
</script>
