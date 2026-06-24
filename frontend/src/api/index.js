import axios from "axios"

const api = axios.create({ baseURL: "/api", timeout: 30000 })

export default {
  uploadResume(file) {
    const form = new FormData()
    form.append("file", file)
    return api.post("/resume/upload", form)
  },
  getResume(id) { return api.get(`/resume/${id}`) },
  getResumeStatus(id) { return api.get(`/resume/${id}/status`) },
  getJobMatches(id) { return api.get(`/resume/${id}/jobs`) },
  createInterview(resumeId, targetJob) {
    return api.post("/interview/create", { resume_id: resumeId, target_job: targetJob })
  },
  getInterview(id) { return api.get(`/interview/${id}`) },
  submitAnswer(id, answer) { return api.post(`/interview/${id}/answer`, { answer }) },
  getReport(id) { return api.get(`/interview/${id}/report`) },
  getHistory() { return api.get("/interview/history/list") },
  deleteInterview(id) { return api.delete(`/interview/${id}`) },
}
