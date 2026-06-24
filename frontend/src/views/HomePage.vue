<template>
  <div class="max-w-2xl mx-auto mt-20 px-4">
    <h1 class="text-3xl font-bold text-center mb-2">AI 智能模拟面试</h1>
    <p class="text-gray-500 text-center mb-10">上传简历，AI 将为您匹配岗位并进行模拟面试</p>
    <FileUpload @upload="handleUpload" />
    <p v-if="loading" class="text-center mt-4 text-indigo-600">正在上传...</p>
  </div>
</template>
<script setup>
import { ref } from "vue"
import { useRouter } from "vue-router"
import api from "../api"
import FileUpload from "../components/FileUpload.vue"
const router = useRouter()
const loading = ref(false)
async function handleUpload(file) {
  loading.value = true
  try { const { data } = await api.uploadResume(file); router.push(`/resume/${data.id}`) }
  catch (e) { alert("上传失败: " + (e.response?.data?.detail || e.message)) }
  finally { loading.value = false }
}
</script>
