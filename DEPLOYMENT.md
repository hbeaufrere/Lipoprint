# Deployment Guide - Gel Densitometry Analysis

## Quick Start: Deploy to Streamlit Cloud (Free)

### Option 1: Streamlit Cloud (Recommended - Fastest)

**Time to deploy: 5 minutes**

#### Step 1: Push to GitHub

```bash
cd /home/user/Lipoprint
git remote add github https://github.com/YOUR_USERNAME/Lipoprint.git
git push github claude/gel-densitometry-analysis-U53eI
```

#### Step 2: Create Streamlit Account
1. Go to https://streamlit.io/cloud
2. Click "Sign up"
3. Sign in with GitHub
4. Authorize Streamlit to access your repos

#### Step 3: Deploy App
1. Click "New app"
2. Select repository: `YOUR_USERNAME/Lipoprint`
3. Branch: `claude/gel-densitometry-analysis-U53eI`
4. Main file path: `streamlit_app.py`
5. Click "Deploy"

✅ **Done!** Your app is live at:
```
https://YOUR-USERNAME-lipoprint.streamlit.app
```

---

### Option 2: Run Locally (For Testing)

```bash
# Install dependencies
pip install -r requirements.txt

# Run Streamlit app
streamlit run streamlit_app.py
```

Opens automatically at: `http://localhost:8501`

---

### Option 3: Docker Deployment

#### Build Docker Image

```dockerfile
# Create Dockerfile
FROM python:3.9-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Expose port
EXPOSE 8501

# Health check
HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

# Run app
CMD ["streamlit", "run", "streamlit_app.py", "--server.port=8501", "--server.address=0.0.0.0"]
```

Build and run:
```bash
docker build -t gel-densitometry .
docker run -p 8501:8501 gel-densitometry
```

---

### Option 4: Cloud Platform Deployment

#### AWS EC2

```bash
# 1. Launch EC2 instance (Ubuntu 22.04)
# 2. SSH into instance
ssh -i your-key.pem ubuntu@your-instance-ip

# 3. Install Python and dependencies
sudo apt update
sudo apt install python3-pip python3-venv

# 4. Clone repository
git clone https://github.com/YOUR_USERNAME/Lipoprint.git
cd Lipoprint

# 5. Create virtual environment
python3 -m venv venv
source venv/bin/activate

# 6. Install dependencies
pip install -r requirements.txt

# 7. Run with Gunicorn (production)
pip install gunicorn
gunicorn -b 0.0.0.0:8501 streamlit_app:app

# OR run directly
streamlit run streamlit_app.py --server.port=8501 --server.address=0.0.0.0
```

Access at: `http://your-instance-ip:8501`

#### Google Cloud Run

```bash
# 1. Create project
gcloud projects create gel-densitometry

# 2. Build and push image
gcloud builds submit --tag gcr.io/gel-densitometry/app

# 3. Deploy
gcloud run deploy gel-densitometry \
    --image gcr.io/gel-densitometry/app \
    --platform managed \
    --region us-central1 \
    --memory 2Gi \
    --timeout 3600

# Access: https://gel-densitometry-xxxxx.run.app
```

#### Heroku

```bash
# 1. Create Procfile
echo "web: streamlit run streamlit_app.py --server.port=\$PORT --server.address=0.0.0.0" > Procfile

# 2. Create Heroku app
heroku create gel-densitometry

# 3. Deploy
git push heroku main

# Access: https://gel-densitometry.herokuapp.com
```

---

## Configuration

### Environment Variables

For production deployments, set:

```bash
# Disable browser caching for faster updates
STREAMLIT_CLIENT_CACHE_CONTROL_HEADERS=false

# Disable telemetry
STREAMLIT_LOGGER_LEVEL=error

# Custom theme
STREAMLIT_THEME_PRIMARY_COLOR=#1f77b4
```

### Custom Domain

#### Streamlit Cloud
1. Settings → Custom Domain
2. Point DNS to Streamlit
3. Verify domain

#### AWS/GCP/Azure
Use Route 53, Cloud DNS, or Azure DNS to point your domain to the instance/load balancer.

---

## Performance & Optimization

### Streamlit Cloud Limits
- Free tier: 1 app, limited resources
- Pro tier: Multiple apps, priority support

### Optimization Tips

1. **Cache computationally expensive operations:**
```python
@st.cache_data
def load_image(file):
    return GelImageProcessor(file)
```

2. **Use session state for faster interactions:**
```python
if 'processor' not in st.session_state:
    st.session_state.processor = None
```

3. **Limit file upload size:**
- Streamlit Cloud: 200MB max
- Configure in `.streamlit/config.toml`:
```toml
[client]
maxUploadSize = 200
```

### Memory Management
- Image processing: ~50-100MB per image
- Peak detection: ~10-20MB
- Streamlit overhead: ~100MB
- **Recommended minimum: 512MB RAM**

---

## Monitoring & Maintenance

### Streamlit Cloud Logs
```bash
streamlit logs <app-name>
```

### Health Checks
- App automatically restarts if it crashes
- Unused apps sleep after 7 days of inactivity

### Updates
Simply push to GitHub:
```bash
git push github main
```
App auto-reloads within 1 minute.

---

## Troubleshooting

### Issue: App won't load
- Check logs: Settings → Logs
- Clear cache: Settings → Clear Cache
- Redeploy: Click "Rerun"

### Issue: "Module not found"
- Ensure all imports in `streamlit_app.py` are in `requirements.txt`
- Redeploy after updating requirements

### Issue: Large file uploads fail
- Increase max upload size in config.toml
- Split large images into smaller regions
- Use cloud storage (S3) instead of direct upload

### Issue: Slow performance
- Profile with `streamlit --logger.level=debug`
- Add caching for expensive operations
- Consider upgrading to Streamlit Pro

---

## Comparison: Deployment Options

| Platform | Cost | Setup Time | Ease | Best For |
|----------|------|-----------|------|----------|
| **Streamlit Cloud** | Free (Pro: $5/mo) | 5 min | ⭐⭐⭐⭐⭐ | Quick demos, testing |
| **AWS EC2** | $10-50/mo | 20 min | ⭐⭐⭐ | Production, scaling |
| **Google Cloud** | $15-100/mo | 15 min | ⭐⭐⭐ | Enterprise, GCP integration |
| **Heroku** | $25+/mo | 10 min | ⭐⭐⭐⭐ | Simple deployments |
| **Docker** | Varies | 30 min | ⭐⭐⭐ | Containerized, flexible |
| **Local Machine** | Free | 2 min | ⭐⭐⭐⭐⭐ | Testing, development |

---

## Advanced: CI/CD Pipeline

### GitHub Actions (Auto-deploy on push)

Create `.github/workflows/deploy.yml`:

```yaml
name: Deploy to Streamlit Cloud

on:
  push:
    branches: [ main ]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Trigger Streamlit Cloud Build
        run: |
          curl -X POST "https://api.streamlit.cloud/v1/deployments/create" \
            -H "Authorization: Bearer ${{ secrets.STREAMLIT_API_TOKEN }}" \
            -H "Content-Type: application/json" \
            -d '{"repository":"USERNAME/Lipoprint","branch":"main","file":"streamlit_app.py"}'
```

---

## Support & Documentation

- **Streamlit Docs**: https://docs.streamlit.io
- **Streamlit Community**: https://discuss.streamlit.io
- **Issues**: Report bugs on GitHub
- **Feature Requests**: GitHub Discussions

---

## Next Steps

1. Choose a deployment option from above
2. Follow the setup instructions
3. Test the app with sample gel images
4. Share the public URL with your team
5. Monitor performance and collect feedback
