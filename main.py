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
# 假设这些是你本地的库
try:
    import sms_list 
    import sms_list_new
    from sms_list import *
except ImportError:
    print("警告: 未找到 sms_list 或 sms_list_new 模块")

from Crypto.Cipher import DES3
from datetime import datetime
from telebot import types
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO 

# 屏蔽 SSL 证书报警
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ================= 1. 核心配置 =================
API_TOKEN = '8338893180:AAH-l_4m1-tweKyt92bliyk4fsPqoPQWzpU'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'

# --- 人脸核验/图床配置 ---
FACE_VERIFY_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJsb2dpbl91c2VyX2tleSI6IjA5YjViMDQ2LWI1NzYtNGJlNi05MGVhLTllY2YxNGNiMjI4MiJ9.fIUe4cTbOnK-l68a8cF44glMCd32sWxphcftKah6d9PK4PAo7vV9AdJOByZMt_X8YouKC6cb0_R_IUOgUBNMFg"
IMAGE_HOST_API_KEY = "chv_e0sb_e58e156ce7f7c1d4439b550210c718de0c7af8820db77c0cd04e198ed06011b2e32ed1b5a7f1b00e543c76c20f5c64866bb355fde1dca14d6d74f0a1989b567d"
IMAGE_HOST_URL = "https://imgloc.com/api/1/upload"

# 三要素/二要素接口 Token
THREE_ELEMENTS_AUTH = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpblR5cGUiOiJsb2dpbiIsImxvZ2luSWQiOiJhcHBfdXNlcjoxMTc1NDYwIiwicm5TdHIiOiJJSmVrU005UTlHc2hTV2RiVENQZ1VFbnpDN0MwWjFYZCJ9.vxjF6ShG81TM2hT-uiYyubHGOlEuCKC-m8nSmi7sayU"
AUTH_BEARER = "bearer eyJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6IisxOTM3ODg4NDgyNiIsIm9wZW5JZCI6Im95NW8tNHk3Wnd0WGlOaTVHQ3V3YzVVNDZJYk0iLCJpZENhcmRObyI6IjM3MDQ4MTE5ODgwODIwMzUxNCIsInVzZXJOYW1lIjoi6ams5rCR5by6IiwibG9naW5UaW1lIjoxNzY5NDE1NjYxMTk0LCJhcHBJZCI6Ind4ZjVmZDAyZDEwZGJiMjFkMiIsImlzcmVhbG5hbWUiOnRydWUsInNhYXNVc2VySWQiOm51bGwsImNvbXBhbnlJZCI6bnVsbCwiY29tcGFueVZPUyI6bnVsbH0.GwMYvckFHvFbhSi0NXpQDPiv9ZswUBAImN5bUipBla0"

bot = telebot.TeleBot(API_TOKEN)
user_points = {}
user_states = {}

# ================= 2. 增强逻辑：国内代理获取 (解决 Railway IP问题) =================

def get_domestic_proxies():
    """抓取国内公益代理列表"""
    try:
        r = requests.get("https://api.proxyscrape.com/v2/?request=displayproxies&protocol=http&timeout=1000&country=cn&ssl=all&anonymity=all", timeout=10)
        if r.status_code == 200:
            return r.text.strip().split('\r\n')
    except: pass
    return []

# ================= 3. 数据持久化 =================
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

# ================= 4. 功能逻辑 =================

def upload_to_host(img_bytes):
    """上传到图床"""
    try:
        files = {'source': ('photo.jpg', img_bytes, 'image/jpeg')}
        data = {'key': IMAGE_HOST_API_KEY, 'format': 'json'}
        r = requests.post(IMAGE_HOST_URL, files=files, data=data, timeout=30)
        if r.status_code == 200:
            res = r.json()
            if res.get('status_code') == 200:
                return res['image']['url']
    except: pass
    return None

def verify_face_logic(chat_id, name, id_card, pic_url, uid):
    """请求人脸核验接口 - 带代理重试逻辑"""
    url = "https://www.cjhyzx.com/api/vx/actual/carrier/center/realPersonAuthentication"
    headers = {
        "Authorization": FACE_VERIFY_TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X)",
        "Referer": "https://servicewechat.com/wx2d2597151b9e8347/12/page-frame.html"
    }
    payload = {
        "carrierUser": {
            "identityCard": id_card, "nickName": name,
            "address": "江苏省扬州市", "identityvalidPeriodTo": "2036-08-26"
        },
        "sysAttachmentInfoList": [{"fileUrl": pic_url}]
    }

    # 首先获取代理列表
    proxy_list = get_domestic_proxies()
    # 在列表最前面加入 None，表示先尝试直连
    proxy_list.insert(0, None)

    success = False
    for p_addr in proxy_list[:5]: # 最多尝试前 5 个链路
        proxies = {"http": f"http://{p_addr}", "https": f"http://{p_addr}"} if p_addr else None
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=20, proxies=proxies, verify=False)
            
            # 解决 Expecting value 报错：如果返回的不是 JSON 而是 HTML，说明 IP 被拦截
            if "<html" in response.text:
                continue # 尝试下一个代理
                
            result = response.json()
            user_points[uid] -= 2.0 
            save_points()
            
            if str(result.get("code")) == "200":
                msg = f"✅ **人脸核验成功！**\n👤 姓名: {name}\n🆔 身份证: {id_card}\n🟢 结果: 核验通过"
            else:
                msg = f"❌ **人脸核验失败**\n👤 姓名: {name}\n原因: {result.get('msg', '不匹配')} 🔴"
            
            bot.send_message(chat_id, msg, parse_mode='Markdown')
            success = True
            break # 成功则退出循环
        except:
            continue

    if not success:
        bot.send_message(chat_id, "❌ 核验失败：Railway 海外 IP 被拦截且暂无可用国内公益代理链路。")

