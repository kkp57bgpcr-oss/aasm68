#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import telebot
import json
import os

# ============ 核心配置 ============
# 专门用于签到管理的新 Token
API_TOKEN = '8505048236:AAFHPC3448Gti60whSAC9mak_oKzd7BN1eY'
ADMIN_ID = 6649617045  # 确保这是你的 Telegram ID
SIGN_FILE = 'sign_targets.json'

bot = telebot.TeleBot(API_TOKEN)

# 初始化 JSON 文件
if not os.path.exists(SIGN_FILE):
    with open(SIGN_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

def load_data():
    try:
        with open(SIGN_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return []

def save_data(data):
    with open(SIGN_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ============ 指令逻辑 ============

@bot.message_handler(commands=['start', 'zl'])
def show_menu(message):
    if message.from_user.id != ADMIN_ID:
        return # ID不匹配则不响应
    menu = (
        "🤖 **自动签到控制系统**\n\n"
        "📋 **任务查看:**\n"
        "/list - 查看所有签到目标\n\n"
        "✨ **任务管理:**\n"
        "/add 名称 @用户名 命令\n"
        "/del @用户名\n\n"
        "💡 **运行说明:**\n"
        "1. 使用 `/add` 添加目标，例如: `/add 小纸条 sdxhzbot /qd`\n"
        "2. 系统会在北京时间 00:00 和 12:00 自动尝试签到。\n"
        "3. 执行动作由后台 `auto_sign.py` 使用个人号完成。"
    )
    bot.reply_to(message, menu, parse_mode='Markdown')

@bot.message_handler(commands=['list'])
def list_bots(message):
    if message.from_user.id != ADMIN_ID: return
    data = load_data()
    if not data:
        return bot.reply_to(message, "📋 签到列表为空。")
    
    res = "📋 **当前签到列表:**\n\n"
    for i, b in enumerate(data, 1):
        res += f"{i}. {b['name']}\n   账号: @{b['bot_username']}\n   指令: `{b['command']}`\n\n"
    bot.reply_to(message, res, parse_mode='Markdown')

@bot.message_handler(commands=['add'])
def add_bot(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        return bot.reply_to(message, "⚠️ 格式: `/add 名称 @用户名 指令`")
    
    name, username, command = parts[1], parts[2].replace("@", ""), parts[3]
    data = load_data()
    data.append({"name": name, "bot_username": username, "command": command})
    save_data(data)
    bot.reply_to(message, f"✅ 已添加目标: {name}")

@bot.message_handler(commands=['del'])
def del_bot(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "⚠️ 格式: `/del @用户名`")
    
    target = parts[1].replace("@", "")
    data = load_data()
    new_data = [b for b in data if b['bot_username'] != target]
    save_data(new_data)
    bot.reply_to(message, f"🗑️ 已移除: @{target}")

# ID 测试指令：如果你发现不理你，发这个看 ID 对不对
@bot.message_handler(commands=['myid'])
def myid(message):
    bot.reply_to(message, f"你的 ID 是: `{message.from_user.id}`", parse_mode='Markdown')

if __name__ == '__main__':
    print("✅ 签到管理后台已运行 (使用新Token)...")
    bot.infinity_polling()
