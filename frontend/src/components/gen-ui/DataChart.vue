<template>
  <div class="data-chart bg-surface rounded-xl border border-outline-variant/10 overflow-hidden">
    <div class="p-3 md:p-4 border-b border-outline-variant/10 bg-surface-container-low">
      <div class="flex items-center gap-2">
        <span class="material-symbols-outlined text-primary">insert_chart</span>
        <h4 class="font-semibold text-on-surface text-sm">数据图表</h4>
      </div>
    </div>
    
    <div class="p-4">
      <canvas 
        ref="canvasRef"
        :width="canvasWidth"
        :height="canvasHeight"
        class="w-full"
      ></canvas>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, nextTick } from 'vue'

const props = defineProps({
  labels: {
    type: Array,
    default: () => []
  },
  values: {
    type: Array,
    default: () => []
  },
  title: {
    type: String,
    default: ''
  },
  type: {
    type: String,
    default: 'bar', // bar, line
    validator: (v) => ['bar', 'line'].includes(v)
  }
})

const canvasRef = ref(null)
const canvasWidth = ref(600)
const canvasHeight = ref(300)

const colors = [
  '#6750A4', // Primary
  '#006A6A', // Tertiary
  '#7D5260', // Error
  '#625B71', // Secondary
  '#0061A4',
  '#954DA1'
]

const drawChart = () => {
  if (!canvasRef.value || !props.labels.length || !props.values.length) return
  
  const canvas = canvasRef.value
  const ctx = canvas.getContext('2d')
  const width = canvas.width
  const height = canvas.height
  const padding = { top: 30, right: 30, bottom: 50, left: 50 }
  const chartWidth = width - padding.left - padding.right
  const chartHeight = height - padding.top - padding.bottom
  
  // 清空画布
  ctx.clearRect(0, 0, width, height)
  
  // 找出最大值和最小值
  const maxValue = Math.max(...props.values)
  const minValue = Math.min(0, Math.min(...props.values))
  const valueRange = maxValue - minValue || 1
  
  // 绘制 Y 轴刻度
  ctx.strokeStyle = '#CAC4D0'
  ctx.lineWidth = 1
  ctx.beginPath()
  ctx.moveTo(padding.left, padding.top)
  ctx.lineTo(padding.left, height - padding.bottom)
  ctx.stroke()
  
  // 绘制 X 轴
  ctx.beginPath()
  ctx.moveTo(padding.left, height - padding.bottom)
  ctx.lineTo(width - padding.right, height - padding.bottom)
  ctx.stroke()
  
  // 绘制网格线和 Y 轴标签
  ctx.fillStyle = '#49454F'
  ctx.font = '12px sans-serif'
  ctx.textAlign = 'right'
  
  const gridLines = 5
  for (let i = 0; i <= gridLines; i++) {
    const y = padding.top + (chartHeight * i / gridLines)
    const value = maxValue - (valueRange * i / gridLines)
    
    // 网格线
    ctx.strokeStyle = '#E7E0EC'
    ctx.beginPath()
    ctx.moveTo(padding.left, y)
    ctx.lineTo(width - padding.right, y)
    ctx.stroke()
    
    // Y 轴标签
    ctx.fillStyle = '#49454F'
    ctx.fillText(value.toFixed(1), padding.left - 10, y + 4)
  }
  
  if (props.type === 'bar') {
    // 绘制柱状图
    const barWidth = chartWidth / props.labels.length * 0.6
    const gap = chartWidth / props.labels.length * 0.4
    
    props.labels.forEach((label, i) => {
      const x = padding.left + (chartWidth / props.labels.length) * i + gap / 2
      const barHeight = (props.values[i] - minValue) / valueRange * chartHeight
      const y = height - padding.bottom - barHeight
      
      // 绘制柱子
      ctx.fillStyle = colors[i % colors.length]
      ctx.fillRect(x, y, barWidth, barHeight)
      
      // 绘制 X 轴标签
      ctx.fillStyle = '#49454F'
      ctx.font = '12px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(label, x + barWidth / 2, height - padding.bottom + 20)
      
      // 绘制数值标签
      ctx.fillStyle = '#1D1B20'
      ctx.font = 'bold 12px sans-serif'
      ctx.fillText(props.values[i].toString(), x + barWidth / 2, y - 8)
    })
  } else {
    // 绘制折线图
    const pointRadius = 4
    const stepX = chartWidth / (props.labels.length - 1)
    
    // 绘制线条
    ctx.strokeStyle = colors[0]
    ctx.lineWidth = 3
    ctx.lineCap = 'round'
    ctx.lineJoin = 'round'
    ctx.beginPath()
    
    props.values.forEach((value, i) => {
      const x = padding.left + stepX * i
      const y = height - padding.bottom - (value - minValue) / valueRange * chartHeight
      
      if (i === 0) {
        ctx.moveTo(x, y)
      } else {
        ctx.lineTo(x, y)
      }
    })
    ctx.stroke()
    
    // 绘制数据点和标签
    props.values.forEach((value, i) => {
      const x = padding.left + stepX * i
      const y = height - padding.bottom - (value - minValue) / valueRange * chartHeight
      
      // 数据点
      ctx.fillStyle = colors[0]
      ctx.beginPath()
      ctx.arc(x, y, pointRadius, 0, Math.PI * 2)
      ctx.fill()
      
      // X 轴标签
      ctx.fillStyle = '#49454F'
      ctx.font = '12px sans-serif'
      ctx.textAlign = 'center'
      ctx.fillText(props.labels[i], x, height - padding.bottom + 20)
      
      // 数值标签
      ctx.fillStyle = '#1D1B20'
      ctx.font = 'bold 12px sans-serif'
      ctx.fillText(value.toString(), x, y - 12)
    })
  }
}

const resize = () => {
  if (canvasRef.value && canvasRef.value.parentElement) {
    canvasWidth.value = canvasRef.value.parentElement.clientWidth - 32
  }
}

onMounted(() => {
  resize()
  nextTick(() => {
    drawChart()
  })
  window.addEventListener('resize', () => {
    resize()
    drawChart()
  })
})

watch(() => [props.labels, props.values, props.type], () => {
  drawChart()
}, { deep: true })
</script>
