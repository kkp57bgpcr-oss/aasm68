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

# ================= 2. 核心查询逻辑 (铭哥定制版) =================

# --- 三要素查询逻辑 ---
def query_3ys_logic(chat_id, name, id_card, phone, uid):
    url = "https://esb.wbszkj.cn/prod-api/wxminiapp/user/userIdVerify"
    headers = {
        "Authorization": AUTH_BEARER,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X)"
    }
    data = {
        "name": name,
        "phone": phone,
        "idNo": id_card,
        "idType": 1,
        "idFrontFile": "https://guarantee-file.wbszkj.cn/gcb/prod/demo_front.jpg",
        "idBackFile": "https://guarantee-file.wbszkj.cn/gcb/prod/demo_back.jpg"
    }
    try:
        response = requests.post(url, headers=headers, json=data, verify=False, timeout=10)
        user_points[uid] -= 0.05
        save_points()
        
        if response.status_code == 200:
            result = response.json()
            # 这里的判断逻辑根据实际接口返回的 success 字段
            status = "三要素核验一致✅" if result.get("success") == True else "三要素核验不一致❌"
            res_msg = (f"名字：{name}\n手机号：{phone}\n身份证：{id_card}\n结果：{status}\n\n"
                       f"已扣除 0.05 积分！\n当前余额：{user_points[uid]:.2f}")
        else:
            res_msg = f"❌ 接口请求失败，状态码: {response.status_code}"
        bot.send_message(chat_id, res_msg)
    except Exception as e:
        bot.send_message(chat_id, f"❌ 三要素查询出错：{str(e)}")

# --- 二要素查询逻辑 (修复自动识别的关键) ---
def single_verify_2ys(chat_id, name, id_card, uid):
    # 这里使用的是你截图中的 xhmxb 接口或类似的二要素接口
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.01
        save_points()
        
        res_json = r.json()
        # 根据你的需求，修改返回文字
        status = "二要素核验一致✅" if res_json.get("success") == True else "二要素核验不一致❌"
        
        res_msg = (f"姓名: {name}\n身份证: {id_card}\n结果: {status}\n\n"
                   f"已扣除 0.01 积分！\n当前余额：{user_points[uid]:.2f}")
        bot.send_message(chat_id, res_msg)
    except Exception as e:
        bot.send_message(chat_id, f"❌ 二要素核验出错: {str(e)}")

# --- 常用号查询 ---
def xiaowunb_query_logic(chat_id, id_number, uid):
    base_url = "http://xiaowunb.top/cyh.php"
    params = {"sfz": id_number}
    try:
        response = requests.get(base_url, params=params, timeout=10)
        response.encoding = 'utf-8'
        user_points[uid] -= 1.5
        save_points()
        res_text = response.text if response.text.strip() else "查询结果为空"
        result_message = f"📑 **身份查询结果**\n\n{res_text}\n\n已扣除 **1.5** 积分！\n当前余额: **{user_points[uid]:.2f}**"
        bot.send_message(chat_id, result_message, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 常用号查询失败: {e}")

# ================= 3. 辅助功能 (菜单、计算等) =================

def get_id_check_code(id17):
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    rem_map = {0: '1', 1: '0', 2: 'X', 3: '9', 4: '8', 5: '7', 6: '6', 7: '5', 8: '4', 9: '3', 10: '2'}
    try:
        sum_val = sum(int(id17[i]) * factors[i] for i in range(17))
        return rem_map[sum_val % 11]
    except: return "X"

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("使用帮助", callback_data="view_help"),
               types.InlineKeyboardButton("在线充值", callback_data="view_pay"))
    return markup

def get_pay_markup():
    admin_url = f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("在线充值联系管理员", url=admin_url),
               types.InlineKeyboardButton("🔙 返回主菜单", callback_data="back_to_main"))
    return markup

def get_main_text(uid, pts):
    return (f"Admin@铭\n\n用户 ID: `{uid}`\n当前余额: `{pts:.2f} 积分`\n\n1 USDT = 1 积分\n直接发送：姓名 身份证 手机号 (自动识别三要素)\n直接发送：姓名 身份证 (自动识别二要素)")

