import asyncio
import json
import os
from telethon import TelegramClient
from datetime import datetime

# ============ 核心配置 ============
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
PHONE = '+243991464642'
CONFIG_FILE = 'sign_targets.json'  # 共享配置文件名

async def main():
    # 使用独立的 session 文件名
    client = TelegramClient("sign_worker_session", API_ID, API_HASH)
    await client.connect()
    
    if not await client.is_user_authorized():
        print("首次运行，请在下方输入验证码进行授权：")
        await client.send_code_request(PHONE)
        code = input("请输入手机验证码: ")
        await client.sign_in(PHONE, code)

    print(f"✅ 自动签到监控已启动！(账号: {PHONE})")
    print("等待北京时间 00:00 或 12:00 触发任务...")
    
    while True:
        try:
            now = datetime.now()
            # 每天 0点和12点触发
            if now.hour in [0, 12]:
                # 实时读取主机器人修改后的配置文件
                if os.path.exists(CONFIG_FILE):
                    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                        sign_list = json.load(f)
                else:
                    sign_list = []

                if sign_list:
                    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] 启动定时签到，目标数: {len(sign_list)}")
                    for bot in sign_list:
                        try:
                            # 发送签到指令
                            await client.send_message(bot['bot_username'], bot['command'])
                            print(f"  - [成功] 已发送至: {bot['name']} (@{bot['bot_username']})")
                            await asyncio.sleep(5) # 频率保护，防止太快被封
                        except Exception as e:
                            print(f"  - [失败] {bot['name']}: {e}")
                    
                    print("✨ 本轮签到任务已全部完成，休眠 1 小时避开重复触发...")
                    await asyncio.sleep(3600) 
                else:
                    print("⚠️ 签到列表为空，请在机器人中使用 /add_sign 添加。")
                    await asyncio.sleep(3600)

            await asyncio.sleep(60) # 每分钟检查一次时间
        except Exception as e:
            print(f"发生异常: {e}")
            await asyncio.sleep(30)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("签到进程已手动停止")
