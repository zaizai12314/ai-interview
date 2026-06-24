import { createRouter, createWebHistory } from "vue-router"

const routes = [
  { path: "/", name: "Home", component: () => import("../views/HomePage.vue") },
  { path: "/resume/:id", name: "Resume", component: () => import("../views/ResumePage.vue") },
  { path: "/interview/:id", name: "Interview", component: () => import("../views/InterviewPage.vue") },
  { path: "/interview/:id/report", name: "Report", component: () => import("../views/ReportPage.vue") },
  { path: "/history", name: "History", component: () => import("../views/HistoryPage.vue") },
]

export default createRouter({ history: createWebHistory(), routes })
