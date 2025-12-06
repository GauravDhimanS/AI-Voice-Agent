# 🎤 Fix Microphone Access Issue

## 🔴 The Problem

```
Microphone Error
Could not access microphone: Cannot read properties of undefined (reading 'getUserMedia')
```

**Root Cause:** Browsers block microphone access on HTTP (non-HTTPS) for security, except on `localhost`.

---

## ✅ **SOLUTION 1: Use Localhost (Easiest)**

### On the same computer where the server is running:

**Instead of:**
```
http://192.168.1.42:8000/web/app.html  ❌
```

**Use:**
```
http://localhost:8000/web/app.html  ✅
```

This works immediately, no setup needed!

---

## ✅ **SOLUTION 2: Enable HTTPS for LAN Access**

If you want friends/other devices to access it, you need HTTPS.

### Step 1: Create SSL Certificate

**Run this:**
```bash
create_ssl_powershell.bat
```

This creates `cert.pfx` using PowerShell (no extra tools needed).

### Step 2: Stop Current Server

In the terminal where the server is running, press `Ctrl+C`

### Step 3: Start Server with HTTPS

```bash
uvicorn server:app --host 0.0.0.0 --port 8000 --ssl-keyfile cert.pfx --ssl-certfile cert.pfx --ssl-keyfile-password password
```

### Step 4: Access via HTTPS

```
https://192.168.1.42:8000/web/app.html
```

**Note:** Browser will show security warning. Click:
1. "Advanced"
2. "Proceed to 192.168.1.42 (unsafe)"

This is safe - it's your own certificate!

---

## ✅ **SOLUTION 3: Chrome Insecure Origins Flag (Development Only)**

**For testing only** - allows HTTP microphone on specific IPs.

### Step 1: Open Chrome Flags

In Chrome, go to:
```
chrome://flags/#unsafely-treat-insecure-origin-as-secure
```

### Step 2: Add Your IP

In the text box, enter:
```
http://192.168.1.42:8000
```

### Step 3: Enable and Restart

1. Click "Enable"
2. Click "Relaunch"

Now `http://192.168.1.42:8000/web/app.html` will work!

**Warning:** This is a development workaround. For production, use HTTPS.

---

## 📊 Comparison

| Method | Effort | Security | Works for Others? |
|--------|--------|----------|-------------------|
| Localhost | None | ✅ Safe | ❌ No |
| HTTPS | Low | ✅ Safe | ✅ Yes |
| Chrome Flag | Low | ⚠️ Dev only | ❌ No |

---

## 🚀 **Recommended Approach:**

### For **local testing** (just you):
```bash
# Use localhost
http://localhost:8000/web/app.html
```

### For **sharing with friends**:
```bash
# 1. Create certificate
create_ssl_powershell.bat

# 2. Start with HTTPS
uvicorn server:app --host 0.0.0.0 --port 8000 --ssl-keyfile cert.pfx --ssl-certfile cert.pfx --ssl-keyfile-password password

# 3. Share HTTPS link
https://192.168.1.42:8000/web/app.html
```

---

## 🐛 Troubleshooting

### Certificate creation failed?
Try the PowerShell method:
```bash
create_ssl_powershell.bat
```

### Still can't access microphone?
1. Check browser permissions (click microphone icon in address bar)
2. Make sure you clicked "Allow" when prompted
3. Try a different browser (Chrome/Edge recommended)

### HTTPS not working?
Make sure you're using `https://` (not `http://`) in the URL.

---

## 💡 Summary

**The microphone error is a browser security feature, not a bug!**

**Quick fix:** Use `http://localhost:8000/web/app.html`

**For LAN:** Use HTTPS with self-signed cert

Your voice agent code is working perfectly - it's just the browser being protective! 🎉
