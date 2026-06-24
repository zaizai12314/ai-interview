<template>
  <div class="max-w-3xl mx-auto mt-10 px-4">
    <div v-if="loading" class="text-center py-12"><LoadingSpinner text="正在生成报告..." /></div>
    <template v-else-if="report">
      <div class="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h2 class="text-2xl font-bold mb-2">{{ report.target_job }} - 面试报告</h2>
        <p class="text-gray-400 text-sm">完成时间: {{ report.completed_at?.slice(0, 16).replace("T", " ") }}</p>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-6 mb-6" v-if="report.history?.length">
        <h3 class="text-lg font-bold mb-4">逐题评分</h3>
        <ScoreChart :items="report.history.map(h => ({ score: h.score || 0 }))" />
        <div class="mt-6 space-y-4">
          <div v-for="(h, idx) in report.history" :key="idx" class="border-t pt-4">
            <p class="font-medium text-gray-800">Q{{ idx + 1 }}: {{ h.question }}</p>
            <p class="text-gray-600 mt-1 text-sm">回答: {{ h.answer || "(未回答)" }}</p>
            <p class="text-sm font-bold mt-2" :class="h.score >= 80 ? 'text-green-600' : h.score >= 60 ? 'text-yellow-600' : 'text-red-600'">得分: {{ h.score }}</p>
            <p class="text-gray-500 text-sm mt-1">{{ h.feedback }}</p>
          </div>
        </div>
      </div>
      <div class="bg-white rounded-xl shadow-sm p-6" v-if="report.report">
        <h3 class="text-lg font-bold mb-4">综合评估</h3>
        <div class="prose prose-sm max-w-none" v-html="report.report.replace(/\n/g, '<br>')"></div>
      </div>
    </template>
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue"
import { useRoute } from "vue-router"
import api from "../api"
import ScoreChart from "../components/ScoreChart.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
const route = useRoute()
const report = ref(null)
const loading = ref(true)
onMounted(async () => { try { const { data } = await api.getReport(route.params.id); report.value = data } catch (e) { alert("加载报告失败") } finally { loading.value = false } })
</script>
