import api from './api'

export const authService = {
  async register(username, email, password) {
    const response = await api.post('/auth/register', {
      username,
      email,
      password
    })
    return response.data
  },

  async login(username, password) {
    const formData = new URLSearchParams()
    formData.append('username', username)
    formData.append('password', password)

    const response = await api.post('/auth/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })
    
    const { access_token, user } = response.data
    
    localStorage.setItem('auth_token', access_token)
    localStorage.setItem('user_info', JSON.stringify(user))
    
    return { access_token, user }
  },

  async getCurrentUser() {
    const response = await api.get('/auth/me')
    return response.data
  },

  async getRegistrationConfig() {
    const response = await api.get('/auth/registration-config')
    return response.data
  },

  async updateRegistrationConfig(allowRegistration) {
    const response = await api.put('/auth/registration-config', {
      allow_registration: allowRegistration
    })
    return response.data
  },

  async getPdfConversionConfig() {
    const response = await api.get('/auth/pdf-conversion-config')
    return response.data
  },

  async updatePdfConversionConfig(allowPdfConversion) {
    const response = await api.put('/auth/pdf-conversion-config', {
      allow_pdf_conversion: allowPdfConversion
    })
    return response.data
  },

  logout() {
    localStorage.removeItem('auth_token')
    localStorage.removeItem('user_info')
  },

  isAuthenticated() {
    return !!localStorage.getItem('auth_token')
  },

  getUserInfo() {
    try {
      const userStr = localStorage.getItem('user_info')
      return userStr ? JSON.parse(userStr) : null
    } catch {
      return null
    }
  }
}
