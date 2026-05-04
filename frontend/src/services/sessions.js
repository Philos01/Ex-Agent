import api from './api'

export const sessionService = {
  async getSessions() {
    const response = await api.get('/sessions')
    return response.data
  },

  async createSession(sessionName) {
    const response = await api.post('/sessions', { session_name: sessionName })
    return response.data
  },

  async getSession(sessionId) {
    const response = await api.get(`/sessions/${sessionId}`)
    return response.data
  },

  async getSessionContext(sessionId, limit = 20) {
    const response = await api.get(`/sessions/${sessionId}/context`, {
      params: { limit }
    })
    return response.data
  },

  async addMessage(sessionId, role, content, sources = null, reactSteps = null) {
    // 确保sources是对象或null，避免发送undefined
    const sourcesData = sources || null
    const data = {
      role,
      content,
      sources: sourcesData
    }
    if (reactSteps) {
      data.react_steps = reactSteps
    }
    const response = await api.post(`/sessions/${sessionId}/messages`, data)
    return response.data
  },

  async deleteSession(sessionId) {
    const response = await api.delete(`/sessions/${sessionId}`)
    return response.data
  }
}
