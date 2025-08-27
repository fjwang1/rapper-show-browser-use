# @file purpose: Rapper搜索服务类，封装browser-use自动化搜索逻辑
"""
Rapper演出信息搜索服务

这个文件定义了RapperSearchService类，封装了使用browser-use和DeepSeek模型
自动化搜索说唱歌手演出信息的核心逻辑。

主要功能：
- 使用DeepSeek Chat模型驱动browser-use
- 自动化访问秀动网站并搜索指定rapper
- 提取并结构化演出信息
- 处理搜索结果和错误情况
"""

import asyncio
import json
import os
from datetime import datetime, date
import re
from typing import List, Dict, Any, Optional

from pydantic import BaseModel

from browser_use import Agent, Controller, BrowserSession, BrowserProfile
from browser_use.llm import ChatDeepSeek
from browser_use.agent.views import AgentHistoryList

from api.db.repository import init_schema, cleanup_expired_by_rapper, insert_performance_row


class TicketPrice(BaseModel):
    """票价信息模型"""
    presale: str
    regular: str
    vip: str


class PerformanceInfo(BaseModel):
    """单个演出信息模型"""
    address: str
    venue: str
    date: str
    guest: List[str]
    ticket_prices: TicketPrice
    performance_url: str


class PerformanceResults(BaseModel):
    """演出结果集模型"""
    performances: List[PerformanceInfo]


