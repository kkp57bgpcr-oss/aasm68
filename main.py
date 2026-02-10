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

# [配置信息 API_TOKEN, ADMIN_ID, AUTH_BEARER 等保持不变]

# ================= 1. 严格对齐的 UI 文本 =================

def get_main_text(source, uid, pts):
    # 严格对齐截图：包含 ID、名称、用户名、余额和自动识别提示
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
    # 这里的文案完全复刻你的使用帮助截图，包含分割线
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
        "每次核验扣除 0.05 积分\n"
        "——————————————————\n"
        "常用号查询\n"
        "发送 /cyh 进行查询\n"
        "每次查询扣除 1.5 积分 空不扣除积分"
    )

# ================= 2. 三要素逻辑 (结果：✅一致✅) =================

def query_3ys_logic(chat_id, name, id_card, phone, uid):
    # 彻底删除任何 url 拼接，直接返回结果
    url = "https://esb.wbszkj.cn/prod-api/wxminiapp/user/userIdVerify" 
    headers = {"Authorization": AUTH_BEARER, "Content-Type": "application/json"}
    payload = {"name": name, "phone": phone, "idNo": id_card, "idType": 1}
    
    try:
        r = requests.post(url, headers=headers, json=payload, verify=False, timeout=10)
        user_points[uid] -= 0.05
        save_points()
        
        # 对齐截图格式：结果：✅一致✅ 或 结果：三要素核验不一致❌
        is_ok = r.status_code == 200 and r.json().get("success") == True
        status = "三要素核验一致✅" if is_ok else "三要素核验不一致❌"
        
        res = (f"名字：{name}\n"
               f"手机号：{phone}\n"
               f"身份证：{id_card}\n"
               f"结果：{status}\n\n"
               f"已扣除 0.05 积分！\n"
               f"当前积分余额：{user_points[uid]:.2f} 积分")
        bot.send_message(chat_id, res)
    except:
        bot.send_message(chat_id, "❌ 接口请求失败")

# ================= 3. 核心分发逻辑 (解决指令没反应) =================

@bot.message_handler(func=lambda m: True)
def handle_all_messages(message):
    uid, chat_id, text = message.from_user.id, message.chat.id, message.text.strip()
    
    # --- 1. 优先判定指令 (解决截图里指令失效的问题) ---
    if text.startswith('/'):
        cmd = text.split()[0].lower()
        if cmd == '/start':
            if uid not in user_points: user_points[uid] = 0.0
            return bot.send_message(chat_id, get_main_text(message, uid, user_points[uid]), parse_mode='Markdown', reply_markup=get_main_markup())
        elif cmd == '/add' and uid == ADMIN_ID:
            # 充值逻辑：/add ID 积分
            try:
                p = text.split()
                tid, amt = int(p[1]), float(p[2])
                user_points[tid] = user_points.get(tid, 0.0) + amt
                save_points()
                return bot.reply_to(message, f"✅ 已充值！当前余额：`{user_points[tid]:.2f}`")
            except: return bot.reply_to(message, "用法：`/add ID 积分`")
        elif cmd == '/sms':
            # 短信轰炸逻辑入口...
            return bot.reply_to(message, "请输入要轰炸的手机号：")
        elif cmd == '/pl':
            user_states[chat_id] = {'step': 'v_name'}
            return bot.send_message(chat_id, "请输入批量核验的姓名：")
        # 其他指令 (/bq, /cyh, /2ys, /3ys) 同理...
        return

    # --- 2. 状态机逻辑 (正在进行的业务) ---
    if chat_id in user_states:
        # 这里处理你原本的批量核验、补齐身份证等分步流程...
        return

    # --- 3. 自动识别逻辑 (只有不是指令、不是分步流程时才触发) ---
    parts = re.split(r'[,/\s]+', text)
    if len(parts) == 3: # 三要素识别
        n, p, i = None, None, None
        for x in parts:
            if re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
            elif re.match(r'^1[3-9]\d{9}$', x): p = x
            elif re.match(r'^[\dXx]{15,18}$', x): i = x.upper()
        if n and p and i:
            if user_points.get(uid, 0.0) < 0.05: return bot.send_message(chat_id, "积分不足，请先充值！")
            return query_3ys_logic(chat_id, n, i, p, uid)
