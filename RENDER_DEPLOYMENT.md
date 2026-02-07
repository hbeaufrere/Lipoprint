# Deploy Gel Densitometry App to Render

Follow these steps to deploy your Dash application to Render.com.

## Prerequisites

- GitHub account with your repository pushed
- Render.com account (free)
- These deployment files already created:
  - `requirements.txt` - Python dependencies
  - `Procfile` - Deployment instructions

## Step-by-Step Deployment

### 1. Sign Up for Render (if needed)
- Go to https://render.com
- Sign up with GitHub account (easiest option)
- Authorize Render to access your GitHub

### 2. Create a New Web Service
- Click "New +" button
- Select "Web Service"
- Choose your GitHub repository: `hbeaufrere/Lipoprint`

### 3. Configure the Service

| Setting | Value |
|---------|-------|
| **Name** | `lipoprint-gel-analysis` (or any name) |
| **Branch** | `claude/gel-densitometry-analysis-U53eI` |
| **Runtime** | Python 3 |
| **Build Command** | `pip install -r requirements.txt` |
| **Start Command** | `python dash_app.py` |
| **Instance Type** | Free tier (sufficient for this app) |
| **Environment** | Set `PORT=10000` (Render default) |

### 4. Deploy
- Click "Create Web Service"
- Wait 2-5 minutes for build and deployment
- You'll get a live URL like: `https://lipoprint-gel-analysis.onrender.com`

### 5. Test the Live App
- Open your URL in browser
- Upload a gel image
- Verify all features work

## After Deployment

### Auto-Deploy on Push
Render will automatically redeploy when you push to your branch:
```bash
git push origin claude/gel-densitometry-analysis-U53eI
```

### Monitor the App
- View logs in Render dashboard
- Check deployment status
- Restart if needed (rare)

### Free Tier Limitations
- App spins down after 15 minutes of inactivity (15s to restart)
- Limited to small file uploads
- Should work fine for your use case

### Upgrade to Paid (Optional)
- Paid tier: $7/month minimum
- Keeps app always running
- Better for production use

## If Something Goes Wrong

### App won't build?
- Check `requirements.txt` is correct
- Verify `Procfile` has no typos
- Check Render build logs for errors

### Port issues?
- Render provides `PORT` environment variable
- Our app automatically detects it
- Should work without changes

### Upload file size limits?
- Render has upload limits
- Dash default is ~32MB
- Contact Render support if needed

## Environment Variables

Currently using:
- `PORT` - Automatically detected (default: 8050 locally, 10000 on Render)
- `ENVIRONMENT` - Set to "production" on Render to disable debug mode

To add more environment variables:
1. Go to Render dashboard
2. Select your service
3. Click "Environment"
4. Add variables as needed

## Local Testing Before Deploy

Test locally exactly as Render will run it:
```bash
# Set production environment
export ENVIRONMENT=production
export PORT=8050

# Run the app
python dash_app.py
```

## Getting Your URL

After deployment succeeds:
1. Go to Render dashboard
2. Select your service
3. Copy the URL from "Live URL" section
4. Share with colleagues!

Example: `https://lipoprint-gel-analysis.onrender.com`

## Troubleshooting

**Q: App keeps spinning down**
- Normal on free tier after 15 minutes inactivity
- Wakes up when accessed (slight delay first time)
- Upgrade to paid if this is annoying

**Q: Upload fails**
- Check file size (should be <30MB)
- Verify file format (TIF/JPEG)
- Try smaller test image first

**Q: Changes not showing after push**
- Wait for Render build to complete (check dashboard)
- Hard refresh browser (Ctrl+Shift+R)
- Check Render logs for errors

**Q: Need to restart app?**
- Go to Render dashboard
- Click "Manual Deploy" → "Deploy latest commit"

## File Structure

Your repository should have:
```
Lipoprint/
├── dash_app.py              # Main app
├── image_processor.py       # Image processing
├── export_handler.py        # Export functions
├── requirements.txt         # Python dependencies ← IMPORTANT
├── Procfile                 # Deployment config ← IMPORTANT
├── .gitignore              # Git ignore rules
├── DASH_APP_README.md       # Local usage
└── RENDER_DEPLOYMENT.md     # This file
```

## Next Steps

1. ✅ Commit `requirements.txt` and `Procfile` to git
2. ✅ Push to `claude/gel-densitometry-analysis-U53eI` branch
3. ✅ Sign up for Render
4. ✅ Create new Web Service (connect GitHub)
5. ✅ Configure as shown above
6. ✅ Deploy!
7. ✅ Share live URL

## Support

For Render issues:
- https://render.com/docs
- Render support: support@render.com

For app issues:
- Check Render logs
- Review DASH_APP_README.md
- Test locally first with `python dash_app.py`
