import os
import json
import asyncio
from datetime import datetime
from telethon import TelegramClient

# --- 你的账号配置 ---
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
PHONE = '+243991464642'
SIGN_FILE = 'sign_targets.json'

async def main():
    client = TelegramClient("sign_worker_session", API_ID, API_HASH)
    await client.start(phone=PHONE)
    print("🚀 签到执行进程 (auto_sign) 已就绪...")

    while True:
        now = datetime.now()
        # 每天 00:00 和 12:00 执行
        if now.hour in [0, 12]:
            if os.path.exists(SIGN_FILE):
                with open(SIGN_FILE, 'r', encoding='utf-8') as f:
                    targets = json.load(f)
                
                print(f"[{now}] 正在处理 {len(targets)} 个任务...")
                for b in targets:
                    try:
                        await client.send_message(b['bot_username'], b['command'])
                        print(f"  ✅ {b['name']} 发送成功")
                        await asyncio.sleep(5) # 频率保护
                    except Exception as e:
                        print(f"  ❌ {b['name']} 失败: {e}")
                
                # 执行完休息一小时，防止重复触发
                await asyncio.sleep(3601)
        
        await asyncio.sleep(60)

if __name__ == "__main__":
    asyncio.run(main())
