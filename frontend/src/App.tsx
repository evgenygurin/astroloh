import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import HomePage from './pages/HomePage'
import LoginPage from './pages/LoginPage'
import RegisterPage from './pages/RegisterPage'
import ProfilePage from './pages/ProfilePage'
import NatalChartPage from './pages/NatalChartPage'
import HoroscopePage from './pages/HoroscopePage'
import LunarCalendarPage from './pages/LunarCalendarPage'
import CompatibilityPage from './pages/CompatibilityPage'
import { AuthProvider } from './contexts/AuthContext'

function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-dark-900 text-mystical-silver">
        {/* Floating particles background */}
        <div className="floating-particles" />
        
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<HomePage />} />
            <Route path="login" element={<LoginPage />} />
            <Route path="register" element={<RegisterPage />} />
            <Route path="profile" element={<ProfilePage />} />
            <Route path="natal-chart" element={<NatalChartPage />} />
            <Route path="horoscope" element={<HoroscopePage />} />
            <Route path="lunar-calendar" element={<LunarCalendarPage />} />
            <Route path="compatibility" element={<CompatibilityPage />} />
          </Route>
        </Routes>
      </div>
    </AuthProvider>
  )
}

export default App