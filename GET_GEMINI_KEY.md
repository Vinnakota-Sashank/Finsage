# 🔑 How to Get Your Gemini API Key (5 Minutes)

## Step-by-Step Visual Guide

### Step 1: Open Google AI Studio
```
🌐 Visit: https://aistudio.google.com/app/apikey
```

### Step 2: Sign In
- Use your Google account (Gmail)
- If you don't have one, create a free Google account first

### Step 3: Create API Key
```
Click the blue button: "Create API Key"
```

You'll see options:
- **Create API key in new project** ← Choose this if first time
- **Create API key in existing project** ← If you already have a project

### Step 4: Copy Your Key
```
Your key will look like:
AIzaSyDXqVGm8RN6IjlNfsLdJ5kx9jSlRBp6wigfDr7fTgLjzgiKEFmKdePw
         ↑
    Starts with "AIzaSy"
```

**Important**: 
- Copy the ENTIRE key
- Don't share it publicly
- Don't commit it to GitHub (it's in .env which is .gitignored)

### Step 5: Add to Your Project
```bash
# Open backend/.env file
# Find this line:
GEMINI_API_KEY=AIzaSyDXqVGm8RN6IjlNfsLdJ5kx9jSlRBp6wigfDr7fTgLjzgiKEFmKdePw

# Replace with YOUR key:
GEMINI_API_KEY=AIzaSy_YOUR_ACTUAL_KEY_HERE
```

### Step 6: Restart Backend
```bash
# Stop current server (Ctrl+C in terminal)
# Then restart:
cd backend
python -m uvicorn app.main:app --reload
```

### Step 7: Verify It Works
```bash
# In a new terminal:
curl http://localhost:8000/api/v1/chat/health
```

**Success looks like**:
```json
{
  "ready": true,
  "gemini_configured": true,  ← Should be true
  "mode": "gemini",            ← Should say "gemini"
  "function_calling_enabled": true,
  "tool_chain_size": 5
}
```

**Failure looks like**:
```json
{
  "ready": true,
  "gemini_configured": false,  ← Still false
  "mode": "rule-based",        ← Falls back to rules
  "function_calling_enabled": false,
  "tool_chain_size": 5
}
```

---

## Troubleshooting

### Problem: "gemini_configured": false

**Check 1**: Is the key in `.env` file?
```bash
cd backend
cat .env | grep GEMINI
# Should show: GEMINI_API_KEY=AIzaSy...
```

**Check 2**: Did you restart the server?
```bash
# Stop server (Ctrl+C)
# Start again:
python -m uvicorn app.main:app --reload
```

**Check 3**: Is the key format correct?
- Must start with `AIzaSy`
- No spaces before or after
- All on one line

### Problem: API Key Invalid Error

**Solution 1**: Create a new key
- Go back to https://aistudio.google.com/app/apikey
- Delete old key
- Create new key
- Copy and paste again

**Solution 2**: Check API quota
- Free tier: 60 requests per minute
- If you hit limit, wait 1 minute and try again

### Problem: Can't Access Google AI Studio

**Solution**: 
- Google AI Studio is available in most countries
- If blocked, you can use a VPN
- Or ask a teammate to create a key and share it securely

---

## Free Tier Limits

✅ **Free Forever**:
- 60 requests per minute
- 1,500 requests per day
- Perfect for hackathon demo

✅ **No Credit Card Required**:
- Just need a Google account
- No billing setup needed

✅ **Enough for Demo**:
- Each chat message = 1-2 requests
- You can do 1,500 chat messages per day
- More than enough for judging + testing

---

## Security Best Practices

### ✅ DO:
- Keep key in `.env` file (already .gitignored)
- Use environment variables
- Rotate key after hackathon if shared

### ❌ DON'T:
- Commit key to GitHub
- Share key publicly
- Hardcode key in source files
- Post key in Discord/Slack

---

## Quick Reference

**Get Key**: https://aistudio.google.com/app/apikey  
**File Location**: `backend/.env`  
**Variable Name**: `GEMINI_API_KEY`  
**Format**: Starts with `AIzaSy`  
**Test Endpoint**: `GET /api/v1/chat/health`  

**Time Required**: 5 minutes  
**Cost**: Free forever  
**Quota**: 60 req/min, 1,500 req/day  

---

## What Happens After You Add the Key?

### Before (Without Key):
- Chat uses rule-based intent detection
- No AI enhancement
- Still works, but less intelligent

### After (With Key):
- Chat uses Gemini function calling
- AI selects best tool for each query
- Responses are polished by AI
- More natural conversation flow

### Example Difference:

**Without Gemini**:
```
User: "How much food?"
Bot: "You spent ₹14,800 on food this month."
```

**With Gemini**:
```
User: "How much food?"
Bot: "This month, you've spent ₹14,800 on food across 
     delivery (₹8,200), dining out (₹4,100), and 
     groceries (₹2,500). That's 18% of your total spending."
```

---

## Ready to Test?

Once you have your key:

1. ✅ Add to `backend/.env`
2. ✅ Restart backend server
3. ✅ Test health endpoint
4. ✅ Try a chat query
5. ✅ Proceed with demo prep

**Next**: See `QUICK_FIX_GUIDE.md` for testing instructions
