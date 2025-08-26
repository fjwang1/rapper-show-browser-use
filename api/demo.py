#!/usr/bin/env python3
# @file purpose: API服务使用演示脚本
"""
Rapper搜索API使用演示

这个脚本展示了如何使用rapper搜索API服务来搜索说唱歌手的演出信息。
"""

import asyncio
import json
import httpx


async def demo_search_rapper(rapper_name: str, api_url: str = "http://localhost:8000"):
    """演示搜索rapper演出信息"""
    
    print(f"🎤 演示搜索rapper: {rapper_name}")
    print(f"🌐 API地址: {api_url}")
    print("=" * 60)
    
    async with httpx.AsyncClient(timeout=600.0) as client:
        try:
            request_data = {
                "rapper_name": rapper_name,
                "timeout_seconds": 300
            }
            
            print(f"📤 发送搜索请求...")
            print(f"   请求数据: {json.dumps(request_data, ensure_ascii=False, indent=2)}")
            print()
            
            response = await client.post(
                f"{api_url}/search/rapper",
                json=request_data
            )
            
            print(f"📥 收到响应 (状态码: {response.status_code})")
            
            if response.status_code == 200:
                result = response.json()
                
                print("✅ 搜索成功！")
                print(f"🎯 搜索的rapper: {result['rapper_name']}")
                print(f"📊 找到演出数量: {result['total_count']}")
                print(f"⏰ 搜索时间: {result['search_time']}")
                print()
                
                if result['total_count'] > 0:
                    print("🎭 演出信息:")
                    for i, perf in enumerate(result['performances'], 1):
                        print(f"\n  演出 {i}:")
                        print(f"    📍 地址: {perf['address']}")
                        print(f"    🏢 场地: {perf['venue']}")
                        print(f"    📅 时间: {perf['date']}")
                        print(f"    👥 嘉宾: {', '.join(perf['guest']) if perf['guest'] else '无'}")
                        print(f"    💰 票价:")
                        print(f"       预售: {perf['ticket_prices']['presale']}")
                        print(f"       正价: {perf['ticket_prices']['regular']}")
                        print(f"       VIP: {perf['ticket_prices']['vip']}")
                        print(f"    🔗 链接: {perf['performance_url']}")
                else:
                    print("📭 没有找到演出信息")
                
                # 显示执行统计
                stats = result.get('execution_stats', {})
                print(f"\n📈 执行统计:")
                print(f"   总步数: {stats.get('total_steps', 'N/A')}")
                print(f"   执行时长: {stats.get('duration_seconds', 'N/A')}秒")
                print(f"   是否完成: {stats.get('is_done', 'N/A')}")
                print(f"   是否成功: {stats.get('is_successful', 'N/A')}")
                
            else:
                print("❌ 搜索失败")
                try:
                    error_data = response.json()
                    print(f"   错误信息: {error_data.get('error_message', '未知错误')}")
                    print(f"   错误代码: {error_data.get('error_code', 'UNKNOWN')}")
                except:
                    print(f"   响应内容: {response.text}")
                    
        except httpx.TimeoutException:
            print("⏰ 请求超时")
        except httpx.ConnectError:
            print("🔌 无法连接到API服务")
            print("💡 请确保API服务正在运行: python start_api.py")
        except Exception as e:
            print(f"❌ 发生异常: {e}")


async def demo_health_check(api_url: str = "http://localhost:8000"):
    """演示健康检查"""
    
    print("🏥 检查API服务健康状态...")
    
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            response = await client.get(f"{api_url}/health")
            
            if response.status_code == 200:
                health_data = response.json()
                print("✅ API服务运行正常")
                print(f"   状态: {health_data.get('status')}")
                print(f"   时间: {health_data.get('timestamp')}")
                print(f"   服务: {health_data.get('service')}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False


async def main():
    """主演示函数"""
    
    print("🎤 Rapper演出搜索API演示")
    print("=" * 60)
    print()
    
    api_url = "http://localhost:8000"
    
    # 1. 健康检查
    health_ok = await demo_health_check(api_url)
    print()
    
    if not health_ok:
        print("⚠️  API服务似乎不可用，请先启动服务:")
        print("   cd /path/to/rapper-show-browser-use/api")
        print("   python start_api.py")
        return
    
    # 2. 演示搜索功能
    print("开始演示搜索功能...")
    print()
    
    # 搜索示例rapper
    await demo_search_rapper("GAI", api_url)

    print("🏁 演示完成！")
    print()
    print("💡 提示:")
    print("   - API文档: http://localhost:8000/docs")
    print("   - ReDoc文档: http://localhost:8000/redoc")
    print("   - 健康检查: http://localhost:8000/health")


if __name__ == "__main__":
    asyncio.run(main())
