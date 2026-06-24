<template>
  <div
    class="border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-colors"
    :class="dragging ? 'border-indigo-400 bg-indigo-50' : 'border-gray-300 hover:border-indigo-300'"
    @dragover.prevent="dragging = true"
    @dragleave="dragging = false"
    @drop.prevent="handleDrop"
  >
    <input type="file" ref="input" class="hidden" accept=".pdf,.doc,.docx,.txt" @change="handleFile" />
    <div @click="$refs.input.click()">
      <div class="text-4xl mb-3">📄</div>
      <p class="text-gray-600 text-lg">拖拽简历文件到此处，或点击上传</p>
      <p class="text-gray-400 text-sm mt-2">支持 PDF、Word、TXT 格式</p>
      <p v-if="file" class="text-indigo-600 mt-3 font-medium">{{ file.name }}</p>
    </div>
  </div>
  <button v-if="file" @click="$emit('upload', file)" class="mt-4 w-full bg-indigo-600 text-white py-3 rounded-lg hover:bg-indigo-700 transition font-medium">上传并解析</button>
</template>
<script setup>
import { ref } from "vue"
const file = ref(null)
const dragging = ref(false)
function handleDrop(e) { dragging.value = false; const f = e.dataTransfer.files[0]; if (f) file.value = f }
function handleFile(e) { const f = e.target.files[0]; if (f) file.value = f }
defineEmits(["upload"])
</script>
