#!/bin/bash
# Phase 1 Setup Script - Run this to start annotation

echo "🚀 Starting Phase 1 - FFB Annotation Setup"
echo "=========================================="

# Step 1: Verify Docker is running
echo ""
echo "Step 1: Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    echo "   Download from: https://www.docker.com/products/docker-desktop"
    exit 1
fi
echo "✅ Docker found"

# Step 2: Create Label Studio data directory
echo ""
echo "Step 2: Creating Label Studio data directory..."
mkdir -p ~/label-studio-data
echo "✅ Directory created: ~/label-studio-data"

# Step 3: Start Label Studio
echo ""
echo "Step 3: Starting Label Studio (this takes ~30 seconds)..."
docker run -d -p 8080:8080 -v ~/label-studio-data:/label-studio/data \
  --name label-studio \
  heartexlabs/label-studio:latest

sleep 15

echo "✅ Label Studio is starting..."

# Step 4: Check if running
echo ""
echo "Step 4: Verifying Label Studio is running..."
if docker ps | grep -q label-studio; then
    echo "✅ Label Studio is running!"
    echo ""
    echo "🎉 SUCCESS! Label Studio is ready:"
    echo "   → Open: http://localhost:8080"
    echo "   → Default login: admin@heartex.com / password"
    echo ""
    echo "📋 Next steps:"
    echo "   1. Go to http://localhost:8080"
    echo "   2. Create new project: 'FFB Detection Phase 1'"
    echo "   3. Upload 64 images from: SG9-RW010SS-10T-40P-070326 - SMTF1/"
    echo "   4. Configure YOLO annotation template"
    echo "   5. Start annotating FFB bunches"
    echo ""
    echo "📝 Track progress in: PHASE1_CHECKLIST.md"
else
    echo "❌ Label Studio failed to start. Try:"
    echo "   docker logs label-studio"
fi
