import telebot
import requests
import time
import re
import threading
import json
import os
import itertools
import binascii
import random
import concurrent.futures
import inspect  
import urllib.parse
from telebot import types
from concurrent.futures import ThreadPoolExecutor

# 屏蔽 SSL 证书报警
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ================= 1. 核心配置 =================
API_TOKEN = '8338893180:AAH-l_4m1-tweKyt92bliyk4fsPqoPQWzpU'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'
TOKEN_FILE = 'token.txt'
DEFAULT_TOKEN = "eyJhbGciOiJIUzUxMiIsInR5cCI6IkpXVCJ9.eyJ1c2VySWQiOiIyNDkyNDYiLCJpYXQiOjE3Mzg1MDMxMTcsImV4cCI6MTczODY3NTkxN30.i9w1G8Y2mU5R5cCI6IkpXVCJ9" 
AUTH_BEARER = "bearer eyJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6IisxOTM3ODg4NDgyNiIsIm9wZW5JZCI6Im95NW8tNHk3Wnd0WGlOaTVHQ3V3YzVVNDZJYk0iLCJpZENhcmRObyI6IjM3MDQ4MTE5ODgwODIwMzUxNCIsInVzZXJOYW1lIjoi6ams5rCR5by6IiwibG9naW5UaW1lIjoxNzY5NDE1NjYxMTk0LCJhcHBJZCI6Ind4ZjVmZDAyZDEwZGJiMjFkMiIsImlzcmVhbG5hbWUiOnRydWUsInNhYXNVc2VySWQiOm51bGwsImNvbXBhbnlJZCI6bnVsbCwiY29tcGFueVZPUyI6bnVsbH0.GwMYvckFHvFbhSi0NXpQDPiv9ZswUBAImN5bUipBla0"

bot = telebot.TeleBot(API_TOKEN)
user_points = {}
CURRENT_X_TOKEN = DEFAULT_TOKEN
user_states = {}

# --- 数据持久化 ---
def load_data():
    pts = {}
    if os.path.exists(POINTS_FILE):
        try:
            with open(POINTS_FILE, 'r') as f:
                data = json.load(f)
                pts = {int(k): float(v) for k, v in data.items()}
        except: pass
    tk = DEFAULT_TOKEN
    if os.path.exists(TOKEN_FILE):
        try:
            with open(TOKEN_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if content: tk = content
        except: pass
    return pts, tk

user_points, CURRENT_X_TOKEN = load_data()

def save_points():
    with open(POINTS_FILE, 'w') as f:
        json.dump({str(k): v for k, v in user_points.items()}, f)

# ================= 2. 严格对齐截图的 UI =================

def get_main_text(source, uid, pts):
    first_name = source.from_user.first_name if hasattr(source.from_user, 'first_name') else "铭"
    username = f"@{source.from_user.username}" if hasattr(source.from_user, 'username') and source.from_user.username else "未设置"
    return (f"Admin@铭\n\n"
            f"用户 ID: `{uid}`\n"
            f"用户名称: `{first_name}`\n"
            f"用户名: {username}\n"
            f"当前余额: `{pts:.2f}积分`\n\n"
            f"使用帮助可查看使用教程\n"
            f"在线充值可支持24小时\n"
            f"1 USDT = 1 积分\n"

def get_help_text():
    return (
        "🛠️️使用帮助\n"
        "短信测压\n"
        "发送 /sms 手机号\n"
        "每次消耗 3.5 积分\n"
        "——————————————————\n"
        "批量二要素核验\n"
        "发送 /pl 进行核验\n"
        "每次核验扣除 2.5 积分\n"
        "——————————————————\n"
        "补齐身份证and核验\n"
        "发送 /bq 进行操作\n"
        "每次补齐扣除 0.1 积分\n"
        "——————————————————\n"
        "名字-身份证核验（企业级）\n"
        "全天24h秒出 毫秒级响应\n"
        "发送 /2ys 进行核验\n"
        "每次核验扣除 0.01 积分\n"
        "——————————————————\n"
        "名字-手机号-身份证核验（企业级）\n"
        "发送 /3ys 进行核验\n"
        "每次扣除 0.05 积分\n"
        "——————————————————\n"
        "常用号查询\n"
        "发送 /cyh 进行查询\n"
        "每次查询扣除 1.5 积分 空不扣除积分"
    )

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("使用帮助", callback_data="view_help"),
               types.InlineKeyboardButton("在线充值", callback_data="view_pay"))
    return markup

# ================= 3. 业务逻辑 (去链接版) =================

def query_3ys_logic(chat_id, name, id_card, phone, uid):
    url = "https://esb.wbszkj.cn/prod-api/wxminiapp/user/userIdVerify"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json"}
    data = {"name": name, "phone": phone, "idNo": id_card, "idType": 1}
    try:
        r = requests.post(url, headers=headers, json=data, verify=False, timeout=10)
        user_points[uid] -= 0.05
        save_points()
        is_ok = r.status_code == 200 and r.json().get("success")
        status = "三要素核验一致✅" if is_ok else "三要素核验不一致❌"
        res = (f"名字：{name}\n手机号：{phone}\n身份证：{id_card}\n结果：{status}\n\n"
               f"已扣除 0.05 积分！\n当前积分余额：{user_points[uid]:.2f} 积分")
        bot.send_message(chat_id, res)
    except: bot.send_message(chat_id, "❌ 接口超时")

# ================= 4. 解决指令无反应逻辑 =================

@bot.message_handler(commands=['start', 'add', 'sms', 'pl', 'bq', 'cyh', '2ys', '3ys'])
def handle_commands(message):
    uid, chat_id = message.from_user.id, message.chat.id
    cmd = message.text.split()[0][1:]
    
    if cmd == 'start':
        if uid not in user_points: user_points[uid] = 0.0
        bot.send_message(chat_id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())
    elif cmd == 'add' and uid == ADMIN_ID:
        try:
            p = message.text.split()
            tid, amt = int(p[1]), float(p[2])
            user_points[tid] = user_points.get(tid, 0.0) + amt; save_points()
            bot.reply_to(message, f"✅ 已充值！当前余额: `{user_points[tid]:.2f}`")
        except: bot.reply_to(message, "用法: /add ID 积分")
    # 其他指令按原逻辑处理...

@bot.message_handler(func=lambda m: True)
def handle_text_recognition(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return # 跳过指令，指令由上面 handle_commands 处理

    parts = re.split(r'[,/\s]+', text)
    if len(parts) == 3: # 自动识别三要素
        n, p, i = None, None, None
        for x in parts:
            if re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
            elif re.match(r'^1[3-9]\d{9}$', x): p = x
            elif re.match(r'^[\dXx]{15,18}$', x): i = x.upper()
        if n and p and i:
            if user_points.get(uid, 0.0) < 0.05: return bot.reply_to(message, "积分不足")
            return query_3ys_logic(chat_id, n, i, p, uid)
    # [其他自动识别逻辑...]

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid, pts = call.from_user.id, user_points.get(call.from_user.id, 0.0)
    if call.data == "view_help":
        bot.edit_message_text(get_help_text(), call.message.chat.id, call.message.message_id)
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(call, uid, pts), call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_main_markup())

if __name__ == '__main__':
    bot.infinity_polling()
