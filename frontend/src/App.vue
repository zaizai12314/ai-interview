<template>
  <div class="min-h-screen bg-gray-50">
    <nav class="bg-white shadow-sm border-b">
      <div class="max-w-6xl mx-auto px-4 py-3 flex items-center gap-6">
        <router-link to="/" class="font-bold text-lg text-indigo-600">AI Interview</router-link>
        <router-link to="/history" class="text-gray-600 hover:text-gray-900 text-sm">面试历史</router-link>
        <router-link to="/questions" class="text-gray-600 hover:text-gray-900 text-sm">题库管理</router-link>
      </div>
    </nav>
    <router-view />
  </div>
</template>
