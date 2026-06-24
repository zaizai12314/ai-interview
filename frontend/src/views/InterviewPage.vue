<template>
  <div class="max-w-2xl mx-auto mt-10 px-4">
    <div v-if="loading" class="text-center py-12"><LoadingSpinner :text="loadingText" /></div>
    <template v-else-if="state.action === 'ask_question' || !state.action">
      <QuestionCard :question="currentQuestion" :round="state.round || 1" :progress="state.progress || 0" :submitting="submitting" @submit="handleSubmit" />
    </template>
    <template v-else-if="state.action === 'finish'">
      <div class="bg-white rounded-xl shadow-sm p-8 text-center">
        <div class="text-5xl mb-4">🎉</div>
        <h2 class="text-2xl font-bold mb-2">面试结束</h2>
        <p class="text-gray-500 mb-6">AI 面试官已完成对您的评估</p>
        <router-link :to="`/interview/${route.params.id}/report`" class="inline-block bg-indigo-600 text-white px-8 py-3 rounded-lg hover:bg-indigo-700 transition font-medium">查看面试报告</router-link>
      </div>
    </template>
    <ScoreFeedback v-if="showFeedback" :score="feedback.score" :feedback="feedback.feedback" :nextAction="nextActionAfterFeedback" @close="handleFeedbackClose" />
  </div>
</template>
<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue"
import { useRoute } from "vue-router"
import api from "../api"
import QuestionCard from "../components/QuestionCard.vue"
import ScoreFeedback from "../components/ScoreFeedback.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
const route = useRoute()
const loading = ref(true)
const submitting = ref(false)
const state = ref({})
const showFeedback = ref(false)
const feedback = ref({})
const nextActionAfterFeedback = ref("ask_question")
const lastDisplayedRound = ref(0)
let pollTimer = null
const loadingText = computed(() => state.value._loadingText || "面试官正在准备题目...")
const currentQuestion = computed(() => state.value.content || "准备中...")
onMounted(() => { startPolling() })
onUnmounted(() => { if (pollTimer) clearInterval(pollTimer) })

function startPolling() {
  if (pollTimer) clearInterval(pollTimer)
  pollTimer = setInterval(async () => {
    try {
      const { data } = await api.getInterview(route.params.id)
      const currentRound = data.current_round || 0

      // 1. 面试完成
      if (data.status === "completed") {
        state.value = { action: "finish", content: "面试已结束" }
        loading.value = false
        clearInterval(pollTimer)
        pollTimer = null
        return
      }

      // current_question 为 null/undefined 时继续轮询（空字符串也算有效内容，不跳过）
      if (data.current_question == null) return

      // 2. 新轮次到达（Celery 处理完成）
      if (currentRound > lastDisplayedRound.value) {
        lastDisplayedRound.value = currentRound

        // 如果有上一题的评分反馈，先弹窗展示
        if (data.evaluation) {
          feedback.value = {
            score: data.evaluation.score || 0,
            feedback: data.evaluation.feedback || ""
          }
          nextActionAfterFeedback.value = "ask_question"
          showFeedback.value = true
        }

        // 显示新题目（如果同时有反馈弹窗，题目在弹窗后面渲染）
        state.value = {
          action: "ask_question",
          content: data.current_question,
          round: currentRound,
          progress: Math.min(currentRound / 10, 1.0)
        }
        loading.value = false
        clearInterval(pollTimer)
        pollTimer = null
      }
      // else: 轮次没变 → Celery 还在处理，继续等待
    } catch (e) { /* poll - ignore errors */ }
  }, 2000)
}

async function handleSubmit(answer) {
  submitting.value = true
  showFeedback.value = false
  try {
    await api.submitAnswer(route.params.id, answer)
    // 提交后进入加载状态，启动轮询等待评估和新题目
    // 注意：不清空 state，保持当前问题可见（loading=true 会覆盖显示，但 state.round 保留）
    state.value = { _loadingText: "AI 面试官正在评估你的回答，请稍候..." }
    loading.value = true
    startPolling()
  } catch (e) {
    alert("提交失败: " + (e.response?.data?.detail || e.message))
  } finally {
    submitting.value = false
  }
}

function handleFeedbackClose() {
  showFeedback.value = false
  // 关闭反馈后如果面试结束，跳转到完成界面
  if (nextActionAfterFeedback.value === "finish") {
    state.value = { action: "finish", content: "面试已结束" }
    return
  }
  // state.value 已有新题目，无需额外操作
}
</script>
