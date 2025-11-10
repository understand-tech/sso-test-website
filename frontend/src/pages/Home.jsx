import { useRef, useEffect, useState } from 'react'
import { API_BASE_URL } from '../App'
import './Home.css'

// Widget configuration
const WIDGET_URL = 'https://staging.understand.tech/?api_key=07ee4d545ea51e78845052933880ed34c8f61f8033892dfe65bf2371015caec9&model_id=bimbab'
const MODEL_ID = 'bimbab'

function Home({ user, onLogout }) {
  const iframeRef = useRef(null)
  const [widgetReady, setWidgetReady] = useState(false)
  const [widgetError, setWidgetError] = useState(null)
  const ottSentRef = useRef(false) // Track if OTT was already sent

  useEffect(() => {
    const fetchAndSendOTT = async () => {
      // Prevent duplicate OTT requests
      if (ottSentRef.current) {
        return
      }
      
      ottSentRef.current = true // Mark as in-progress
      console.log('🚀 [FRONTEND] Starting Widget OTT Exchange Flow')
      
      try {
        // Fetch OTT from parent backend
        const requestBody = {
          model_id: MODEL_ID,
          origin: window.location.origin,
        }
        
        console.log('📤 [FRONTEND] Requesting OTT from backend')
        
        const response = await fetch(`${API_BASE_URL}/widget/get-ott`, {
          method: 'POST',
          credentials: 'include',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(requestBody),
        })

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Failed to get OTT' }))
          console.error('❌ [FRONTEND] Failed to get OTT:', errorData.detail)
          throw new Error(errorData.detail || 'Failed to get OTT')
        }

        const data = await response.json()
        const ottPreview = data.ott?.substring(0, 30) + '...' || 'None'
        
        console.log('✅ [FRONTEND] OTT received successfully')
        
        // Send OTT to iframe via postMessage
        if (iframeRef.current?.contentWindow) {
          const message = { type: 'UT_OTT', ott: data.ott }
          const targetOrigin = new URL(WIDGET_URL).origin
          
          console.log('\n📨 [FRONTEND] Sending OTT to widget iframe')
          
          iframeRef.current.contentWindow.postMessage(message, targetOrigin)
          
          console.log('✅ [FRONTEND] OTT sent to iframe via postMessage')
          
          setWidgetReady(true)
        } else {
          console.error('❌ [FRONTEND] Iframe contentWindow not available')
          console.log('='.repeat(80) + '\n')
          throw new Error('Iframe not ready')
        }
      } catch (error) {
        console.error('❌ [FRONTEND] OTT exchange flow failed:', error)
        console.log('='.repeat(80) + '\n')
        setWidgetError(error.message)
        ottSentRef.current = false
      }
    }

    // Wait for iframe to load before sending OTT
    const iframe = iframeRef.current
    if (iframe) {
      
      iframe.onload = () => {
        console.log('✅ [FRONTEND] Widget iframe loaded successfully')
        console.log('⏱️ [FRONTEND] Waiting 500ms for iframe to initialize...')
        
        setTimeout(() => {
          console.log('▶️ [FRONTEND] Starting OTT fetch...')
          fetchAndSendOTT()
        }, 500)
      }
    } else {
      console.warn('⚠️ [FRONTEND] Iframe ref not available yet')
    }

    // Optional: Listen for UT_READY message from iframe
    const handleMessage = (event) => {
      const eventOrigin = new URL(WIDGET_URL).origin
      
      // Validate origin for security
      if (event.origin !== eventOrigin) {
        return
      }

      console.log(`📬 [FRONTEND] Received message from widget iframe:`, event.data)

      if (event.data.type === 'UT_READY') {
        console.log('✅ [FRONTEND] Widget sent UT_READY signal')
        // Iframe is ready, send OTT if we haven't already
        if (!ottSentRef.current) {
          console.log('🔄 [FRONTEND] Widget ready but OTT not sent yet, fetching OTT...')
          fetchAndSendOTT()
        } else {
          console.log('ℹ️ [FRONTEND] OTT already sent, ignoring UT_READY')
        }
      }
    }

    console.log('👂 [FRONTEND] Setting up message listener for widget communication')
    window.addEventListener('message', handleMessage)

    return () => {
      console.log('🧹 [FRONTEND] Cleaning up widget listeners')
      window.removeEventListener('message', handleMessage)
      if (iframe) {
        iframe.onload = null
      }
    }
  }, []) // Empty dependency array - only run once on mount

  // Log when component mounts
  useEffect(() => {
    console.log('\n' + '='.repeat(80))
    console.log('🏠 [FRONTEND] Home component mounted')
    console.log(`   - User: ${user?.name} (${user?.email})`)
    console.log(`   - Widget URL: ${WIDGET_URL}`)
    console.log(`   - Model ID: ${MODEL_ID}`)
    console.log('='.repeat(80) + '\n')
  }, [])

  return (
    <div className="home-container">
      <nav className="navbar">
        <div className="nav-content">
          <h1 className="nav-title">Widget SSO Demo</h1>
          <div className="nav-user">
            <span className="user-name">{user.name}</span>
            <span className="user-email">{user.email}</span>
            <button className="logout-button" onClick={onLogout}>
              Logout
            </button>
          </div>
        </div>
      </nav>

      <main className="main-content">
        <div className="welcome-section">
          <h2>Welcome, {user.name?.split(' ')[0]}! 👋</h2>
          <p className="subtitle">
            You're successfully authenticated via Microsoft SSO
          </p>
        </div>

        <div className="content-grid">
          <div className="info-card">
            <h3>Hello World!</h3>
            <p>
              This is your parent website dashboard. The widget iframe will be
              embedded in the section below once configured.
            </p>
          </div>

          <div className="widget-section">
            <h3>Widget Area</h3>
            <div className="widget-placeholder">
              {widgetError && (
                <div className="widget-error">
                  <p>⚠️ Widget Error: {widgetError}</p>
                </div>
              )}
              
              <iframe 
                ref={iframeRef}
                src={WIDGET_URL}
                width="100%" 
                height="600px" 
                title="Chat Widget"
                className="widget-iframe"
                allow="clipboard-read; clipboard-write"
              />

              {!widgetReady && !widgetError && (
                <div className="widget-loading">
                  <p>Loading widget...</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </main>
    </div>
  )
}

export default Home

