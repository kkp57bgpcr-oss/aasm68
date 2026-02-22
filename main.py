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
from telethon import TelegramClient
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

# Telegram 用户号配置
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
sign_in_status = {}

# 导入测压模块
try:
    import sms_list 
    import sms_list_new
    from sms_list import *
except:
    pass

# ================= 2. 数据持久化 =================

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

# ================= 3. 用户号自动签到逻辑 (协程) =================

async def run_sign_in_task(client):
    print("📅 [系统] 自动签到协程已就绪")
    while True:
        try:
            now = datetime.now()
            # 每天 12点 和 0点 执行
            if now.hour in [12, 0] and now.minute == 0:
                print(f"🚀 [签到] 开始执行例行签到...")
                for b in SIGN_IN_BOTS:
                    try:
                        await client.send_message(b['bot_username'], b['command'])
                        sign_in_status[b['name']] = f"✅ {now.strftime('%m-%d %H:%M')}"
                        await asyncio.sleep(random.randint(3, 7))
                    except Exception as e:
                        sign_in_status[b['name']] = f"❌ 失败"
                await asyncio.sleep(60) # 防止在同一分钟重复触发
            await asyncio.sleep(30)
        except Exception as e:
            await asyncio.sleep(30)

async def init_user_client():
    client = TelegramClient("my_account.session", TG_API_ID, TG_API_HASH)
    await client.connect()
    if not await client.is_user_authorized():
        print(f"🚨 [账号] 未检测到登录状态，开始验证: {USER_PHONE}")
        await client.send_code_request(USER_PHONE)
        code = input("请输入手机收到的 Telegram 验证码: ")
        try:
            await client.sign_in(USER_PHONE, code)
        except SessionPasswordNeededError:
            password = input("请输入两步验证密码: ")
            await client.sign_in(password=password)
    print("✅ [账号] 用户号登录成功")
    asyncio.create_task(run_sign_in_task(client))
    return client

# ================= 4. 业务功能函数 =================

def get_id_check_code(id17):
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    rem_map = {0: '1', 1: '0', 2: 'X', 3: '9', 4: '8', 5: '7', 6: '6', 7: '5', 8: '4', 9: '3', 10: '2'}
    try:
        sum_val = sum(int(id17[i]) * factors[i] for i in range(17))
        return rem_map[sum_val % 11]
    except: return "X"

def cp_query_logic(chat_id, car_no, uid):
    url = f"http://zgzapi.idc.cn.com/车档.php?key=体验卡&cph={urllib.parse.quote(car_no)}"
    try:
        response = requests.get(url, timeout=15)
        response.encoding = 'utf-8'
        raw_res = response.text.strip()
        if raw_res and "未找到" not in raw_res and "错误" not in raw_res:
            user_points[uid] -= 2.5
            save_points()
            bot.send_message(chat_id, f"车牌查询结果:\n\n车牌号：{car_no}\n详细信息：\n{raw_res}\n\n已扣除 2.5 积分！\n当前余额: {user_points[uid]:.2f}")
        else:
            bot.send_message(chat_id, f"车牌查询结果:\n\n未匹配到有效车档信息。\n\n查询无结果，不扣分。\n余额: {user_points[uid]:.2f}")
    except:
        bot.send_message(chat_id, "⚠️ 接口请求失败")

def xiaowunb_query_logic(chat_id, id_number, uid):
    base_url = "http://xiaowunb.top/cyh.php"
    try:
        response = requests.get(base_url, params={"sfz": id_number}, timeout=10)
        response.encoding = 'utf-8'
        phones = re.findall(r'1[3-9]\d{9}', response.text)
        if phones:
            user_points[uid] -= 1.5
            save_points()
            unique_phones = list(dict.fromkeys(phones))
            phone_list = "\n".join([f"{idx+1}、{p}" for idx, p in enumerate(unique_phones)])
            bot.send_message(chat_id, f"身份证查询结果:\n\n匹配到 {len(unique_phones)} 个手机号:\n{phone_list}\n\n已扣除 1.5 积分！")
        else:
            bot.send_message(chat_id, "未匹配到有效手机号，不扣分。")
    except:
        bot.send_message(chat_id, "❌ 接口超时")

