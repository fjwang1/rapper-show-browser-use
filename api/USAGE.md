# Rapper演出搜索API使用指南

## 快速开始

### 1. 启动API服务

```bash
# 进入API目录
cd /Users/wangfangjia/code/rapper-show-browser-use/api

# 启动服务（推荐方式）
python start_api.py

# 或者直接使用uvicorn
python main.py
```

服务启动后，你会看到类似以下输出：
```
🎤 启动Rapper演出搜索API服务...
📍 地址: http://0.0.0.0:8000
📋 API文档: http://0.0.0.0:8000/docs
🔧 重载模式: 开启
📝 日志级别: info
```

### 2. 测试API服务

```bash
# 运行API测试脚本
python test_api.py

# 运行完整演示
python demo.py
```

### 3. 使用API搜索rapper

#### 方式1: 使用cURL

```bash
curl -X POST "http://localhost:8000/search/rapper" \
  -H "Content-Type: application/json" \
  -d '{
    "rapper_name": "kito",
    "timeout_seconds": 300
  }'
```

#### 方式2: 使用Python

```python
import requests

response = requests.post(
    "http://localhost:8000/search/rapper",
    json={
        "rapper_name": "kito",
        "timeout_seconds": 300
    }
)

result = response.json()
print(f"找到 {result['total_count']} 个演出")
for perf in result['performances']:
    print(f"- {perf['venue']} ({perf['date']})")
```

#### 方式3: 使用httpx (异步)

```python
import asyncio
import httpx

async def search_rapper(name):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "http://localhost:8000/search/rapper",
            json={"rapper_name": name}
        )
        return response.json()

result = asyncio.run(search_rapper("kito"))
```

## API接口说明

### 搜索rapper演出

**POST** `/search/rapper`

**请求体:**
```json
{
  "rapper_name": "kito",
  "timeout_seconds": 300
}
```

**成功响应:**
```json
{
  "success": true,
  "rapper_name": "kito",
  "performances": [
    {
      "address": "广州市荔湾区恩宁路265号3层",
      "venue": "MAOLivehouse广州（永庆坊店）",
      "date": "08月24日 19:00-08月24日 20:30",
      "guest": ["SHark米尔艾力", "LilAsian"],
      "ticket_prices": {
        "presale": "￥158",
        "regular": "￥198",
        "vip": "￥288"
      },
      "performance_url": "https://www.showstart.com/event/273756"
    }
  ],
  "total_count": 1,
  "search_time": "2024-01-15T10:30:00",
  "execution_stats": {
    "total_steps": 8,
    "duration_seconds": 45.6,
    "is_done": true,
    "is_successful": true
  }
}
```

### 健康检查

**GET** `/health`

**响应:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00",
  "service": "rapper-search-api"
}
```

## 配置选项

### 环境变量

在项目根目录创建 `.env` 文件：

```bash
# DeepSeek API配置
DEEPSEEK_API_KEY=your_api_key_here

# 服务器配置
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=info

# 搜索配置
DEFAULT_TIMEOUT_SECONDS=300
```

### 启动参数

```bash
python start_api.py --help

# 自定义端口启动
python start_api.py --port 9000

# 生产模式启动（禁用重载）
python start_api.py --no-reload --workers 4

# 调试模式启动
python start_api.py --log-level debug
```

## 常见问题

### Q: API服务启动失败
A: 检查以下几点：
- 确保已安装所有依赖：`uv sync`
- 检查端口是否被占用：`lsof -i :8000`
- 查看错误日志中的具体信息

### Q: 搜索总是返回失败
A: 可能的原因：
- DeepSeek API密钥无效或过期
- 网络连接问题
- 搜索超时时间设置过短
- 目标网站结构发生变化

### Q: 搜索速度很慢
A: 优化建议：
- 增加搜索超时时间
- 检查网络连接质量
- 考虑使用更快的模型

### Q: 如何部署到生产环境
A: 生产部署建议：
```bash
# 使用gunicorn部署
pip install gunicorn
gunicorn -w 4 -k uvicorn.workers.UvicornWorker main:app

# 使用Docker部署
docker build -t rapper-api .
docker run -p 8000:8000 rapper-api
```

## 扩展和定制

### 添加新的搜索网站

修改 `rapper_search_service.py` 中的 `_create_search_task` 方法：

```python
def _create_search_task(self, rapper_name: str) -> str:
    task = f"""搜索{rapper_name}在以下网站的演出信息：
    1. 秀动网站 (https://www.showstart.com/)
    2. 大麦网 (https://www.damai.cn/)
    3. 摩天轮票务 (https://www.摩天轮.cn/)
    ..."""
    return task
```

### 添加缓存支持

```python
# 安装Redis
pip install redis

# 在rapper_search_service.py中添加缓存逻辑
import redis
r = redis.Redis(host='localhost', port=6379, db=0)

async def search_rapper_performances(self, rapper_name: str):
    # 检查缓存
    cache_key = f"rapper:{rapper_name}"
    cached_result = r.get(cache_key)
    if cached_result:
        return json.loads(cached_result)
    
    # 执行搜索...
    result = await self._perform_search(rapper_name)
    
    # 存储到缓存（1小时过期）
    r.setex(cache_key, 3600, json.dumps(result))
    return result
```

### 添加API认证

```python
# 在main.py中添加API密钥认证
from fastapi import Header, HTTPException

async def verify_api_key(x_api_key: str = Header()):
    if x_api_key != "your_secret_api_key":
        raise HTTPException(status_code=401, detail="Invalid API Key")

@app.post("/search/rapper", dependencies=[Depends(verify_api_key)])
async def search_rapper(request: SearchRequest):
    # ... 现有逻辑
```

## 监控和日志

### 查看日志

```bash
# 查看API服务日志
tail -f logs/api.log

# 查看browser-use对话记录
ls conversations/
cat conversations/conversation_rapper_kito_*.txt
```

### 监控指标

API会自动记录以下指标：
- 搜索请求数量
- 搜索成功/失败率
- 平均搜索时间
- 错误类型统计

可以通过执行统计信息查看这些数据。
