#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import telebot
import json
import os

# ============ 核心配置 ============
# 已更新为你的新机器人 Token
API_TOKEN = '8505048236:AAFHPC3448Gti60whSAC9mak_oKzd7BN1eY'
ADMIN_ID = 6649617045
SIGN_FILE = 'sign_targets.json'

bot = telebot.TeleBot(API_TOKEN)

# 确保配置文件存在
if not os.path.exists(SIGN_FILE):
    with open(SIGN_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

def load_data():
    with open(SIGN_FILE, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except:
            return []

def save_data(data):
    with open(SIGN_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ============ 指令处理 ============

@bot.message_handler(commands=['start', 'zl'])
def show_menu(message):
    if message.from_user.id != ADMIN_ID: return
    menu = (
        "🤖 **签到助手管理后台**\n\n"
        "📋 **状态查询:**\n"
        "/list - 查看当前签到机器人列表\n"
        "/status - 查看运行环境状态\n\n"
        "✨ **管理控制:**\n"
        "/add_bot 名称 @用户名 命令\n"
        "/del_bot @用户名\n\n"
        "🔧 **说明:**\n"
        "本机器人仅负责名单管理，具体发消息动作由执行进程按时完成 (00:00/12:00)。"
    )
    bot.reply_to(message, menu, parse_mode='Markdown')

@bot.message_handler(commands=['list'])
def list_bots(message):
    if message.from_user.id != ADMIN_ID: return
    data = load_data()
    if not data:
        return bot.reply_to(message, "📋 当前列表为空。")
    
    res = "📋 **签到列表:**\n"
    for i, b in enumerate(data, 1):
        res += f"{i}. {b['name']} (@{b['bot_username']}) -> `{b['command']}`\n"
    bot.reply_to(message, res, parse_mode='Markdown')

@bot.message_handler(commands=['add_bot'])
def add_bot(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        return bot.reply_to(message, "⚠️ 用法: `/add_bot 名称 @用户名 命令`\n例: `/add_bot 小纸条 sdxhzbot /qd`", parse_mode='Markdown')
    
    name, username, command = parts[1], parts[2].replace("@", ""), parts[3]
    data = load_data()
    data.append({"name": name, "bot_username": username, "command": command})
    save_data(data)
    bot.reply_to(message, f"✅ 已添加目标: {name} (@{username})")

@bot.message_handler(commands=['del_bot'])
def del_bot(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split()
    if len(parts) < 2:
        return bot.reply_to(message, "⚠️ 用法: `/del_bot @用户名`", parse_mode='Markdown')
    
    target = parts[1].replace("@", "")
    data = load_data()
    new_data = [b for b in data if b['bot_username'] != target]
    
    if len(data) == len(new_data):
        bot.reply_to(message, f"❌ 未在列表中找到 @{target}")
    else:
        save_data(new_data)
        bot.reply_to(message, f"🗑️ 已成功移除 @{target}")

@bot.message_handler(commands=['status'])
def check_status(message):
    if message.from_user.id != ADMIN_ID: return
    data = load_data()
    bot.reply_to(message, f"📊 **运行状态:**\n- 任务总数: {len(data)}\n- 自动执行时间: 00:00 / 12:00\n- 配置同步: 实时读取 JSON", parse_mode='Markdown')

if __name__ == '__main__':
    print(f"✅ 管理机器人已启动，请在 Telegram 中对新 Bot 发送 /zl")
    bot.infinity_polling()
