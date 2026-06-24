<template>
  <div class="bg-white rounded-xl shadow-sm p-6">
    <div class="flex items-center gap-3 mb-4">
      <span class="bg-indigo-100 text-indigo-700 text-sm px-3 py-1 rounded-full">第 {{ round }} 题</span>
      <ProgressBar :progress="progress" />
    </div>
    <div class="text-lg font-medium mb-6 leading-relaxed">{{ question }}</div>
    <textarea v-model="answer" rows="5" class="w-full border rounded-lg px-4 py-3 focus:ring-2 focus:ring-indigo-300 focus:border-indigo-400 outline-none resize-none" placeholder="在此输入您的回答..." :disabled="submitting"></textarea>
    <div class="flex justify-between items-center mt-4">
      <span class="text-gray-400 text-sm">{{ answer.length }} 字</span>
      <button @click="$emit('submit', answer)" :disabled="!answer.trim() || submitting" class="bg-indigo-600 text-white px-6 py-2 rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition">{{ submitting ? "提交中..." : "提交回答" }}</button>
    </div>
  </div>
</template>
<script setup>
import { ref } from "vue"
import ProgressBar from "./ProgressBar.vue"
defineProps({ question: String, round: Number, progress: Number, submitting: Boolean })
defineEmits(["submit"])
const answer = ref("")
</script>
