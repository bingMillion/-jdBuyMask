import time
import json
import logging
import logging.handlers
import requests
import sys


def get_user_name(session):
    """通过访问该网站，即可从返回信息里获取到用户名"""
    userName_Url = 'https://passport.jd.com/new/helloService.ashx?callback=jQuery339448&_=' + str(
        int(time.time() * 1000))
    session.headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://order.jd.com/center/list.action",
        "Connection": "keep-alive"
    }
    resp = session.get(url=userName_Url, allow_redirects=True)
    resultText = resp.text
    resultText = resultText.replace('jQuery339448(', '')
    resultText = resultText.replace(')', '')
    usernameJson = json.loads(resultText)
    logger.info('登录账号名称[%s]', usernameJson['nick'])

def validate_cookies(session,message):
    """用session会话去访问“我的订单页面”以检查cookies的有效性"""
    for flag in range(1, 3):
        try:
            targetURL = 'https://order.jd.com/center/list.action'
            payload = {
                'rid': str(int(time.time() * 1000)),
            }
            resp = session.get(url=targetURL, params=payload, allow_redirects=False)
            if resp.status_code == requests.codes.OK:
                logger.info('校验是否登录[成功]')
                return True
            else:
                logger.info('校验是否登录[失败]')
                logger.info('请在configDemo.ini文件下更新cookie')
                time.sleep(5)
                continue
        except Exception as e:
            logger.info('第【%s】次请重新获取cookie', flag)
            time.sleep(5)
            continue
    message.sendAny('脚本登录cookie失效了，请重新登录')
    sys.exit(1)


def set_logger():
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    file_handler = logging.handlers.RotatingFileHandler(
        LOG_FILENAME, maxBytes=10485760, backupCount=5, encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

LOG_FILENAME = 'jdBuyMask.log'
logger = logging.getLogger()
set_logger()

def parse_json(s):
    begin = s.find('{')
    end = s.rfind('}') + 1
    return json.loads(s[begin:end])


def get_tag_value(tag, key='', index=0):
    if key:
        value = tag[index].get(key)
    else:
        value = tag[index].text
    return value.strip(' \t\r\n')


def get_cookies(cookies_string):
    cookies = {}
    for cookie in cookies_string.split(';'):
        name, value = cookie.strip().split('=',1) # 1表示分隔1次，变成两个值
        cookies[name] = value
    return cookies