def query_3ys_logic(chat_id, name, id_card, phone, uid):
    url = "http://xiaowunb.top/3ys.php"
    try:
        response = requests.get(url, params={"name": name, "sfz": id_card, "sjh": phone}, timeout=15)
        response.encoding = 'utf-8'
        user_points[uid] -= 0.05
        save_points()
        clean_res = re.sub(r'小无 API.*?官方客服:@\w+', '', response.text, flags=re.DOTALL).strip()
        res_status = "三要素核验成功✅" if ("成功" in clean_res or "一致" in clean_res) else "三要素核验失败❌"
        bot.send_message(chat_id, f"姓名：{name}\n手机：{phone}\n结果：{res_status}\n\n已扣 0.05 积分！\n余额：{user_points[uid]:.2f}")
    except:
        bot.send_message(chat_id, "⚠️ 系统异常")

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.01
        save_points()
        res_type = "核验一致✅" if r.json().get("success") else "验证失败 ❌"
        bot.send_message(chat_id, f"姓名: {name}\n结果: {res_type}\n\n已扣 0.01 积分！\n余额：{user_points[uid]:.2f}")
    except:
        bot.send_message(chat_id, "❌ 接口报错")

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
        bot.send_message(message.chat.id, f"✅ 目标 `{target}` 任务完毕")
    threading.Thread(target=do_bomb).start()

# ================= 6. 界面与指令控制 =================

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("使用帮助", callback_data="view_help"), 
        types.InlineKeyboardButton("在线充值", callback_data="view_pay"),
        types.InlineKeyboardButton("📋 签到状态", callback_data="view_sign")
    )
    return markup

def get_pay_markup():
    admin_url = f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(
        types.InlineKeyboardButton("USDT/OkPay/RMB 充值", url=admin_url), 
        types.InlineKeyboardButton("🔙 返回", callback_data="back_to_main")
    )
    return markup

@bot.message_handler(commands=['start', 'cyh', '3ys', '2ys', 'cp', 'bq', 'add'])
def handle_commands(message):
    uid, chat_id = message.from_user.id, message.chat.id
    cmd = message.text.split()[0][1:]
    
    if cmd == 'start':
        if uid not in user_points: user_points[uid] = 0.0
        txt = f"Admin@铭\n\n用户 ID: `{uid}`\n当前余额: `{user_points[uid]:.2f}积分`"
        bot.send_message(chat_id, txt, parse_mode='Markdown', reply_markup=get_main_markup())
    elif cmd == 'add' and uid == ADMIN_ID:
        try:
            p = message.text.split(); tid, amt = int(p[1]), float(p[2])
            user_points[tid] = user_points.get(tid, 0.0) + amt; save_points()
            bot.reply_to(message, f"✅ 充值成功！余额: `{user_points[tid]:.2f}`")
        except: pass
    elif cmd == 'cyh':
        user_states[chat_id] = {'step': 'cyh_id'}; bot.send_message(chat_id, "请输入要查询的身份证号：")
    elif cmd == 'cp':
        user_states[chat_id] = {'step': 'v_cp'}; bot.send_message(chat_id, "请输入车牌号：")
    elif cmd == '3ys':
        user_states[chat_id] = {'step': 'v_3ys'}; bot.send_message(chat_id, "请输入：姓名 手机号 身份证")
    elif cmd == '2ys':
        user_states[chat_id] = {'step': 'v_2ys'}; bot.send_message(chat_id, "请输入：姓名 身份证")
    elif cmd == 'bq':
        user_states[chat_id] = {'step': 'g_card'}; bot.send_message(chat_id, "请输入身份证号（未知位用x）：")

