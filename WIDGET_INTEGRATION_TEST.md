# Widget OTT Exchange Integration Test Guide

This guide helps you test the complete widget OTT (One-Time Token) exchange flow.

## Prerequisites

Before testing, ensure you have:

1. **Backend `.env` configured** with:
   - `WIDGET_API_KEY`: Your team's widget API key from Understand Tech
   - `UT_API_BASE_URL`: The UT API endpoint (e.g., `https://staging.understand.tech`)
   - `MICROSOFT_CLIENT_ID`, `MICROSOFT_CLIENT_SECRET`, `MICROSOFT_TENANT_ID`: For SSO
   - `SESSION_SECRET` (and optionally `JWT_SECRET` if you want a dedicated signing key): For session management
   - `FRONTEND_URL`: Your frontend URL (e.g., `http://localhost:5173`)

2. **Frontend configuration** in `src/pages/Home.jsx`:
   - `WIDGET_URL`: Set to your widget domain (default: `https://app.understand.tech`)
   - `MODEL_ID`: Your assistant's model ID (default: `Ydol Chatbot`)

3. **Both servers running**:
   - Backend: `http://localhost:8000`
   - Frontend: `http://localhost:5173`

## Test Flow

### Step 1: Parent Site Authentication

1. Open browser to `http://localhost:5173`
2. Click "Sign in with Microsoft"
3. Complete Microsoft OAuth login
4. Verify you're redirected to `/home`
5. Verify your name and email display correctly
6. Open DevTools → Application → Cookies and confirm an `auth_token` cookie exists for the parent site origin

**Expected Result**: ✅ User authenticated on parent site with Microsoft SSO

### Step 2: OTT Request (Backend)

Monitor backend logs for the OTT request:

```
POST /widget/get-ott
```

**What happens**:
- Frontend sends POST request with `model_id` and `origin`
- Backend validates auth token (JWT cookie)
- Backend calls UT API: `POST /widget/ott` with Authorization header
- UT API validates Widget API Key, team, assistant, origin
- UT API returns signed OTT with 60-second expiry

**Expected Result**: ✅ Backend receives OTT from UT API

**Debug**: Check browser DevTools Network tab:
- Request to `/widget/get-ott` should return 200
- Response body should contain: `{ "ott": "...", "expires_in": 60 }`

### Step 3: PostMessage to Iframe (Frontend)

Check browser console for logs:

```javascript
console.log('Sending OTT to iframe:', { type: 'UT_OTT', ott })
```

**What happens**:
- Frontend receives OTT from backend
- Frontend waits for iframe to load
- Frontend calls `postMessage()` with `{ type: 'UT_OTT', ott }`
- Message is sent to widget iframe with targetOrigin = WIDGET_URL

**Expected Result**: ✅ OTT sent to iframe via postMessage

**Debug**: 
- Check for "Loading widget..." message (should disappear after OTT is sent)
- Check for any error messages displayed in the widget area

### Step 4: OTT Exchange (Widget Iframe - UT Side)

