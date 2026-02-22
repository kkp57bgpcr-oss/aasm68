#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import telebot
import json
import os

# ============ 核心配置 ============
# 使用和你 main 代码一样的 Token，但注意不要同时开启 polling 否则会冲突
API_TOKEN = '8338893180:AAH-l_4m1-tweKyt92bliyk4fsPqoPQWzpU'
ADMIN_ID = 6649617045
SIGN_FILE = 'sign_targets.json'

bot = telebot.TeleBot(API_TOKEN)

# 确保配置文件存在
if not os.path.exists(SIGN_FILE):
    with open(SIGN_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f)

def load_data():
    with open(SIGN_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_data(data):
    with open(SIGN_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# ============ 指令处理 ============

@bot.message_handler(commands=['zl'])
def show_menu(message):
    if message.from_user.id != ADMIN_ID: return
    menu = (
        "🤖 **控制命令:**\n\n"
        "📋 **状态查询:**\n"
        "/status - 查看状态\n"
        "/list - 查看签到机器人列表\n\n"
        "✨ **签到控制:**\n"
        "/sign_now - 立即签到一次\n"
        "/add_bot 名称 @用户名 命令 - 添加签到机器人\n"
        "/del_bot @用户名 - 删除签到机器人\n\n"
        "📝 **手动消息:**\n"
        "/send @用户名 消息 - 发送消息\n\n"
        "🔧 **其他:**\n"
        "/help - 查看帮助"
    )
    bot.reply_to(message, menu, parse_mode='Markdown')

@bot.message_handler(commands=['list'])
def list_bots(message):
    if message.from_user.id != ADMIN_ID: return
    data = load_data()
    if not data:
        return bot.reply_to(message, "📋 当前签到列表为空。")
    
    res = "📋 **签到机器人列表:**\n"
    for i, b in enumerate(data, 1):
        res += f"{i}. {b['name']} (@{b['bot_username']}) -> `{b['command']}`\n"
    bot.reply_to(message, res, parse_mode='Markdown')

@bot.message_handler(commands=['add_bot'])
def add_bot(message):
    if message.from_user.id != ADMIN_ID: return
    parts = message.text.split(maxsplit=3)
    if len(parts) < 4:
        return bot.reply_to(message, "⚠️ 用法: `/add_bot 名称 @用户名 命令`", parse_mode='Markdown')
    
    name, username, command = parts[1], parts[2].replace("@", ""), parts[3]
    data = load_data()
    data.append({"name": name, "bot_username": username, "command": command})
    save_data(data)
    bot.reply_to(message, f"✅ 已添加签到目标: {name} (@{username})")

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
        bot.reply_to(message, f"🗑️ 已成功删除 @{target}")

@bot.message_handler(commands=['status'])
def check_status(message):
    if message.from_user.id != ADMIN_ID: return
    data = load_data()
    bot.reply_to(message, f"📊 **运行状态:**\n- 监控中目标数: {len(data)}\n- 自动执行时间: 00:00 / 12:00\n- 执行账号: 已在 auto_sign.py 中配置", parse_mode='Markdown')

if __name__ == '__main__':
    print("✅ 签到管理机器人 (sign_manager) 已启动...")
    bot.infinity_polling()
