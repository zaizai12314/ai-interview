<template>
  <div class="fixed inset-0 bg-black/30 flex items-center justify-center z-50" @click.self="$emit('close')">
    <div class="bg-white rounded-2xl shadow-xl p-8 max-w-md w-full mx-4">
      <div class="text-center mb-4"><div class="text-5xl font-bold" :class="scoreColor">{{ score }}</div><div class="text-gray-500 mt-1">分</div></div>
      <p class="text-gray-600 text-center mb-6">{{ feedback }}</p>
      <button @click="$emit('close')" class="w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 transition font-medium">{{ nextAction === "finish" ? "查看报告" : "下一题" }}</button>
    </div>
  </div>
</template>
<script setup>
import { computed } from "vue"
const props = defineProps({ score: Number, feedback: String, nextAction: String })
defineEmits(["close"])
const scoreColor = computed(() => props.score >= 80 ? "text-green-500" : props.score >= 60 ? "text-yellow-500" : "text-red-500")
</script>
