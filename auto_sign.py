import os
import json
import asyncio
import time
from datetime import datetime
from telethon import TelegramClient

# 配置
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
CONFIG_FILE = 'sign_targets.json'

async def main():
    client = TelegramClient("sign_worker", API_ID, API_HASH)
    await client.start() # 首次运行需输入验证码
    
    print("✅ 签到执行进程已启动...")

    while True:
        now = datetime.now()
        # 每天 0点 和 12点 执行
        if now.hour in [0, 12]:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    targets = json.load(f)
                
                print(f"[{now}] 正在执行 {len(targets)} 个签到任务...")
                for bot in targets:
                    try:
                        await client.send_message(bot['bot_username'], bot['command'])
                        print(f"  ✓ {bot['name']} 发送成功")
                        await asyncio.sleep(5) # 频率保护
                    except Exception as e:
                        print(f"  ✗ {bot['name']} 失败: {e}")
                
                print("任务结束，休眠一小时...")
                await asyncio.sleep(3601) # 避免在同一小时内重复触发
        
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