class RapperSearchService:
    """Rapper演出信息搜索服务类"""
    
    def __init__(self):
        self.deepseek_api_key = os.getenv(
            'DEEPSEEK_API_KEY', 
            'sk-cd4480658d354f9e91d96b66a47cda4a'
        )
        
        self.llm = ChatDeepSeek(
            base_url='https://api.deepseek.com/v1',
            model='deepseek-chat',
            api_key=self.deepseek_api_key,
        )
        
        # 创建带有结构化输出的Controller
        self.controller = Controller(output_model=PerformanceResults)

        print("🎤 RapperSearchService初始化完成")
        # 初始化数据库表结构（幂等）
        try:
            init_schema()
            print("🗄️  数据库表已就绪")
        except Exception as e:
            print(f"⚠️  初始化数据库表失败: {e}")

    def _create_search_task(self, rapper_name: str) -> str:
        json_example = '''{
        "mainImage": "https://s2.showstart.com/img/2025/0813/16/30/3d8dbf67b3834e9891c4bd18009ca737_2988_5257_6400974.0x0.png",
        "title": "2025 KITO\\"KDAY\\" KITO TOUR 巡演（北京站）",
        "artists": ["黄旭", "KITO", "Vinz-T"],
        "price": "¥158起",
        "date": "2025/09/07 19:00",
        "venue": "[北京]MAO Livehouse北京（五棵松店）",
        "purchase_url": "https://www.showstart.com/event/273756"
    }'''

        task = f"""我想要在秀动网站搜索说唱歌手{rapper_name}的演出信息，请按照以下方式操作：
    1、直接打开 https://www.showstart.com/event/list?keyword={rapper_name} 进入搜索结果页面。
    2、从搜索结果页面直接提取每场演出的基本信息：演出名称、艺人、价格、时间、场地、演出头图（可能需要extract_structured_data工具提取，其中参数extract_links为true才能拿到头图链接）。
    3、点击每个演出卡片进入详情页，仅获取该页面的URL作为购买链接，无需提取其他DOM元素。
    最终返回的结果是json格式的，如下所示：
    {json_example}
        
        如果找到多个演出，请返回包含所有演出信息的数组格式：
        {{
            "performances": [
                {{演出信息1}},
                {{演出信息2}},
                ...
            ]
        }}
        
        请确保搜索全面，包括所有可用的演出信息。"""

        return task

    def _parse_performance_date(self, date_text: Optional[str]) -> date:
        """从文本中解析演出日期，仅日期部分。无法解析则返回今天。"""
        if not date_text:
            return date.today()
        # 尝试 YYYY-MM-DD
        m = re.search(r"(20\\d{2})-(0[1-9]|1[0-2])-(0[1-9]|[12]\\d|3[01])", date_text)
        if m:
            y, mth, d = m.groups()
            return date(int(y), int(mth), int(d))
        # 尝试 MM月DD日（无年份，按今年）
        m = re.search(r"(0?[1-9]|1[0-2])\\s*月\\s*(0?[1-9]|[12]\\d|3[01])\\s*日", date_text)
        if m:
            y = date.today().year
            mth, d = m.groups()
            return date(int(y), int(mth), int(d))
        # 兜底
        return date.today()

    def _parse_price(self, price_text: Optional[str]) -> Optional[float]:
        """将 '￥158'、'158'、'¥199.00' 等解析为 float；解析失败返回 None。"""
        if not price_text:
            return None
        try:
            digits = re.findall(r"[0-9]+(?:\\.[0-9]+)?", price_text)
            if not digits:
                return None
            return float(digits[0])
        except Exception:
            return None

    async def _handle_agent_result(self, history: AgentHistoryList, rapper_name: str) -> Dict[str, Any]:
        try:
            final_result = history.final_result()

            if not final_result:
                return {
                    "success": False,
                    "error_message": "Agent没有返回结果",
                    "performances": [],
                    "total_count": 0
                }

            print(f"🔍 Agent原始结果: {final_result}")

            # 尝试解析JSON
            try:
                result_json = json.loads(final_result)
            except json.JSONDecodeError:
                # 如果不是JSON格式，尝试从文本中提取信息
                return {
                    "success": False,
                    "error_message": f"无法解析Agent返回的结果为JSON格式: {final_result}",
                    "performances": [],
                    "total_count": 0
                }

            # 标准化结果格式
            if isinstance(result_json, dict):
                if 'performances' in result_json:
                    # 已经是标准格式
                    performances_data = result_json
                elif 'address' in result_json:
                    # 单个演出信息，转换为标准格式
                    performances_data = {'performances': [result_json]}
                else:
                    return {
                        "success": False,
                        "error_message": "返回的数据格式不正确",
                        "performances": [],
                        "total_count": 0
                    }
            else:
                return {
                    "success": False,
                    "error_message": "返回的数据类型不正确",
                    "performances": [],
                    "total_count": 0
                }

            # 验证数据结构
            try:
                validated_results = PerformanceResults.model_validate(performances_data)
                performances = [perf.dict() for perf in validated_results.performances]

                # 清理过期数据（今天之前）
                try:
                    deleted = cleanup_expired_by_rapper(rapper_name)
                    print(f"🧹 已清理过期记录 {deleted} 条（{rapper_name}）")
                except Exception as e:
                    print(f"⚠️ 清理过期记录失败: {e}")

                # 写入结果
                inserted = 0
                for perf in performances:
                    perf_date_text = perf.get("date")
                    perf_date = self._parse_performance_date(perf_date_text)
                    price_obj = perf.get("ticket_prices") or {}
                    row = {
                        "rapper_name": rapper_name,
                        "performance_date": perf_date,
                        "performance_time_text": perf_date_text,
                        "venue": perf.get("venue"),
                        "address": perf.get("address"),
                        "price_presale": self._parse_price(price_obj.get("presale")),
                        "price_regular": self._parse_price(price_obj.get("regular")),
                        "price_vip": self._parse_price(price_obj.get("vip")),
                        "purchase_url": perf.get("performance_url"),
                        "guests_json": json.dumps(perf.get("guest") or [] , ensure_ascii=False),
                        "source": "showstart",
                    }
                    try:
                        inserted += insert_performance_row(row)
                    except Exception as e:
                        print(f"⚠️ 插入记录失败: {e}，数据: {row}")
                print(f"📝 本次写入 {inserted} 条记录（{rapper_name}）")

                return {
                    "success": True,
                    "performances": performances,
                    "total_count": len(performances),
                    "error_message": None
                }

            except Exception as e:
                return {
                    "success": False,
                    "error_message": f"数据验证失败: {str(e)}",
                    "performances": [],
                    "total_count": 0
                }

        except Exception as e:
            return {
                "success": False,
                "error_message": f"处理Agent结果时发生错误: {str(e)}",
                "performances": [],
                "total_count": 0
            }

    async def search_rapper_performances(
        self,
        rapper_name: str,
        timeout_seconds: int = 300
    ) -> Dict[str, Any]:
        """
        搜索指定rapper的演出信息

        Args:
            rapper_name: rapper名字
            timeout_seconds: 搜索超时时间（秒）

        Returns:
            Dict[str, Any]: 包含搜索结果的字典
        """
        search_start_time = datetime.now()

        try:
            print(f"🎤 开始搜索rapper: {rapper_name}")

            # 创建搜索任务
            task = self._create_search_task(rapper_name)

            # 存储Agent结果的变量
            agent_result = {"processed": False, "data": None}

            async def result_callback(history: AgentHistoryList):
                """Agent完成时的回调函数"""
                if not agent_result["processed"]:
                    agent_result["data"] = await self._handle_agent_result(history, rapper_name)
                    agent_result["processed"] = True

            # 使用无头浏览器会话
            browser_session = BrowserSession(browser_profile=BrowserProfile(headless=True))

            # 创建Agent
            agent = Agent(
                task=task,
                llm=self.llm,
                controller=self.controller,
                use_vision=False,
                # browser_session = browser_session,
                save_conversation_path=f'conversation_rapper_{rapper_name}_{search_start_time.strftime("%Y%m%d_%H%M%S")}.txt',
                register_done_callback=result_callback,
            )

            # 执行搜索，带超时控制
            try:
                history = await asyncio.wait_for(
                    agent.run(),
                    timeout=timeout_seconds
                )
            except asyncio.TimeoutError:
                return {
                    "success": False,
                    "rapper_name": rapper_name,
                    "performances": [],
                    "total_count": 0,
                    "search_time": search_start_time.isoformat(),
                    "execution_stats": {"timeout": True, "timeout_seconds": timeout_seconds},
                    "error_message": f"搜索超时（{timeout_seconds}秒）"
                }

            # 如果回调还没有处理结果，手动处理
            if not agent_result["processed"]:
                agent_result["data"] = await self._handle_agent_result(history, rapper_name)

            result_data = agent_result["data"]

            # 添加执行统计信息
            execution_stats = {
                "total_steps": history.number_of_steps(),
                "duration_seconds": history.total_duration_seconds(),
                "is_done": history.is_done(),
                "is_successful": history.is_successful(),
                "timeout": False
            }

            # 检查是否有错误
            errors = [e for e in history.errors() if e is not None]
            if errors:
                execution_stats["errors"] = errors

            # 构建最终响应
            response = {
                "success": result_data["success"],
                "rapper_name": rapper_name,
                "performances": result_data["performances"],
                "total_count": result_data["total_count"],
                "search_time": search_start_time.isoformat(),
                "execution_stats": execution_stats,
                "error_message": result_data.get("error_message")
            }

            if response["success"]:
                print(f"✅ 搜索完成，找到 {response['total_count']} 个演出")
            else:
                print(f"❌ 搜索失败: {response['error_message']}")

            return response

        except Exception as e:
            print(f"❌ 搜索过程中发生异常: {str(e)}")
            return {
                "success": False,
                "rapper_name": rapper_name,
                "performances": [],
                "total_count": 0,
                "search_time": search_start_time.isoformat(),
                "execution_stats": {"exception": str(e)},
                "error_message": f"搜索过程中发生异常: {str(e)}"
            }


# 用于测试的主函数
async def test_search_service():
    """测试搜索服务"""
    service = RapperSearchService()
    result = await service.search_rapper_performances("kito")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    asyncio.run(test_search_service())