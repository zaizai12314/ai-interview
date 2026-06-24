<template>
  <div class="max-w-3xl mx-auto mt-10 px-4">
    <LoadingSpinner v-if="loading" text="正在解析简历..." />
    <template v-else-if="resume">
      <div class="bg-white rounded-xl shadow-sm p-6 mb-6">
        <h2 class="text-xl font-bold mb-4">简历解析结果</h2>
        <div v-if="resume.skills?.length" class="mb-4">
          <span class="text-sm text-gray-500">技能标签</span>
          <div class="flex flex-wrap gap-2 mt-1">
            <span v-for="s in resume.skills" :key="s" class="bg-indigo-100 text-indigo-700 px-3 py-1 rounded-full text-sm">{{ s }}</span>
          </div>
        </div>
        <div v-if="resume.experience?.length" class="mb-4">
          <span class="text-sm text-gray-500">工作经历</span>
          <div v-for="(exp, i) in resume.experience" :key="i" class="mt-1 text-gray-700">{{ exp.company }} - {{ exp.role }} ({{ exp.years }})</div>
        </div>
        <div v-if="resume.education?.length || resume.education?.school" class="mb-4">
          <span class="text-sm text-gray-500">教育背景</span>
          <template v-if="Array.isArray(resume.education)">
            <div v-for="(edu, i) in resume.education" :key="i" class="mt-1 text-gray-700">{{ edu.school }} · {{ edu.major }}<span v-if="edu.degree"> · {{ edu.degree }}</span><span v-if="edu.period"> ({{ edu.period }})</span></div>
          </template>
          <div v-else class="mt-1 text-gray-700">{{ resume.education.school }}<span v-if="resume.education.major"> · {{ resume.education.major }}</span></div>
        </div>
      </div>
      <LoadingSpinner v-if="!resume.parsed_at && !parseError" text="AI 正在解析简历并匹配岗位，请稍候..." />
      <div v-if="parseError" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
        <p class="text-red-700 text-sm mb-2">{{ parseError }}</p>
        <button @click="retryParse" class="bg-red-600 text-white px-4 py-2 rounded-lg text-sm hover:bg-red-700">重新解析</button>
      </div>
      <JobSelector v-if="resume.parsed_at" :jobs="jobs" @select="startInterview" />
      <div v-if="jobsError" class="mt-2 text-center">
        <p class="text-amber-600 text-sm mb-1">{{ jobsError }}</p>
        <button @click="retryJobs" class="text-indigo-600 text-sm hover:text-indigo-800 underline">重试岗位匹配</button>
      </div>
    </template>
  </div>
</template>
<script setup>
import { ref, onMounted } from "vue"
import { useRoute, useRouter } from "vue-router"
import api from "../api"
import JobSelector from "../components/JobSelector.vue"
import LoadingSpinner from "../components/LoadingSpinner.vue"
const route = useRoute()
const router = useRouter()
const resume = ref(null)
const jobs = ref([])
const loading = ref(true)
const parseError = ref("")
const jobsError = ref("")

let pollInterval = null

async function checkStatus() {
  try {
    const { data: s } = await api.getResumeStatus(route.params.id)
    if (s.status === "parsed") {
      clearInterval(pollInterval)
      const { data: r } = await api.getResume(route.params.id)
      resume.value = r
      loading.value = true
      try {
        const { data: j } = await api.getJobMatches(route.params.id)
        jobs.value = j
      } catch (e) {
        // 岗位匹配失败，保留空列表，显示重试提示
        jobsError.value = "岗位匹配暂时失败，可重试"
      }
      loading.value = false
    } else if (s.status === "error") {
      clearInterval(pollInterval)
      parseError.value = s.detail || "简历解析失败，请重试"
    }
  } catch (e) {
    // Keep polling on network errors
  }
}

async function retryJobs() {
  jobsError.value = ""
  try {
    const { data: j } = await api.getJobMatches(route.params.id)
    jobs.value = j
  } catch (e) {
    jobsError.value = "岗位匹配失败，可稍后重试"
  }
}

async function retryParse() {
  parseError.value = ""
  loading.value = true
  try {
    const { data: s } = await api.getResumeStatus(route.params.id)
    if (s.status === "parsed") {
      const { data: r } = await api.getResume(route.params.id)
      resume.value = r
      try {
        const { data: j } = await api.getJobMatches(route.params.id)
        jobs.value = j
      } catch (e) {
        jobsError.value = "岗位匹配暂时失败，可重试"
      }
    } else if (s.status === "error") {
      parseError.value = s.detail || "简历解析失败，请重试"
    } else {
      pollForCompletion()
    }
  } catch (e) {
    parseError.value = "网络错误，请重试"
  }
  loading.value = false
}

function pollForCompletion() {
  // Poll every 5s for up to 120s (24 attempts)
  let attempts = 0
  const maxAttempts = 24
  pollInterval = setInterval(async () => {
    attempts++
    if (attempts >= maxAttempts) {
      clearInterval(pollInterval)
      parseError.value = "简历解析超时，请点击重新解析"
      return
    }
    await checkStatus()
  }, 5000)
}

onMounted(async () => {
  try {
    const { data } = await api.getResume(route.params.id)
    resume.value = data
    loading.value = false
    if (data.parsed_at) {
      try {
        const { data: j } = await api.getJobMatches(route.params.id)
        jobs.value = j
      } catch (e) {
        jobsError.value = "岗位匹配暂时失败，可重试"
      }
    } else {
      pollForCompletion()
    }
  } catch (e) {
    loading.value = false
    parseError.value = "加载失败: " + (e.response?.data?.detail || e.message)
  }
})

async function startInterview(job) {
  try {
    const { data } = await api.createInterview(resume.value.id, job.title)
    router.push(`/interview/${data.id}`)
  } catch (e) { alert("创建面试失败") }
}
</script>