<template>
  <div class="max-w-4xl mx-auto mt-10 px-4">
    <div class="flex justify-between items-center mb-6">
      <h2 class="text-2xl font-bold">题库管理</h2>
      <div class="flex gap-3">
        <button @click="showForm = !showForm" class="bg-indigo-600 text-white px-4 py-2 rounded-lg hover:bg-indigo-700">{{ showForm ? "取消" : "添加题目" }}</button>
        <button @click="handleReEmbed" class="bg-gray-600 text-white px-4 py-2 rounded-lg hover:bg-gray-700">重新向量化</button>
      </div>
    </div>
    <QuestionForm v-if="showForm" @submit="handleCreate" @close="showForm = false" />
    <div class="bg-white rounded-lg shadow-sm divide-y">
      <div v-for="q in questions" :key="q.id" class="p-4">
        <div class="flex items-start gap-3">
          <span class="text-xs px-2 py-0.5 rounded-full shrink-0" :class="q.difficulty === 'easy' ? 'bg-green-100 text-green-700' : q.difficulty === 'hard' ? 'bg-red-100 text-red-700' : 'bg-yellow-100 text-yellow-700'">{{ q.difficulty }}</span>
          <div>
            <p class="font-medium">{{ q.content }}</p>
            <div class="flex gap-2 mt-1">
              <span class="text-xs text-gray-400">{{ q.job_title }}</span>
              <span v-for="s in (q.skills || [])" :key="s" class="text-xs bg-gray-100 px-2 rounded">{{ s }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue"
import api from "../api"
import QuestionForm from "../components/QuestionForm.vue"
const questions = ref([])
const showForm = ref(false)
onMounted(async () => { const { data } = await api.listQuestions({ limit: 50 }); questions.value = data })
async function handleCreate(formData) { await api.createQuestion(formData); showForm.value = false; const { data } = await api.listQuestions({ limit: 50 }); questions.value = data }
async function handleReEmbed() { await api.reEmbed(); alert("向量化任务已提交") }
</script>