# ================= 4. 核心逻辑入口 (解决二要素识别消失) =================

@bot.message_handler(commands=['start', '3ys', '2ys', 'cyh', 'add', 'set_token'])
def handle_commands(message):
    uid, chat_id = message.from_user.id, message.chat.id
    cmd = message.text.split()[0][1:]
    
    if cmd == 'start':
        if uid not in user_points: user_points[uid] = 0.0
        bot.send_message(chat_id, get_main_text(uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())
    elif cmd == 'add' and uid == ADMIN_ID:
        try:
            p = message.text.split(); tid, amt = int(p[1]), float(p[2])
            user_points[tid] = user_points.get(tid, 0.0) + amt; save_points()
            bot.reply_to(message, f"✅ 已为 {tid} 充值 {amt}！当前: {user_points[tid]}")
        except: pass
    elif cmd == '3ys':
        user_states[chat_id] = {'step': 'v_3ys'}
        bot.send_message(chat_id, "请输入：姓名 身份证 手机号")
    elif cmd == '2ys':
        user_states[chat_id] = {'step': 'v_2ys'}
        bot.send_message(chat_id, "请输入：姓名 身份证")

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return 
    
    # --- 💡 铭哥认证：全自动智能识别引擎 (修复位置) ---
    if chat_id not in user_states or not user_states[chat_id].get('step'):
        # 1. 提取所有可能的要素
        id_search = re.search(r'(\d{18}|\d{17}[Xx]|\d{15})', text)
        phone_search = re.search(r'(1[3-9]\d{9})', text)
        name_search = re.search(r'[\u4e00-\u9fa5]{2,4}', text)

        # 🚀 情况 A: 三要素 (有姓名、身份证、手机号)
        if id_search and phone_search and name_search:
            n, i, p = name_search.group(), id_search.group().upper(), phone_search.group()
            if user_points.get(uid, 0.0) < 0.05: return bot.reply_to(message, "积分不足")
            return query_3ys_logic(chat_id, n, i, p, uid)
            
        # 🚀 情况 B: 二要素 (有姓名、身份证，但没有11位手机号)
        if id_search and name_search and not phone_search:
            n, i = name_search.group(), id_search.group().upper()
            if user_points.get(uid, 0.0) < 0.01: return bot.reply_to(message, "积分不足")
            return single_verify_2ys(chat_id, n, i, uid)

        # 🚀 情况 C: 常用号 (只有身份证)
        if id_search and not name_search and not phone_search:
            i = id_search.group().upper()
            if user_points.get(uid, 0.0) < 1.5: return bot.reply_to(message, "积分不足")
            return xiaowunb_query_logic(chat_id, i, uid)

    # --- 状态机处理 (手动点击菜单后的逻辑) ---
    state = user_states.get(chat_id)
    if not state: return
    step = state['step']
    
    if step == 'v_3ys':
        del user_states[chat_id]
        parts = re.split(r'[,/\s\n]+', text)
        if len(parts) >= 3:
            query_3ys_logic(chat_id, parts[0], parts[1].upper(), parts[2], uid)
    elif step == 'v_2ys':
        del user_states[chat_id]
        parts = re.split(r'[,/\s\n]+', text)
        if len(parts) >= 2:
            single_verify_2ys(chat_id, parts[0], parts[1].upper(), uid)

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = call.from_user.id
    if call.data == "view_help":
        bot.edit_message_text("直接发送信息即可识别：\n1. 姓名+身份证+手机号 (三要素)\n2. 姓名+身份证 (二要素)\n3. 身份证号 (常用号查询)", call.message.chat.id, call.message.message_id, reply_markup=types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙 返回", callback_data="back_to_main")))
    elif call.data == "view_pay":
        bot.edit_message_text("🛍️ 充值请联系管理员：\n1 USDT = 1 积分", call.message.chat.id, call.message.message_id, reply_markup=get_pay_markup())
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(uid, user_points.get(uid, 0)), call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_main_markup())

if __name__ == '__main__':
    bot.infinity_polling()
