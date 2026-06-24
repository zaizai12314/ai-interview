<template>
  <div class="text-center py-12">
    <div class="animate-spin w-10 h-10 border-4 border-indigo-200 border-t-indigo-600 rounded-full mx-auto"></div>
    <p class="text-gray-500 mt-4">{{ text }}</p>
  </div>
</template>
<script setup>
defineProps({ text: { type: String, default: "加载中..." } })
</script>
