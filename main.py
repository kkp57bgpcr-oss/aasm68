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
import sms_list 
import sms_list_new
from sms_list import *
from Crypto.Cipher import DES3
from datetime import datetime
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

# 三要素/二要素 接口 Authorization
AUTH_BEARER = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpblR5cGUiOiJsb2dpbiIsImxvZ2luSWQiOiJhcHBfdXNlcjoxMTc1NDYwIiwicm5TdHIiOiJJSmVrU005UTlHc2hTV2RiVENQZ1VFbnpDN0MwWjFYZCJ9.vxjF6ShG81TM2hT-uiYyubHGOlEuCKC-m8nSmi7sayU"

bot = telebot.TeleBot(API_TOKEN)
user_points = {}
CURRENT_X_TOKEN = DEFAULT_TOKEN
user_states = {}
generated_cache = {} 

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

def save_token(new_tk):
    global CURRENT_X_TOKEN
    CURRENT_X_TOKEN = new_tk
    with open(TOKEN_FILE, 'w', encoding='utf-8') as f:
        f.write(new_tk)

# ================= 2. 核心界面生成 (恢复原样) =================

def get_main_text(source, uid, pts):
    # 尝试获取昵称和用户名
    first_name = source.from_user.first_name if hasattr(source.from_user, 'first_name') else "用户"
    username = f"@{source.from_user.username}" if hasattr(source.from_user, 'username') and source.from_user.username else "未设置"
    
    return (f"Admin@铭\n\n"
            f"用户 ID: `{uid}`\n"
            f"用户名称: `{first_name}`\n"
            f"用户名: {username}\n"
            f"当前余额: `{pts:.2f} 积分`\n\n"
            f"使用帮助可查看使用教程\n"
            f"在线充值可支持 24 小时\n"
            f"1 USDT = 1 积分")

def get_help_text():
    return (
        "🛠️ **使用帮助**\n\n"
        "**短信测压**\n发送 `/sms 手机号` 消耗 3.5 积分\n"
        "——————————————————\n"
        "**批量二要素核验**\n发送 `/pl` 进行批量操作 消耗 2.5 积分\n"
        "——————————————————\n"
        "**补齐身份证and核验**\n发送 `/bq` 进行操作 消耗 0.1 积分\n"
        "——————————————————\n"
        "**名字-身份证核验（企业级)**\n全天 24h 秒出，消耗 0.01 积分\n"
        "直接发送：`姓名 身份证` 即可自动识别\n"
        "——————————————————\n"
        "**名字-手机-身份证核验（企业级)**\n消耗 0.05 积分\n"
        "直接发送：`姓名 身份证 手机号` 即可自动识别\n"
        "——————————————————\n"
        "**常用号查询**\n发送 `/cyh` 进行查询 消耗 1.5 积分"
    )

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("使用帮助", callback_data="view_help"),
               types.InlineKeyboardButton("在线充值", callback_data="view_pay"))
    return markup

def get_pay_markup():
    admin_url = f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("联系管理员充值", url=admin_url),
               types.InlineKeyboardButton("🔙 返回", callback_data="back_to_main"))
    return markup

# ================= 3. 业务逻辑 =================

def query_3ys_logic(chat_id, name, id_card, phone, uid):
    url = "https://esb.wbszkj.cn/prod-api/wxminiapp/user/userIdVerify"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json"}
    data = {"name": name, "phone": phone, "idNo": id_card, "idType": 1}
    try:
        response = requests.post(url, headers=headers, json=data, verify=False, timeout=10)
        user_points[uid] -= 0.05; save_points()
        status = "三要素核验一致✅" if response.status_code == 200 and response.json().get("success") else "三要素核验不一致❌"
        res = f"名字：{name}\n手机号：{phone}\n身份证：{id_card}\n结果：{status}\n\n已扣除 0.05 积分！\n当前余额：{user_points[uid]:.2f}"
        bot.send_message(chat_id, res)
    except: bot.send_message(chat_id, "❌ 接口超时")

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    try:
        r = requests.post(url, headers={"Authorization": AUTH_BEARER}, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.01; save_points()
        status = "二要素核验一致✅" if r.json().get("success") else "二要素核验不一致❌"
        res = f"姓名: {name}\n身份证: {id_card}\n结果: {status}\n\n已扣除 0.01 积分！\n当前余额：{user_points[uid]:.2f}"
        bot.send_message(chat_id, res)
    except: bot.send_message(chat_id, "❌ 接口超时")

def xiaowunb_query_logic(chat_id, id_number, uid):
    try:
        r = requests.get(f"http://xiaowunb.top/cyh.php?sfz={id_number}", timeout=10)
        user_points[uid] -= 1.5; save_points()
        bot.send_message(chat_id, f"📑 **查询结果**\n\n{r.text}\n\n已扣除 1.5 积分")
    except: bot.send_message(chat_id, "❌ 查询失败")

# --- 短信测压与批量核验函数省略（此处逻辑保持您原本 main.py 中的完整版，不删减功能） ---
# [此处建议保留您原本文件中的 get_all_senders, run_batch_task 等高级功能代码]

# ================= 4. 核心入口 =================

@bot.message_handler(commands=['start', 'sms', 'pl', 'bq', 'cyh', '3ys', '2ys'])
def handle_cmds(message):
    uid, chat_id = message.from_user.id, message.chat.id
    cmd = message.text.split()[0][1:]
    if cmd == 'start':
        if uid not in user_points: user_points[uid] = 0.0
        bot.send_message(chat_id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())
    elif cmd == '3ys':
        user_states[chat_id] = {'step': 'v_3ys'}; bot.send_message(chat_id, "请输入：姓名 身份证 手机号")
    # ... 其他指令如 sms/pl/bq 保持原样逻辑即可 ...

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return 

    # --- 自动识别逻辑 ---
    if chat_id not in user_states or not user_states[chat_id].get('step'):
        id_search = re.search(r'(\d{18}|\d{17}[Xx]|\d{15})', text)
        phone_search = re.search(r'(1[3-9]\d{9})', text)
        name_search = re.search(r'[\u4e00-\u9fa5]{2,4}', text)

        if id_search and phone_search and name_search:
            return query_3ys_logic(chat_id, name_search.group(), id_search.group().upper(), phone_search.group(), uid)
        if id_search and name_search and not phone_search:
            return single_verify_2ys(chat_id, name_search.group(), id_search.group().upper(), uid)
        if id_search and not name_search:
            return xiaowunb_query_logic(chat_id, id_search.group().upper(), uid)

    # --- 状态机分步处理 (pl, bq 等) ---
    # [这里保留您原本的代码逻辑]

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = call.from_user.id
    pts = user_points.get(uid, 0.0)
    if call.data == "view_help":
        bot.edit_message_text(get_help_text(), call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_pay_markup())
    elif call.data == "view_pay":
        bot.edit_message_text("🛍️ **充值中心**\n\n1 USDT = 1 积分\n请联系管理员进行人工充值。", call.message.chat.id, call.message.message_id, reply_markup=get_pay_markup())
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(call, uid, pts), call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_main_markup())

if __name__ == '__main__':
    bot.infinity_polling()
