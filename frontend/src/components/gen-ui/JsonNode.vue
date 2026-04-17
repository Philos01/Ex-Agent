<template>
  <div class="json-node">
    <!-- 键名（总是显示，如果有） -->
    <span v-if="keyName" class="json-key">{{ escapeKey(keyName) }}</span>
    <span v-if="keyName" class="json-colon">: </span>

    <!-- 值部分（独立的条件判断） -->
    <!-- 空值 -->
    <span v-if="nodeValue === null" class="json-null">null</span>

    <!-- 布尔值 -->
    <span v-else-if="typeof nodeValue === 'boolean'" class="json-boolean">{{ nodeValue ? 'true' : 'false' }}</span>

    <!-- 数字 -->
    <span v-else-if="typeof nodeValue === 'number'" class="json-number">{{ nodeValue }}</span>

    <!-- 字符串 -->
    <span v-else-if="typeof nodeValue === 'string'" class="json-string">"{{ escapeString(nodeValue) }}"</span>

    <!-- 数组 -->
    <template v-else-if="Array.isArray(nodeValue)">
      <span class="json-bracket">[</span>
      <span 
        v-if="!isExpanded && nodeValue.length > 0"
        class="json-ellipsis"
        @click="toggle"
      >
        {{ nodeValue.length }} item{{ nodeValue.length !== 1 ? 's' : '' }}
      </span>
      <button 
        v-if="isExpandable && !isExpanded"
        @click="toggle"
        class="json-toggle-btn"
      >
        <span class="material-symbols-outlined text-sm">chevron_right</span>
      </button>
      <button 
        v-if="isExpandable && isExpanded"
        @click="toggle"
        class="json-toggle-btn"
      >
        <span class="material-symbols-outlined text-sm">expand_more</span>
      </button>
      <div v-if="isExpanded" class="json-children" :style="{ marginLeft: indent + 'px' }">
        <div v-for="(item, index) in nodeValue" :key="index" class="json-item">
          <JsonNode 
            :value="item"
            :key-name="null"
            :depth="depth + 1"
            :expand-level="expandLevel"
            @toggle="$emit('toggle', ...arguments)"
          />
          <span v-if="index < nodeValue.length - 1" class="json-comma">,</span>
        </div>
      </div>
      <span class="json-bracket">]</span>
    </template>

    <!-- 对象 -->
    <template v-else-if="typeof nodeValue === 'object' && nodeValue !== null">
      <span class="json-brace">{</span>
      <span 
        v-if="!isExpanded && Object.keys(nodeValue).length > 0"
        class="json-ellipsis"
        @click="toggle"
      >
        {{ Object.keys(nodeValue).length }} key{{ Object.keys(nodeValue).length !== 1 ? 's' : '' }}
      </span>
      <button 
        v-if="isExpandable && !isExpanded"
        @click="toggle"
        class="json-toggle-btn"
      >
        <span class="material-symbols-outlined text-sm">chevron_right</span>
      </button>
      <button 
        v-if="isExpandable && isExpanded"
        @click="toggle"
        class="json-toggle-btn"
      >
        <span class="material-symbols-outlined text-sm">expand_more</span>
      </button>
      <div v-if="isExpanded" class="json-children" :style="{ marginLeft: indent + 'px' }">
        <div v-for="(key, index) in sortedKeys" :key="key" class="json-item">
          <JsonNode 
            :value="nodeValue[key]"
            :key-name="key"
            :depth="depth + 1"
            :expand-level="expandLevel"
            @toggle="$emit('toggle', ...arguments)"
          />
          <span v-if="index < sortedKeys.length - 1" class="json-comma">,</span>
        </div>
      </div>
      <span class="json-brace">}</span>
    </template>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'

const props = defineProps({
  value: {
    type: [String, Number, Boolean, Object, Array, null],
    required: true
  },
  keyName: {
    type: [String, Number],
    default: null
  },
  depth: {
    type: Number,
    default: 0
  },
  expandLevel: {
    type: Number,
    default: 2
  }
})

const emit = defineEmits(['toggle'])

const isExpandedLocal = ref(null)
const indent = 20

// 核心：添加 nodeValue computed 属性
const nodeValue = computed(() => {
  console.log('[DEBUG] JsonNode nodeValue:', props.value, 'type:', typeof props.value)
  return props.value
})

const nodePath = computed(() => {
  return props.keyName ? `${props.keyName}_${props.depth}` : `root_${props.depth}`
})

const isExpandable = computed(() => {
  if (Array.isArray(nodeValue.value)) {
    return nodeValue.value.length > 0
  }
  if (typeof nodeValue.value === 'object' && nodeValue.value !== null) {
    return Object.keys(nodeValue.value).length > 0
  }
  return false
})

const isExpanded = computed({
  get: () => {
    if (isExpandedLocal.value !== null) {
      return isExpandedLocal.value
    }
    return props.depth < props.expandLevel
  },
  set: (val) => {
    isExpandedLocal.value = val
  }
})

const sortedKeys = computed(() => {
  if (typeof nodeValue.value === 'object' && nodeValue.value !== null && !Array.isArray(nodeValue.value)) {
    const keys = Object.keys(nodeValue.value).sort()
    console.log('[DEBUG] JsonNode sortedKeys:', keys, 'for value:', nodeValue.value)
    return keys
  }
  return []
})

const toggle = () => {
  isExpanded.value = !isExpanded.value
  emit('toggle', nodePath.value, isExpanded.value)
}

const escapeString = (str) => {
  if (typeof str !== 'string') {
    str = String(str)
  }
  return str
    .replace(/\\/g, '\\\\')
    .replace(/"/g, '\\"')
    .replace(/\n/g, '\\n')
    .replace(/\r/g, '\\r')
    .replace(/\t/g, '\\t')
}

const escapeKey = (key) => {
  if (key === null || key === undefined) {
    return ''
  }
  const keyStr = String(key)
  if (/^[a-zA-Z_$][a-zA-Z0-9_$]*$/.test(keyStr)) {
    return keyStr
  }
  return `"${escapeString(keyStr)}"`
}
</script>

<style scoped>
.json-node {
  display: inline;
}

.json-key {
  color: #9cdcfe;
}

.json-colon {
  color: #d4d4d4;
}

.json-null {
  color: #569cd6;
}

.json-boolean {
  color: #569cd6;
}

.json-number {
  color: #b5cea8;
}

.json-string {
  color: #ce9178;
}

.json-bracket,
.json-brace {
  color: #ffd700;
  font-weight: 600;
}

.json-comma {
  color: #d4d4d4;
}

.json-ellipsis {
  color: #6a9955;
  cursor: pointer;
  user-select: none;
  padding: 0 4px;
  border-radius: 4px;
}

.json-ellipsis:hover {
  background-color: rgba(255, 255, 255, 0.1);
}

.json-toggle-btn {
  background: none;
  border: none;
  cursor: pointer;
  padding: 2px 4px;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  margin: 0 2px;
  color: #808080;
  transition: all 0.15s;
}

.json-toggle-btn:hover {
  background-color: rgba(255, 255, 255, 0.1);
  color: #d4d4d4;
}

.json-children {
  display: block;
}

.json-item {
  display: block;
}
</style>
