<template>
  <div class="space-y-3">
    <div v-for="(item, idx) in items" :key="idx" class="flex items-center gap-3">
      <span class="text-sm text-gray-600 w-16 shrink-0">第{{ idx + 1 }}题</span>
      <div class="flex-1 h-3 bg-gray-200 rounded-full">
        <div class="h-3 rounded-full transition-all" :class="barColor(item.score)" :style="{ width: item.score + '%' }"></div>
      </div>
      <span class="text-sm font-bold w-10 text-right">{{ item.score }}</span>
    </div>
  </div>
</template>
<script setup>
defineProps({ items: Array })
function barColor(score) { return score >= 80 ? "bg-green-500" : score >= 60 ? "bg-yellow-500" : "bg-red-500" }
</script>
