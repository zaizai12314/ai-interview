<template>
  <div class="bg-white rounded-xl shadow-sm p-6">
    <h3 class="text-lg font-bold mb-4">推荐岗位</h3>
    <div class="space-y-3">
      <div v-for="job in jobs" :key="job.title" class="border rounded-lg p-4 cursor-pointer hover:border-indigo-400 hover:bg-indigo-50 transition" @click="$emit('select', job)">
        <div class="flex justify-between items-center">
          <span class="font-medium text-lg">{{ job.title }}</span>
          <span class="text-indigo-600 font-bold">{{ job.match_score }}% 匹配</span>
        </div>
        <p class="text-gray-500 text-sm mt-1">{{ job.reason }}</p>
      </div>
    </div>
  </div>
</template>
<script setup>
defineProps({ jobs: Array })
defineEmits(["select"])
</script>