@bot.message_handler(func=lambda m: True)
def handle_all_msg(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return
    
    # 状态机逻辑
    state = user_states.get(chat_id)
    if state:
        step = state.get('step')
        if step == 'v_cp':
            del user_states[chat_id]; cp_query_logic(chat_id, text.upper(), uid)
        elif step == 'cyh_id':
            del user_states[chat_id]; xiaowunb_query_logic(chat_id, text, uid)
        elif step == 'v_3ys':
            del user_states[chat_id]
            parts = re.split(r'[,，\s\n]+', text)
            if len(parts) >= 3: query_3ys_logic(chat_id, parts[0], parts[2], parts[1], uid)
        elif step == 'v_2ys':
            del user_states[chat_id]
            parts = re.split(r'[,，\s\n]+', text)
            if len(parts) >= 2: single_verify_2ys(chat_id, parts[0], parts[1], uid)
        elif step == 'g_card':
            user_states[chat_id].update({'step': 'g_sex', 'card': text.lower()})
            bot.send_message(chat_id, "请输入性别 (男/女):")
        elif step == 'g_sex':
            user_points[uid] -= 0.1; save_points()
            base_17 = state['card'][:17]
            char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in base_17]
            if text == "男": char_sets[16] = [c for c in char_sets[16] if int(c) % 2 != 0]
            else: char_sets[16] = [c for c in char_sets[16] if int(c) % 2 == 0]
            ids = [s17 + get_id_check_code(s17) for s17 in ["".join(res) for res in itertools.product(*char_sets)]]
            with open("铭.txt", "w", encoding="utf-8") as f: f.write("\n".join(ids))
            with open("铭.txt", "rb") as f: bot.send_document(chat_id, f, caption=f"✅ 生成成功！消耗0.1积分")
            del user_states[chat_id]
        return

    # 自动识别逻辑
    if re.match(r'^[京津沪渝冀豫云辽黑湖南皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1}[A-Z]{1}[A-Z0-9]{5,6}$', text.upper()):
        if user_points.get(uid, 0.0) < 2.5: return bot.reply_to(message, "积分不足(2.5)")
        cp_query_logic(chat_id, text.upper(), uid)
    elif re.match(r'^\d{17}[\dXx]$|^\d{15}$', text):
        if user_points.get(uid, 0.0) < 1.5: return bot.reply_to(message, "积分不足(1.5)")
        xiaowunb_query_logic(chat_id, text, uid)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = call.from_user.id
    if call.data == "view_help":
        help_text = (
            "🛠️️ **使用帮助**\n\n"
            "🚀 **短信测压**: 发送 `/sms 手机号` (3.5积分)\n"
            "🆔 **补齐身份证**: 发送 `/bq` 操作 (0.1积分)\n"
            "✅ **二要素核验**: 发送 `/2ys` 姓名+身份证 (0.01积分)\n"
            "✅ **三要素核验**: 发送 `/3ys` 姓名+手机+身份证 (0.05积分)\n"
            "🚗 **车牌查询**: 发送 `/cp` 车牌号 (2.5积分)\n"
            "🔍 **常用号查询**: 发送 `/cyh` 身份证 (1.5积分)\n"
            "——————————————————\n"
            "💡 **自动识别**: 直接发送车牌或身份证即可自动查询"
        )
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 返回", callback_data="back_to_main")))
    elif call.data == "view_pay":
        bot.edit_message_text("🛍️ **充值方式**\n\n1 USDT = 1 积分\n联系管理充值，支持USDT/OkPay/RMB", call.message.chat.id, call.message.message_id, reply_markup=get_pay_markup())
    elif call.data == "view_sign":
        res = "📋 **自动签到监控**\n\n"
        for name, stat in sign_in_status.items(): res += f"🔹 {name}: {stat}\n"
        if not sign_in_status: res += "等待首次执行..."
        bot.edit_message_text(res, call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 返回", callback_data="back_to_main")))
    elif call.data == "back_to_main":
        txt = f"Admin@铭\n\n用户 ID: `{uid}`\n当前余额: `{user_points.get(uid,0.0):.2f}积分`"
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_main_markup())

# ================= 7. 启动入口 =================

def run_bot():
    print("🤖 [系统] 主机器人轮询已启动")
    bot.infinity_polling()

async def main():
    # 初始化并登录用户号（如果需要验证码会在控制台弹出）
    user_client = await init_user_client()
    
    # 在独立线程跑 Telebot，防止阻塞
    threading.Thread(target=run_bot, daemon=True).start()
    
    # 保持主进程活跃
    await user_client.run_until_disconnected()

if __name__ == "__main__":
    if sys.platform == "win32": os.system("chcp 65001 >nul")
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n停止运行")
