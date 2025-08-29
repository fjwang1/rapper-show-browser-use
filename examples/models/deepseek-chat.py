import asyncio
import os
import json
from typing import List
from pydantic import BaseModel

from browser_use import Agent, Controller, BrowserSession, BrowserProfile
from browser_use.llm import ChatDeepSeek
from browser_use.logging_config import setup_logging
from browser_use.agent.views import AgentHistoryList

deepseek_api_key = 'sk-cd4480658d354f9e91d96b66a47cda4a'

task = """我想要在秀动网站搜索说唱歌手kito的演出信息，请按照以下方式操作：
1、直接打开 https://www.showstart.com/event/list?keyword=kito 进入kito的搜索结果页面。
2、通过extract_rapper_shows_data_for_showstar工具提取从搜索结果页面提取出所有演出信息：演出名称、艺人、价格、时间、场地、演出头图、链接等。
3、其中演出链接在<a href="/event/274673" class="show-item item" data-v-45a60ebc="">标签的href属性中，需要再补上固定的host和Protocol，如https://www.showstart.com/event/274673。
4、你应该调用一次工具即可获取所有演出信息，直接返回即可。不需要后续操作。
最终返回的结果是json格式的，如下所示：
{
    "mainImage": "https://s2.showstart.com/img/2025/0813/16/30/3d8dbf67b3834e9891c4bd18009ca737_2988_5257_6400974.0x0.png",
    "title": "2025 KITO\"KDAY\" KITO TOUR 巡演（北京站）",
    "artists": ["黄旭", "KITO", "Vinz-T"],
    "price": "¥158起",
    "date": "2025/09/07 19:00",
    "venue": "[北京]MAO Livehouse北京（五棵松店）",
    "purchase_url": "https://www.showstart.com/event/273756"
}"""

class PerformanceInfo(BaseModel):
    title: str
    artists: List[str]
    price: str
    date: str
    venue: str
    purchase_url: str

class PerformanceResults(BaseModel):
    performances: List[PerformanceInfo]

async def handle_final_result(history: AgentHistoryList):
    """处理Agent完成后的最终结果"""
    print("\n=== Agent执行完成 ===\n")

    # 获取最终结果
    final_result = history.final_result()
    if final_result:
        print("原始结果:")
        print(final_result)
        print("\n" + "=" * 50 + "\n")

        try:
            # 尝试解析为JSON
            result_json = json.loads(final_result)
            print("解析后的JSON结果:")
            print(json.dumps(result_json, ensure_ascii=False, indent=2))

            # 如果是单个演出信息，转换为列表格式
            if isinstance(result_json, dict) and 'title' in result_json:
                result_json = {'performances': [result_json]}

            # 验证结构化输出
            if isinstance(result_json, dict) and 'performances' in result_json:
                performances = PerformanceResults.model_validate(result_json)
                print("\n验证通过的结构化数据:")
                for i, perf in enumerate(performances.performances, 1):
                    print(f"\n演出 {i}:")
                    print(f"  名称: {perf.title}")
                    print(f"  艺人: {', '.join(perf.artists)}")
                    print(f"  价格: {perf.price}")
                    print(f"  时间: {perf.date}")
                    print(f"  场地: {perf.venue}")
                    print(f"  购买链接: {perf.purchase_url}")
        except json.JSONDecodeError:
            print("结果不是有效的JSON格式")
        except Exception as e:
            print(f"解析结果时出错: {e}")
    else:
        print("没有获取到最终结果")

    # 显示执行统计信息
    print(f"\n执行统计:")
    print(f"  总步数: {history.number_of_steps()}")
    print(f"  执行时长: {history.total_duration_seconds():.2f}秒")
    print(f"  是否完成: {history.is_done()}")
    print(f"  是否成功: {history.is_successful()}")

    # 显示错误信息（如果有）
    errors = [e for e in history.errors() if e is not None]
    if errors:
        print(f"\n错误信息: {errors}")




async def main():
    # 设置详细的调试日志以查看LLM请求
    # 可选的日志级别：'result', 'info', 'debug'
    # 也可以通过环境变量设置: export BROWSER_USE_LOGGING_LEVEL=debug
    setup_logging(log_level='debug')

    llm = ChatDeepSeek(
        base_url='https://api.deepseek.com/v1',
        model='deepseek-chat',
        api_key=deepseek_api_key,
    )

    # 创建带有结构化输出的Controller（可选）
    controller = Controller(output_model=PerformanceResults)

    # 使用无头浏览器会话
    browser_session = BrowserSession(browser_profile=BrowserProfile(headless=True))

    agent = Agent(
        task=task,
        llm=llm,
        controller=controller,
        # browser_session=browser_session,
        use_vision=False,
        save_conversation_path='conversation_deepseek.txt',
        register_done_callback=handle_final_result,
    )

    await agent.run()


if __name__ == '__main__':
    asyncio.run(main())