#!/bin/bash
# deploy.sh - Deploy the Modal app

echo "🚀 Deploying Recipe Generator to Modal..."

# Make sure you're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "❌ Error: requirements.txt not found. Run this from the project root."
    exit 1
fi

# Deploy
modal deploy modal_app/main.py

echo "✅ Deployment complete!"
echo "📝 Your API is now running on Modal"