# ================= 5. 指令入口 =================

@bot.message_handler(commands=['start', 'face', 'cyh', '3ys', '2ys', 'add', 'sms'])
def handle_commands(message):
    uid, chat_id = message.from_user.id, message.chat.id
    text = message.text.split()
    cmd = text[0][1:]

    if cmd == 'start':
        if uid not in user_points: user_points[uid] = 0.0
        bot.send_message(chat_id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())
    
    elif cmd == 'face':
        if user_points.get(uid, 0.0) < 2.0: return bot.reply_to(message, "积分不足(需2.0)")
        user_states[chat_id] = {'step': 'face_info'}
        bot.send_message(chat_id, "👤 **进入人脸核验模式**\n请输入核验信息，格式：\n`姓名 身份证`", parse_mode='Markdown')

    elif cmd == 'cyh':
        if user_points.get(uid, 0.0) < 1.5: return bot.reply_to(message, "积分不足(需1.5)")
        user_states[chat_id] = {'step': 'cyh_id'}; bot.send_message(chat_id, "请输入身份证号：")

    elif cmd == '3ys':
        if user_points.get(uid, 0.0) < 0.05: return bot.reply_to(message, "积分不足(需0.05)")
        user_states[chat_id] = {'step': 'v_3ys'}; bot.send_message(chat_id, "请输入：`姓名 手机号 身份证`", parse_mode='Markdown')

    elif cmd == '2ys':
        if user_points.get(uid, 0.0) < 0.01: return bot.reply_to(message, "积分不足(需0.01)")
        user_states[chat_id] = {'step': 'v_2ys'}; bot.send_message(chat_id, "请输入：`姓名 身份证`", parse_mode='Markdown')

    elif cmd == 'add' and uid == ADMIN_ID:
        try:
            tid, amt = int(text[1]), float(text[2])
            user_points[tid] = user_points.get(tid, 0.0) + amt; save_points()
            bot.reply_to(message, f"✅ 已充值！当前余额: `{user_points[tid]:.2f}`")
        except: pass

# ================= 6. 统一内容处理器 =================

@bot.message_handler(content_types=['text', 'photo'])
def handle_all_content(message):
    uid, chat_id = message.from_user.id, message.chat.id
    state = user_states.get(chat_id)

    if message.content_type == 'text':
        text = message.text.strip()
        if text.startswith('/'): return
        
        if state:
            step = state['step']
            if step == 'face_info':
                parts = re.split(r'[,，\s\n]+', text)
                if len(parts) >= 2:
                    user_states[chat_id].update({'step': 'face_photo', 'name': parts[0], 'id': parts[1]})
                    bot.send_message(chat_id, "📸 **信息已记录**\n请发送需要核验的【实时照片/自拍】:")
                else:
                    bot.reply_to(message, "格式错误！示例：张三 440101...")
                return
            
            # 原有 cyh/3ys 等逻辑的简化处理
            elif step == 'cyh_id':
                del user_states[chat_id]
                xiaowunb_query_logic(chat_id, text, uid)
            elif step == 'v_3ys':
                del user_states[chat_id]
                p = re.split(r'[,，\s\n]+', text)
                if len(p) >= 3: query_3ys_logic(chat_id, p[0], p[2], p[1], uid)
            elif step == 'v_2ys':
                del user_states[chat_id]
                p = re.split(r'[,，\s\n]+', text)
                if len(p) >= 2: single_verify_2ys(chat_id, p[0], p[1], uid)

    elif message.content_type == 'photo':
        if state and state.get('step') == 'face_photo':
            name, id_card = state['name'], state['id']
            del user_states[chat_id]
            bot.send_message(chat_id, "⏳ 正在上传并请求国内链路核验，请稍后...")
            
            try:
                file_info = bot.get_file(message.photo[-1].file_id)
                downloaded_file = bot.download_file(file_info.file_path)
                pic_url = upload_to_host(downloaded_file)
                if pic_url:
                    verify_face_logic(chat_id, name, id_card, pic_url, uid)
                else:
                    bot.send_message(chat_id, "❌ 图片处理失败。")
            except Exception as e:
                bot.send_message(chat_id, f"❌ 错误: {e}")
        else:
            bot.reply_to(message, "请先使用 /face 指令开始。")

# --- UI 辅助函数 (保持不变) ---
def get_main_text(source, uid, pts):
    return (f"👤 用户 ID: `{uid}`\n💰 当前余额: `{pts:.2f}积分`\n\n使用 /face 进行人脸核验\n使用 /sms 手机号 进行测压")

def get_main_markup():
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(types.InlineKeyboardButton("使用帮助", callback_data="view_help"),
               types.InlineKeyboardButton("在线充值", callback_data="view_pay"))
    return markup

# (为了运行，补全一个简单的逻辑函数示例)
def xiaowunb_query_logic(chat_id, id_number, uid):
    bot.send_message(chat_id, f"查询身份证: {id_number} (接口对接中...)")

if __name__ == '__main__':
    print("Bot 正在运行...")
    bot.infinity_polling()
