from telethon import TelegramClient, events
import json
import os

# 配置
API_ID = 2040
API_HASH = "b18441a1ff607e10a989891a5462e627"
BOT_TOKEN = "8417331227:AAESrsOPgEDMeu7NHgLMgoZrynkxoafBLBY"
CONFIG_FILE = 'sign_targets.json'
ADMIN_ID = 6649617045 # 替换为你的 ID

bot = TelegramClient("manager_bot", API_ID, API_HASH)

def get_targets():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

def save_targets(data):
    with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

@bot.on(events.NewMessage(pattern='/zl'))
async def zl_handler(event):
    if event.sender_id != ADMIN_ID: return
    menu = """🤖 **签到管理后台**
/list - 查看当前列表
/add_bot 名称 @用户名 指令
/del_bot @用户名
/status - 查看运行状态"""
    await event.reply(menu)

@bot.on(events.NewMessage(pattern='/list'))
async def list_handler(event):
    if event.sender_id != ADMIN_ID: return
    data = get_targets()
    res = "📋 **签到列表:**\n"
    for i, b in enumerate(data, 1):
        res += f"{i}. {b['name']} (@{b['bot_username']}) - `{b['command']}`\n"
    await event.reply(res or "列表为空")

@bot.on(events.NewMessage(pattern='/add_bot'))
async def add_handler(event):
    if event.sender_id != ADMIN_ID: return
    parts = event.text.split(maxsplit=3)
    if len(parts) < 4:
        await event.reply("用法: `/add_bot 名称 @用户名 指令`")
        return
    
    data = get_targets()
    data.append({"name": parts[1], "bot_username": parts[2].replace("@",""), "command": parts[3]})
    save_targets(data)
    await event.reply(f"✅ 已添加: {parts[1]}")

@bot.on(events.NewMessage(pattern='/del_bot'))
async def del_handler(event):
    if event.sender_id != ADMIN_ID: return
    target = event.text.split()[-1].replace("@","")
    data = [b for b in get_targets() if b['bot_username'] != target]
    save_targets(data)
    await event.reply(f"🗑️ 已删除: @{target}")

if __name__ == "__main__":
    print("✅ 管理机器人已启动...")
    bot.start(bot_token=BOT_TOKEN)
    bot.run_until_disconnected()
