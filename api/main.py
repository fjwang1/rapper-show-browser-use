# @file purpose: FastAPI服务主文件，提供rapper演出信息搜索API
"""
Rapper演出信息搜索API服务

这个文件实现了一个基于FastAPI的web服务，用于自动化搜索说唱歌手的演出信息。
它使用browser-use库和DeepSeek模型来自动化浏览秀动网站并提取演出数据。

主要功能：
- 提供RESTful API接口接收rapper名字
- 使用DeepSeek Chat模型驱动browser-use进行自动化搜索
- 返回结构化的演出信息JSON数据
"""


from typing import Optional
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
import uvicorn

from browser_use.logging_config import setup_logging

from api.rapper_search_service import RapperSearchService


# API请求和响应模型
class SearchRequest(BaseModel):
    """搜索请求模型"""
    rapper_name: str = Field(..., description="说唱歌手名字", min_length=1, max_length=50)
    timeout_seconds: Optional[int] = Field(None, description="搜索超时时间（秒，None表示永不超时）", ge=30)


class SearchResponse(BaseModel):
    """搜索结果响应模型"""
    success: bool = Field(..., description="搜索是否成功")
    rapper_name: str = Field(..., description="搜索的rapper名字")
    performances: list = Field(default_factory=list, description="演出信息列表")
    total_count: int = Field(0, description="演出总数")
    search_time: str = Field(..., description="搜索时间")
    execution_stats: dict = Field(default_factory=dict, description="执行统计信息")
    error_message: Optional[str] = Field(None, description="错误信息")


class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = Field(False, description="操作是否成功")
    error_message: str = Field(..., description="错误信息")
    error_code: str = Field(..., description="错误代码")


# 创建FastAPI应用
app = FastAPI(
    title="Rapper演出信息搜索API",
    description="基于browser-use和DeepSeek的自动化rapper演出信息搜索服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 全局变量
rapper_search_service: Optional[RapperSearchService] = None


@app.on_event("startup")
async def startup_event():
    """应用启动时初始化服务"""
    global rapper_search_service
    
    # 设置日志
    setup_logging(log_level='info')
    
    # 初始化搜索服务
    rapper_search_service = RapperSearchService()
    print("🎤 Rapper演出搜索API服务已启动")


@app.on_event("shutdown")
async def shutdown_event():
    """应用关闭时清理资源"""
    print("🎤 Rapper演出搜索API服务正在关闭...")


@app.get("/", response_model=dict)
async def root():
    """根路径，返回API信息"""
    return {
        "service": "Rapper演出信息搜索API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "search": "/search/rapper",
            "health": "/health",
            "docs": "/docs"
        }
    }


@app.get("/health", response_model=dict)
async def health_check():
    """健康检查接口"""
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "rapper-search-api"
    }


@app.post("/search/rapper", response_model=SearchResponse)
async def search_rapper(request: SearchRequest):
    """
    同步搜索指定rapper的演出信息
    
    Args:
        request: 包含rapper名字和搜索参数的请求
        
    Returns:
        SearchResponse: 包含演出信息的响应
        
    Raises:
        HTTPException: 当搜索失败时抛出
    """
    try:
        if not rapper_search_service:
            raise HTTPException(
                status_code=500, 
                detail="搜索服务未初始化"
            )
        
        print(f"📥 开始同步搜索任务: {request.rapper_name}")
        
        # 同步等待搜索完成，不设置超时限制
        result = await rapper_search_service.search_rapper_performances(
            rapper_name=request.rapper_name,
            timeout_seconds=request.timeout_seconds  # None表示永不超时
        )
        
        print(f"✅ 搜索任务完成: {request.rapper_name}")
        return result
            
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ 搜索过程中发生异常: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"服务器内部错误: {str(e)}"
        )


## 修改为同步等待模式，解决WebSocket连接问题

@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc: HTTPException):
    """HTTP异常处理器"""
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            success=False,
            error_message=exc.detail,
            error_code=f"HTTP_{exc.status_code}"
        ).dict()
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc: Exception):
    """通用异常处理器"""
    return JSONResponse(
        status_code=500,
        content=ErrorResponse(
            success=False,
            error_message=f"服务器内部错误: {str(exc)}",
            error_code="INTERNAL_SERVER_ERROR"
        ).dict()
    )


if __name__ == "__main__":
    # 直接运行时启动开发服务器
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
        timeout_keep_alive=1200,  # 保持连接1200秒
        timeout_graceful_shutdown=60  # 优雅关闭60秒
    )
