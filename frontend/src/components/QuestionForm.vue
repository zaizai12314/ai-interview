<template>
  <div class="bg-white rounded-lg shadow-sm p-4 mb-4 border border-indigo-200">
    <input v-model="form.content" placeholder="题目内容" class="w-full border rounded-lg px-3 py-2 mb-2" />
    <input v-model="form.answer_hint" placeholder="参考答案要点（可选）" class="w-full border rounded-lg px-3 py-2 mb-2" />
    <div class="flex gap-3 mb-2">
      <input v-model="form.job_title" placeholder="岗位" class="flex-1 border rounded-lg px-3 py-2" />
      <select v-model="form.difficulty" class="border rounded-lg px-3 py-2">
        <option value="easy">简单</option>
        <option value="medium">中等</option>
        <option value="hard">困难</option>
      </select>
    </div>
    <input v-model="skillsInput" placeholder="技能标签（逗号分隔）" class="w-full border rounded-lg px-3 py-2 mb-3" />
    <div class="flex gap-2">
      <button @click="submit" class="bg-indigo-600 text-white px-4 py-2 rounded-lg">保存</button>
      <button @click="$emit('close')" class="bg-gray-200 px-4 py-2 rounded-lg">取消</button>
    </div>
  </div>
</template>
<script setup>
import { ref, reactive } from "vue"
const emit = defineEmits(["submit", "close"])
const skillsInput = ref("")
const form = reactive({ content: "", answer_hint: "", job_title: "", difficulty: "medium", skills: [] })
function submit() { form.skills = skillsInput.value.split(",").map(s => s.trim()).filter(Boolean); emit("submit", { ...form, skills: form.skills }) }
</script>
