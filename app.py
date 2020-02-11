import sys
import random
import traceback
import time

import requests

from message import message
from util import  _setDNSCache,getconfig
from jd_cart import select_all_cart_item,remove_cart,add_item_to_cart,get_checkout_page_detail,submit_order
from jd_goods import get_avilable_id,item_removed
from jd_utils import get_user_name,validate_cookies,logger,get_cookies

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
    "Connection": "keep-alive"
}
is_Submit_captcha = False
submit_captcha_rid = ''
submit_captcha_text = ''
encryptClientInfo = ''
submit_Time = 0


def initial(session,message):
    validate_cookies(session, message)
    get_user_name(session)
    select_all_cart_item(session)
    remove_cart(session)

def buy(sku_id,session,skuids):
    """
    京东购物流程
    # 1. 加入购物车
    # 2. 去购物车结算
    # 3. 提交订单
    """
    # 1. 加入购物车
    add_item_to_cart(session,sku_id)
    # 2. 去购物车结算
    risk_control = get_checkout_page_detail(session)
    if risk_control == '刷新太频繁了':
        return False
    # 3. 提交订单
    if len(risk_control) > 0:
        if submit_order(session, risk_control, sku_id, skuids, submit_Time, encryptClientInfo, is_Submit_captcha,
                        '', submit_captcha_text, submit_captcha_rid):
            return True
    return False


def buys(inStockSkuid,session,skuids):
    """购买这批商品"""
    for skuId in inStockSkuid:
        global submit_Time
        submit_Time = int(time.time() * 1000)
        logger.info('[%s]类型口罩有货啦!马上下单', skuId)
        skuidUrl = 'https://item.jd.com/' + skuId + '.html'
        if buy(skuId,session,skuids):
            message.send(skuidUrl, True)
            sys.exit(1)
        else:
            if item_removed(skuId):
                message.send(skuidUrl, False)
            else:
                logger.info('[%s]商品已下柜，商品列表中踢出', skuId)
                skuids.remove(skuId)
            select_all_cart_item()


if __name__ == '__main__':
    # 1. 初始化参数
    cookies_String, mail, sc_key, messageType, modelType, area, skuidsString, skuids, captchaUrl, eid, fp, payment_pwd = getconfig()
    message = message(messageType=messageType, sc_key=sc_key, mail=mail) # 发送邮件/微信
    session, checksession = requests.session(), requests.session()
    session.headers, checksession.headers = HEADERS, HEADERS
    session.cookies = requests.utils.cookiejar_from_dict(get_cookies(cookies_String), cookiejar=None,overwrite=True)
    _setDNSCache()

    # 2. 轮询检测
    flash_time = 0
    initial(session,message)
    while True:
        try:
            logger.info('开始第' + str(flash_time) + '次 ')
            flash_time += 1

            avilable_ids = get_avilable_id(checksession, skuids, area)
            buys(avilable_ids, session, skuids)

            # 休眠
            timesleep = random.randint(1, 3) / 10
            time.sleep(timesleep)

            # 检验登录状态
            if flash_time % 100 == 0:
                logger.info('校验是否还在登录')
                validate_cookies()

        except Exception as e:
            traceback.print_exc()
            time.sleep(10)

