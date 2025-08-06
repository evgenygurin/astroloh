import axios from 'axios'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 10000,
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('auth_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// Handle auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export const authApi = {
  login: async (email: string, password: string) => {
    const response = await api.post('/auth/login', { email, password })
    return response.data
  },
  
  register: async (email: string, password: string, name: string) => {
    const response = await api.post('/auth/register', { email, password, name })
    return response.data
  },
  
  getCurrentUser: async () => {
    const response = await api.get('/auth/me')
    return response.data
  },
}

export const astrologyApi = {
  getNatalChart: async (birthData: {
    date: string
    time: string
    location: string
  }) => {
    const response = await api.post('/api/astrology/natal-chart', birthData)
    return response.data
  },
  
  getHoroscope: async (sign: string, type: 'daily' | 'weekly' | 'monthly') => {
    const response = await api.get(`/api/astrology/horoscope/${sign}/${type}`)
    return response.data
  },
  
  getCompatibility: async (person1: any, person2: any) => {
    const response = await api.post('/api/astrology/compatibility', {
      person1,
      person2
    })
    return response.data
  },
}

export const lunarApi = {
  getCalendar: async (month: number, year: number) => {
    const response = await api.get(`/api/lunar/calendar/${year}/${month}`)
    return response.data
  },
  
  getCurrentPhase: async () => {
    const response = await api.get('/api/lunar/current-phase')
    return response.data
  },
}

export default api