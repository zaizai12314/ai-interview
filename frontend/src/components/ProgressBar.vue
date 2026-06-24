<template>
  <div class="flex-1 h-2 bg-gray-200 rounded-full">
    <div class="h-2 bg-indigo-600 rounded-full transition-all duration-500" :style="{ width: (progress * 100) + '%' }"></div>
  </div>
</template>
<script setup>
defineProps({ progress: { type: Number, default: 0 } })
</script>
