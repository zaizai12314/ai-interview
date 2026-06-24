<template>
  <div class="max-w-3xl mx-auto mt-10 px-4">
    <h2 class="text-2xl font-bold mb-6">面试历史</h2>
    <div v-if="interviews.length === 0" class="text-gray-400 text-center py-12">暂无面试记录</div>
    <div v-for="i in interviews" :key="i.id" class="bg-white rounded-lg shadow-sm p-4 mb-3">
      <div class="flex justify-between items-center">
        <div>
          <span class="font-medium">{{ i.target_job }}</span>
          <span class="ml-2 text-xs px-2 py-0.5 rounded-full" :class="i.status === 'completed' ? 'bg-green-100 text-green-700' : 'bg-yellow-100 text-yellow-700'">{{ i.status === "completed" ? "已完成" : "进行中" }}</span>
        </div>
        <div class="flex items-center gap-3">
          <router-link v-if="i.status === 'completed'" :to="`/interview/${i.id}/report`" class="text-indigo-600 text-sm hover:underline">查看报告</router-link>
          <button @click="handleDelete(i.id)" class="text-red-400 text-sm hover:text-red-600 transition" title="删除">删除</button>
        </div>
      </div>
      <div class="text-gray-400 text-sm mt-1">{{ i.total_rounds }} 轮 · {{ i.created_at?.slice(0, 10) }}</div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue"
import api from "../api"
const interviews = ref([])
onMounted(async () => { await loadHistory() })
async function loadHistory() { const { data } = await api.getHistory(); interviews.value = data }
async function handleDelete(id) {
  if (!confirm("确定要删除这条面试记录吗？")) return
  try {
    await api.deleteInterview(id)
    interviews.value = interviews.value.filter(i => i.id !== id)
  } catch (e) { alert("删除失败") }
}
</script>
