#!/bin/bash

# MindMatch 启动脚本

echo "╔═══════════════════════════════════════════╗"
echo "║      🚀 心灵社交 MindMatch 启动中...      ║"
echo "╚═══════════════════════════════════════════╝"

# 检查Node.js
if ! command -v node &> /dev/null; then
    echo "❌ Node.js 未安装，请先安装 Node.js"
    exit 1
fi

# 创建数据目录
mkdir -p data

# 复制环境变量文件
if [ ! -f .env ]; then
    cp .env.example .env
    echo "✅ 已创建 .env 文件"
fi

# 安装后端依赖
echo "📦 安装后端依赖..."
cd server && npm install
cd ..

# 安装前端依赖
echo "📦 安装前端依赖..."
cd web && npm install
cd ..

echo ""
echo "╔═══════════════════════════════════════════╗"
echo "║              安装完成！                   ║"
echo "╚═══════════════════════════════════════════╝"
echo ""
echo "启动方式："
echo ""
echo "终端1 - 后端服务 (http://localhost:4000)"
echo "  cd server && npm run dev"
echo ""
echo "终端2 - 前端服务 (http://localhost:5173)"
echo "  cd web && npm run dev"
echo ""
echo "或使用 Docker Compose:"
echo "  docker-compose up"
echo ""