The widget iframe (Understand Tech's code) should:

1. Listen for postMessage with `type: 'UT_OTT'`
2. Call UT API: `POST /widget/exchange-ott` with `{ ott }`
3. UT API validates:
   - HMAC signature
   - OTT not expired
   - OTT not used before (replay protection)
   - Origin matches request Origin header
   - Team and assistant still valid
4. UT API sets HttpOnly session cookie (`ut_session`)
5. Widget is now authenticated

**Expected Result**: ✅ Widget iframe has session cookie and is authenticated

**Debug**:
- Open browser DevTools → Application → Cookies
- Look for `ut_session` cookie under widget domain
- Should be `HttpOnly`, `Secure` (if HTTPS), `SameSite=None`, `Partitioned`

### Step 5: Widget Ready for Chat

The widget should now:
- Display chat interface (not login button)
- Accept user messages
- Make authenticated API calls with session cookie

**Expected Result**: ✅ Widget fully functional for chat

## Common Issues & Troubleshooting

### Issue: "Failed to get OTT" error

**Possible Causes**:
1. WIDGET_API_KEY not set or incorrect
2. UT_API_BASE_URL not set or incorrect
3. model_id doesn't exist or doesn't belong to the team
4. Origin not in team's allowed origins list

**Debug Steps**:
- Check backend logs for detailed error from UT API
- Verify WIDGET_API_KEY matches team's key in UT database
- Ensure assistant requires SSO (`sso_enabled: true`)
- Check UT API logs for the `/widget/ott` request

### Issue: OTT not reaching iframe

**Possible Causes**:
1. WIDGET_URL doesn't match iframe's actual origin
2. Iframe not loaded before postMessage sent
3. Widget iframe not listening for messages

**Debug Steps**:
- Check browser console for CORS or postMessage errors
- Verify `iframeRef.current.contentWindow` is not null
- Add console.log in postMessage call to confirm execution
- Verify widget iframe has message listener set up

### Issue: OTT exchange fails (widget iframe)

**Possible Causes**:
1. OTT expired (>60 seconds passed)
2. OTT already used (replay attack protection)
3. Origin mismatch between OTT and request
4. Team or assistant no longer valid

**Debug Steps**:
- Check UT API logs for `/widget/exchange-ott` errors
- Verify Origin header matches origin in OTT payload
- Check if OTT jti exists in `ott_used` collection (replay)
- Ensure less than 60 seconds between issue and exchange

### Issue: Widget not authenticated after exchange

**Possible Causes**:
1. Session cookie not set correctly
2. Cookie blocked by browser (3rd party cookie restrictions)
3. SameSite/Partitioned attributes not compatible with browser

**Debug Steps**:
- Check DevTools → Application → Cookies for `ut_session`
- Try in Chrome/Edge with 3rd party cookies enabled
- Verify cookie has `Partitioned` attribute for iframe context
- Check for cookie warnings in browser console

## Testing Checklist

- [ ] Backend starts without errors
- [ ] Frontend starts without errors
- [ ] Microsoft SSO login works
- [ ] User redirected to /home after login
- [ ] Widget iframe loads (visible in page)
- [ ] Backend `/widget/get-ott` returns 200 with OTT
- [ ] postMessage sent to iframe (check console)
- [ ] No errors in browser console
- [ ] `ut_session` cookie appears in DevTools
- [ ] Widget shows chat interface (not login)
- [ ] Widget accepts and responds to messages

## Security Verification

Verify these security measures are working:

1. **Widget API Key never exposed**:
   - Check browser DevTools → Network tab
   - Widget API Key should NEVER appear in any request/response
   - Only appears in backend code and .env

2. **OTT is single-use**:
   - Try to reuse an OTT (replay attack)
   - Second use should fail with error

3. **OTT expires**:
   - Wait 61+ seconds after OTT issued
   - Attempt to exchange expired OTT
   - Should fail with expiry error

4. **Origin validation**:
   - Try to use OTT from different origin
   - Should fail with origin mismatch error

5. **Session cookie is HttpOnly**:
   - Try to access `ut_session` cookie via JavaScript
   - Should be inaccessible (undefined)

## Success Criteria

The integration is successful when:

1. ✅ User can login via Microsoft SSO
2. ✅ Widget iframe loads on home page
3. ✅ OTT is automatically fetched and sent to iframe
4. ✅ Widget receives OTT and exchanges it for session cookie
5. ✅ Widget displays chat interface (authenticated)
6. ✅ Widget can send/receive chat messages
7. ✅ No errors in browser console or backend logs
8. ✅ All security measures verified

## Performance Notes

- OTT exchange should complete in < 2 seconds
- Widget should be ready for chat within 3 seconds of page load
- No visible delays or loading states after initial page load

## Next Steps After Successful Testing

1. Test with different assistants/model IDs
2. Test origin allowlist restrictions
3. Test session expiry and refresh flows
4. Deploy to staging environment
5. Test with production UT API endpoint
6. Conduct security audit
7. Load test with multiple concurrent users

