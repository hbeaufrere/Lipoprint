# Streamlit Deployment - Quick Start

Get your gel densitometry app live in **5 minutes** ⚡

---

## 🚀 Deploy to Streamlit Cloud (Free & Easy)

### Step 1: Push Code to GitHub

```bash
# If not already on GitHub, create a repo at github.com

# Add GitHub remote
git remote add github https://github.com/YOUR_USERNAME/Lipoprint.git

# Push the branch
git push github claude/gel-densitometry-analysis-U53eI
```

### Step 2: Create Streamlit Account

1. Go to: https://streamlit.io/cloud
2. Click **Sign up**
3. Sign in with **GitHub**
4. Authorize Streamlit to access your repos

### Step 3: Deploy in 1 Click

1. Click **"New app"**
2. Select:
   - **Repository**: `YOUR_USERNAME/Lipoprint`
   - **Branch**: `claude/gel-densitometry-analysis-U53eI`
   - **Main file**: `streamlit_app.py`
3. Click **"Deploy"**

✅ **Done!** Your app is live at:
```
https://YOUR-USERNAME-lipoprint.streamlit.app
```

---

## 🧪 Test Locally First (Optional)

```bash
# Install dependencies
pip install -r requirements.txt

# Run the app
streamlit run streamlit_app.py
```

Opens at: http://localhost:8501

---

## 📱 How to Use the Web App

1. **Upload Image**: Click sidebar to upload TIF file
2. **Select Tube**: Choose which tube (1-12) to analyze
3. **Auto-Detect Bands**: Click "Auto-Detect Bands" button
4. **View Results**:
   - Interactive graph shows densitometry profile
   - Colored bands with cutoff lines
   - Band composition percentages
5. **Export Data**:
   - Download CSV for Excel
   - Download JSON for code
   - Download Summary for reports

---

## 🎯 Share Your App

Once deployed, you can:

- **Share link**: Send URL to colleagues
- **Make public**: Anyone with link can access
- **Add custom domain**: https://docs.streamlit.io/deploy/streamlit-cloud/custom-domains

---

## ⚙️ Configure App Settings

### Public vs Private

```bash
# Streamlit Cloud Dashboard → App Settings
# Share → "Public" or "Private"
```

### Custom Domain

1. Settings → **Custom Domain**
2. Point your DNS (Route53, Namecheap, etc.)
3. Verify domain

### Authentication (Pro Feature)

For private apps, users can sign in with:
- GitHub
- Google
- Email

---

## 📊 Monitor Your App

### View Logs

```bash
streamlit logs YOUR-APP-NAME
```

Or in web dashboard:
- App → **Manage** → **Logs**

### Check Health

- Auto-restart on crash
- Monitor CPU/memory in dashboard

---

## 🆘 Troubleshooting

### "Module not found" error
**Solution**: Ensure all imports are in `requirements.txt`, then redeploy

### App loads slowly
**Solution**:
- Clear cache in Settings → Cache
- Add `@st.cache_data` to expensive functions
- Check file sizes (max 200MB)

### Upload file fails
**Solution**:
- Use images < 50MB
- Check `.streamlit/config.toml` for upload limits

### Need to update code?
**Solution**:
```bash
git push github main
```
App auto-reloads within 1 minute!

---

## 💰 Pricing

| Plan | Cost | Features |
|------|------|----------|
| **Community** | FREE | 1 public app, 1GB storage |
| **Starter** | $5/mo | 3 apps, 3GB storage |
| **Growth** | $30/mo | Unlimited apps, 10GB storage |

Upgrade anytime in dashboard → Settings → Upgrade

---

## 🔐 Security Tips

1. **Never commit secrets**: Use `.env` or Secrets dashboard
2. **Rate limiting**: Implement for image uploads
3. **Validate input**: App already validates file types
4. **Use HTTPS**: Streamlit Cloud uses HTTPS by default

---

## 📈 Performance Tips

### Enable Caching
```python
@st.cache_data
def load_image(uploaded_file):
    # Expensive operation - cached after first run
    return GelImageProcessor(uploaded_file)
```

### Use Session State
```python
if 'processor' not in st.session_state:
    st.session_state.processor = None
```

### Lazy Load Heavy Modules
```python
import streamlit as st

# Only import when needed
@st.cache_resource
def get_processor():
    from image_processor import GelImageProcessor
    return GelImageProcessor
```

---

## 🎨 Customize Appearance

Edit `.streamlit/config.toml`:

```toml
[theme]
primaryColor = "#1f77b4"      # Header/buttons
backgroundColor = "#ffffff"   # Main bg
secondaryBackgroundColor = "#f0f2f6"  # Sidebar
textColor = "#262730"         # Text
font = "sans serif"           # Font
```

Restart app for changes to take effect.

---

## 📚 Useful Links

- **Streamlit Docs**: https://docs.streamlit.io
- **Community Forum**: https://discuss.streamlit.io
- **Deployment Guide**: https://docs.streamlit.io/deploy
- **GitHub Issues**: https://github.com/streamlit/streamlit/issues

---

## ✨ What's Next?

Once deployed, consider:

1. **Add more features**:
   - Batch processing for multiple images
   - Comparison between tubes
   - Export combined results

2. **Improve UI**:
   - Custom styling with CSS
   - Better layout with columns
   - Progress indicators for processing

3. **Scale up**:
   - Add database for results storage
   - User authentication
   - Advanced analytics

4. **Production ready**:
   - Add error logging
   - Monitor app usage
   - Collect user feedback

---

## 🎉 You're Live!

Your gel densitometry analyzer is now accessible from anywhere!

**Share**: https://YOUR-USERNAME-lipoprint.streamlit.app

**Questions?** Check the DEPLOYMENT.md for advanced options.
