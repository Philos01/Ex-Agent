/**
 * useReActStream — Composable for handling ReAct Agent SSE streaming.
 *
 * Extracted from ChatView.vue to keep the component focused on UI rendering.
 * Handles SSE parsing, ReAct step accumulation, and state management.
 */
import { ref, nextTick } from 'vue'
import {
  SSE_REACT_THOUGHT, SSE_REACT_ACTION, SSE_REACT_OBSERVATION,
  SSE_REACT_FINAL_ANSWER, SSE_REACT_STEPS, SSE_REACT_ERROR,
  SSE_CONTENT, SSE_SOURCES, SSE_STATE, SSE_COMPONENT, SSE_DONE,
  STEP_THOUGHT, STEP_ACTION, STEP_OBSERVATION, STEP_FINAL_ANSWER,
} from '../constants/sseEvents.js'

/**
 * @param {object} options
 * @param {import('vue').Ref<Array>} options.messages
 * @param {import('vue').Ref<boolean>} options.isReActRunning
 * @param {import('vue').Ref<boolean>} options.loading
 * @param {import('vue').Ref<boolean>} options.streaming
 * @param {Function} options.scrollToBottom
 * @returns {object}
 */
export function useReActStream({ messages, isReActRunning, loading, streaming, scrollToBottom }) {
  const reactSteps = ref([])
  let receivedFinalAnswer = false
  let fullText = ''
  let sources = []
  let _syncedToMessage = false

  function _ensureSynced() {
    if (!_syncedToMessage) {
      const idx = messages.value.length - 1
      if (idx >= 0) {
        messages.value[idx].reactSteps = reactSteps.value  // reference, not copy
        _syncedToMessage = true
      }
    }
  }

  function _addStep(step) {
    reactSteps.value.push(step)
    _ensureSynced()
    scrollToBottom?.()
  }

  function _stopAll() {
    isReActRunning.value = false
    loading.value = false
    streaming.value = false
  }

  function processSSEEvent(parsed) {
    const lastIndex = messages.value.length - 1
    if (lastIndex < 0) return

    switch (parsed.type) {
      case SSE_CONTENT:
        if (!receivedFinalAnswer) {
          fullText += parsed.content
          messages.value[lastIndex].text = fullText
          messages.value[lastIndex].time = formatTime()
          scrollToBottom?.()
        }
        break

      case SSE_SOURCES:
        sources = parsed.sources || []
        messages.value[lastIndex].sources = sources
        break

      case SSE_STATE:
        messages.value[lastIndex].thinkingState = {
          phase: parsed.phase, message: parsed.message, progress: parsed.progress,
        }
        scrollToBottom?.()
        break

      case SSE_COMPONENT:
        messages.value[lastIndex].components = messages.value[lastIndex].components || []
        messages.value[lastIndex].components.push({
          type: parsed.component, props: parsed.props,
        })
        scrollToBottom?.()
        break

      case SSE_REACT_THOUGHT:
        _addStep({ type: STEP_THOUGHT, content: parsed.content, timestamp: Date.now() })
        break

      case SSE_REACT_ACTION:
        _addStep({
          type: STEP_ACTION, name: parsed.name,
          input: normalizeInput(parsed.input), timestamp: Date.now(),
        })
        break

      case SSE_REACT_OBSERVATION:
        _addStep({ type: STEP_OBSERVATION, content: parsed.content, timestamp: Date.now() })
        break

      case SSE_REACT_FINAL_ANSWER:
        receivedFinalAnswer = true
        const finalContent = parsed.content
        _addStep({ type: STEP_FINAL_ANSWER, content: finalContent, timestamp: Date.now() })
        fullText = finalContent
        messages.value[lastIndex].text = fullText
        messages.value[lastIndex].time = formatTime()
        _stopAll()
        nextTick(() => scrollToBottom?.())
        break

      case SSE_REACT_STEPS:
      case SSE_REACT_ERROR:
        if (parsed.type === SSE_REACT_ERROR) {
          console.error('[ReAct] Error:', parsed.message)
        }
        _stopAll()
        break

      default:
        break
    }
  }

  function processSSELine(rawText) {
    if (rawText === SSE_DONE) return
    try {
      processSSEEvent(JSON.parse(rawText))
    } catch (e) {
      console.error('[useReActStream] Parse error:', e)
    }
  }

  function resetReAct() {
    reactSteps.value = []
    receivedFinalAnswer = false
    fullText = ''
    sources = []
    _syncedToMessage = false
  }

  return {
    reactSteps, processSSEEvent, processSSELine, resetReAct,
    getFullText: () => fullText,
    getSources: () => sources,
  }
}

function normalizeInput(input) {
  if (typeof input === 'string') {
    try { return JSON.parse(input) } catch { return input }
  }
  return input
}

function formatTime() {
  return new Date().toLocaleTimeString('zh-CN', { hour: '2-digit', minute: '2-digit' })
}
