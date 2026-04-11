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

  async addMessage(sessionId, role, content, sources = null) {
    // 确保sources是对象或null，避免发送undefined
    const sourcesData = sources || null
    const response = await api.post(`/sessions/${sessionId}/messages`, {
      role,
      content,
      sources: sourcesData
    })
    return response.data
  },

  async deleteSession(sessionId) {
    const response = await api.delete(`/sessions/${sessionId}`)
    return response.data
  }
}
