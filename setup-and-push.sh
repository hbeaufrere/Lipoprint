#!/bin/bash
# Script to set up Lipoprint gel densitometry project locally and push to GitHub

set -e

echo "🧬 Gel Densitometry - Local Setup Script"
echo "=========================================="

# Check if tar file exists
if [ ! -f "Lipoprint-gel-densitometry.tar.gz" ]; then
    echo "❌ Error: Lipoprint-gel-densitometry.tar.gz not found!"
    echo "Please download it from Claude Code and run this script from that directory."
    exit 1
fi

echo "📂 Extracting project..."
tar -xzf Lipoprint-gel-densitometry.tar.gz

cd Lipoprint

echo "🔧 Setting up git..."

# Initialize git if not already initialized
if [ ! -d ".git" ]; then
    git init
fi

# Add GitHub remote
git remote remove origin 2>/dev/null || true
git remote add origin https://github.com/hbeaufrere/Lipoprint.git

echo "📝 Creating branch..."
git checkout -b claude/gel-densitometry-analysis-U53eI 2>/dev/null || git checkout claude/gel-densitometry-analysis-U53eI

echo "📤 Staging all files..."
git add .

echo "💾 Creating commit..."
git commit -m "Add gel electrophoresis densitometry analysis application

Core Features:
- TIF image upload and processing
- 12-tube gel analysis (6x2 grid)
- Automatic band detection
- Interactive Plotly graphs
- Multi-format export (CSV, JSON, Summary)
- Streamlit web app for cloud deployment
- PyQt6 desktop app for advanced features

See STREAMLIT_QUICKSTART.md for deployment instructions." 2>/dev/null || echo "ℹ️  (Already committed)"

echo "🚀 Pushing to GitHub..."
git push -u origin claude/gel-densitometry-analysis-U53eI

echo ""
echo "✅ SUCCESS! Your code is now on GitHub!"
echo ""
echo "📋 Next Steps:"
echo "1. Go to: https://streamlit.io/cloud"
echo "2. Click 'New app'"
echo "3. Select repository: hbeaufrere/Lipoprint"
echo "4. Branch: claude/gel-densitometry-analysis-U53eI"
echo "5. Main file: streamlit_app.py"
echo "6. Click Deploy!"
echo ""
echo "🎉 Your app will be live at: https://hbeaufrere-lipoprint.streamlit.app"
