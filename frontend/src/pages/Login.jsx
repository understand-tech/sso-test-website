import { useState } from 'react'
import './Login.css'

const API_BASE_URL = 'https://backend-smoky-delta.vercel.app'

function Login() {
  const [loading, setLoading] = useState(false)

  const handleLogin = async () => {
    setLoading(true)
    try {
      const response = await fetch(`${API_BASE_URL}/auth/login`, {
        credentials: 'include',
      })
      const data = await response.json()
      
      // Store state in localStorage for verification after OAuth redirect
      // This is needed because Vercel serverless functions are stateless
      if (data.state) {
        localStorage.setItem('oauth_state', data.state)
      }
      
      // Redirect to Microsoft OAuth
      window.location.href = data.auth_url
    } catch (error) {
      console.error('Login failed:', error)
      setLoading(false)
    }
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <div className="login-header">
          <h1>Welcome</h1>
          <p>Sign in to continue to Widget SSO Demo</p>
        </div>
        
        <div className="login-content">
          <button
            className="microsoft-button"
            onClick={handleLogin}
            disabled={loading}
          >
            <svg className="microsoft-icon" viewBox="0 0 21 21">
              <rect x="1" y="1" width="9" height="9" fill="#f25022"/>
              <rect x="1" y="11" width="9" height="9" fill="#00a4ef"/>
              <rect x="11" y="1" width="9" height="9" fill="#7fba00"/>
              <rect x="11" y="11" width="9" height="9" fill="#ffb900"/>
            </svg>
            {loading ? 'Signing in...' : 'Sign in with Microsoft'}
          </button>
        </div>
        
        <div className="login-footer">
          <p>This is a demo parent website for widget SSO integration</p>
        </div>
      </div>
    </div>
  )
}

export default Login

