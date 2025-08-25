import asyncio
import os
import json
from typing import List
from pydantic import BaseModel

from browser_use import Agent, Controller
from browser_use.llm import ChatDeepSeek
from browser_use.logging_config import setup_logging
from browser_use.agent.views import AgentHistoryList

deepseek_api_key = 'sk-cd4480658d354f9e91d96b66a47cda4a'

task = """我想要在秀动网站搜索说唱歌手kito的演出信息，你可以参考如下方式：
1、打开https://www.showstart.com/ 秀动网站。
2、在右上角搜索框输入"kito"，并获取kito所有的演出信息。
3、提取出演出地点、演出场地、演出嘉宾、演出时间、票价以及演出链接。
最终返回的结果是json格式的，如下所示：
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
  }"""


class TicketPrice(BaseModel):
    presale: str
    regular: str
    vip: str

class PerformanceInfo(BaseModel):
    address: str
    venue: str
    date: str
    guest: List[str]
    ticket_prices: TicketPrice
    performance_url: str

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
            if isinstance(result_json, dict) and 'address' in result_json:
                result_json = {'performances': [result_json]}

            # 验证结构化输出
            if isinstance(result_json, dict) and 'performances' in result_json:
                performances = PerformanceResults.model_validate(result_json)
                print("\n验证通过的结构化数据:")
                for i, perf in enumerate(performances.performances, 1):
                    print(f"\n演出 {i}:")
                    print(f"  地址: {perf.address}")
                    print(f"  场地: {perf.venue}")
                    print(f"  时间: {perf.date}")
                    print(f"  嘉宾: {', '.join(perf.guest)}")
                    print(
                        f"  票价: 预售{perf.ticket_prices.presale}, 正价{perf.ticket_prices.regular}, VIP{perf.ticket_prices.vip}")
                    print(f"  链接: {perf.performance_url}")
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

    agent = Agent(
        task=task,
        llm=llm,
        controller=controller,
        use_vision=False,
        save_conversation_path='conversation_deepseek.txt',
        register_done_callback=handle_final_result,
    )

    await agent.run()


if __name__ == '__main__':
    asyncio.run(main())