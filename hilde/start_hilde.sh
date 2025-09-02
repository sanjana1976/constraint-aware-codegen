#!/bin/bash

echo "🚀 Starting HILDE System..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if NVIDIA Docker is available
if ! docker run --rm --gpus all nvidia/cuda:11.8-base-ubuntu20.04 nvidia-smi > /dev/null 2>&1; then
    echo "⚠️  NVIDIA Docker not available. GPU acceleration may not work."
fi

# Create necessary directories
mkdir -p logs models

# Set environment variables
export COMPLETION_SERVICE_URL=http://localhost:8001
export ANALYSIS_SERVICE_URL=http://localhost:8002

echo "📁 Directories created"
echo "🔧 Environment variables set"

# Start services
echo "🐳 Starting Docker services..."
docker-compose up -d

# Wait for services to be ready
echo "⏳ Waiting for services to start..."
sleep 10

# Check service health
echo "🔍 Checking service health..."

# Check completion service
if curl -s http://localhost:8001/health > /dev/null; then
    echo "✅ Completion service is running"
else
    echo "❌ Completion service failed to start"
fi

# Check analysis service
if curl -s http://localhost:8002/health > /dev/null; then
    echo "✅ Analysis service is running"
else
    echo "❌ Analysis service failed to start"
fi

# Check API gateway
if curl -s http://localhost:8000/health > /dev/null; then
    echo "✅ API gateway is running"
else
    echo "❌ API gateway failed to start"
fi

echo ""
echo "🎉 HILDE system startup complete!"
echo ""
echo "📊 Service Status:"
echo "   Completion LLM: http://localhost:8001"
echo "   Analysis LLM:   http://localhost:8002"
echo "   API Gateway:    http://localhost:8000"
echo ""
echo "🔧 Next steps:"
echo "   1. Install VS Code extension: cd extension && npm install && npm run compile"
echo "   2. Run tests: python test_hilde.py"
echo "   3. Open VS Code and start coding!"
echo ""
echo "📚 Documentation: README.md"
echo "🐛 Issues: Check logs/ directory for detailed logs"
