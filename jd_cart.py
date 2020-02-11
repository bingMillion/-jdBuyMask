import random
import requests
from bs4 import BeautifulSoup
import time
import json
import traceback
from util import  response_status

from jd_utils import logger,get_tag_value


def add_item_to_cart(session,sku_id):
    """添加商品到购物车"""
    url = 'https://cart.jd.com/gate.action'
    payload = {
        'pid': sku_id,
        'pcount': 1,
        'ptype': 1,
    }
    resp = session.get(url=url, params=payload)
    if 'https://cart.jd.com/cart.action' in resp.url:  # 套装商品加入购物车后直接跳转到购物车页面
        result = True
    else:  # 普通商品成功加入购物车后会跳转到提示 "商品已成功加入购物车！" 页面
        soup = BeautifulSoup(resp.text, "html.parser")
        result = bool(soup.select('h3.ftx-02'))  # [<h3 class="ftx-02">商品已成功加入购物车！</h3>]

    if result:
        logger.info('%s  已成功加入购物车', sku_id)
    else:
        logger.error('%s 添加到购物车失败', sku_id)

def get_checkout_page_detail(session):
    """获取订单结算页面信息

    该方法会返回订单结算页面的详细信息：商品名称、价格、数量、库存状态等。

    :return: 结算信息 dict
    """
    url = 'http://trade.jd.com/shopping/order/getOrderInfo.action'
    # url = 'https://cart.jd.com/gotoOrder.action'
    payload = {
        'rid': str(int(time.time() * 1000)),
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://cart.jd.com/cart.action",
        "Connection": "keep-alive",
        'Host': 'trade.jd.com',
    }
    try:
        resp = session.get(url=url, params=payload, headers=headers)
        if not response_status(resp):
            logger.error('获取订单结算页信息失败')
            return ''
        if '刷新太频繁了' in resp.text:
            return '刷新太频繁了'
        soup = BeautifulSoup(resp.text, "html.parser")
        risk_control = get_tag_value(soup.select('input#riskControl'), 'value')
        showCheckCode = get_tag_value(soup.select('input#showCheckCode'), 'value')
        if showCheckCode in ['false','False','FALSE']:
            pass
        else:
            if showCheckCode == 'true':
                logger.info('提交订单需要验证码')
                global is_Submit_captcha, encryptClientInfo
                encryptClientInfo = get_tag_value(soup.select('input#encryptClientInfo'), 'value')
                is_Submit_captcha = True

        order_detail = {
            'address': soup.find('span', id='sendAddr').text[5:],  # remove '寄送至： ' from the begin
            'receiver': soup.find('span', id='sendMobile').text[4:],  # remove '收件人:' from the begin
            'total_price': soup.find('span', id='sumPayPriceId').text[1:],  # remove '￥' from the begin
            'items': []
        }

        logger.info("下单信息：%s", order_detail)
        return risk_control
    except requests.exceptions.RequestException as e:
        logger.error('订单结算页面获取异常：%s' % e)
    except Exception as e:
        logger.error('下单页面数据解析异常：%s', e)
    return ''


def select_all_cart_item(session):
    url = "https://cart.jd.com/selectAllItem.action"
    data = {
        't': 0,
        'outSkus': '',
        'random': random.random()
    }
    resp = session.post(url, data=data)
    if resp.status_code != requests.codes.OK:
        print('Status: %u, Url: %s' % (resp.status_code, resp.url))
        return False
    return True


def remove_cart(session):
    """清空购物车"""

    url = "https://cart.jd.com/batchRemoveSkusFromCart.action"
    data = {
        't': 0,
        'null': '',
        'outSkus': '',
        'random': random.random(),
        'locationId': '19-1607-4773-0'
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/70.0.3538.25 Safari/537.36 Core/1.70.37",
        "Accept": "application/json, text/javascript, */*; q=0.01",
        "Referer": "https://cart.jd.com/cart.action",
        "Host": "cart.jd.com",
        "Content-Type": "application/x-www-form-urlencoded",
        "Accept-Encoding": "gzip, deflate, br",
        "Accept-Encoding": "zh-CN,zh;q=0.9,ja;q=0.8",
        "Origin": "https://cart.jd.com",
        "Connection": "keep-alive"
    }
    resp = session.post(url, data=data, headers=headers)
    logger.info('清空购物车')
    if resp.status_code != requests.codes.OK:
        print('Status: %u, Url: %s' % (resp.status_code, resp.url))
        return False
    return True

def submit_order(session, risk_control, sku_id, skuids, submit_Time, encryptClientInfo, is_Submit_captcha, payment_pwd,
                 submit_captcha_text, submit_captcha_rid):
    """

    重要：
    1.该方法只适用于普通商品的提交订单（即可以加入购物车，然后结算提交订单的商品）
    2.提交订单时，会对购物车中勾选✓的商品进行结算（如果勾选了多个商品，将会提交成一个订单）

    :return: True/False 订单提交结果
    """
    url = 'https://trade.jd.com/shopping/order/submitOrder.action'
    # js function of submit order is included in https://trade.jd.com/shopping/misc/js/order.js?r=2018070403091

    data = {
        'overseaPurchaseCookies': '',
        'vendorRemarks': '[]',
        'submitOrderParam.sopNotPutInvoice': 'false',
        'submitOrderParam.trackID': 'TestTrackId',
        'submitOrderParam.ignorePriceChange': '0',
        'submitOrderParam.btSupport': '0',
        'riskControl': risk_control,
        'submitOrderParam.isBestCoupon': 1,
        'submitOrderParam.jxj': 1,
        'submitOrderParam.trackId': '9643cbd55bbbe103eef18a213e069eb0',  # Todo: need to get trackId
        # 'submitOrderParam.eid': eid,
        # 'submitOrderParam.fp': fp,
        'submitOrderParam.needCheck': 1,
    }




    if len(payment_pwd) > 0:
        payment_pwd = ''.join(['u3' + x for x in payment_pwd])
        data['submitOrderParam.payPassword'] = payment_pwd

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "http://trade.jd.com/shopping/order/getOrderInfo.action",
        "Connection": "keep-alive",
        'Host': 'trade.jd.com',
    }
    for count in range(1, 3):
        logger.info('第[%s/%s]次尝试提交订单', count, 3)
        try:
            if is_Submit_captcha:
                captcha_result = page_detail_captcha(session, encryptClientInfo)
                # 验证码服务错误
                if not captcha_result:
                    logger.error('验证码服务异常')
                    continue
                data['submitOrderParam.checkcodeTxt'] = submit_captcha_text
                data['submitOrderParam.checkCodeRid'] = submit_captcha_rid
            resp = session.post(url=url, data=data, headers=headers)
            resp_json = json.loads(resp.text)
            logger.info('本次提交订单耗时[%s]毫秒', str(int(time.time() * 1000) - submit_Time))

            if resp_json.get('success'):
                logger.info('订单提交成功! 订单号：%s', resp_json.get('orderId'))
                return True
            else:
                resultMessage, result_code = resp_json.get('message'), resp_json.get('resultCode')
                if result_code == 0:
                    # self._save_invoice()
                    if '验证码不正确' in resultMessage:
                        resultMessage = resultMessage + '(验证码错误)'
                        logger.info('提交订单验证码[错误]')
                        continue
                    else:
                        resultMessage = resultMessage + '(下单商品可能为第三方商品，将切换为普通发票进行尝试)'
                elif result_code == 60077:
                    resultMessage = resultMessage + '(可能是购物车为空 或 未勾选购物车中商品)'
                elif result_code == 60123:
                    resultMessage = resultMessage + '(需要在payment_pwd参数配置支付密码)'
                elif result_code == 60070:
                    resultMessage = resultMessage + '(省份不支持销售)'
                    skuids.remove(sku_id)
                    logger.info('[%s]类型口罩不支持销售踢出', sku_id)
                logger.info('订单提交失败, 错误码：%s, 返回信息：%s', result_code, resultMessage)
                logger.info(resp_json)
                return False
        except Exception as e:
            print(traceback.format_exc())
            continue

def page_detail_captcha(session, isId):
    url = 'https://captcha.jd.com/verify/image'
    acid = '{}_{}'.format(random.random(), random.random())
    payload = {
        'acid': acid,
        'srcid': 'trackWeb',
        'is': isId,
    }
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://trade.jd.com/shopping/order/getOrderInfo.action",
        "Connection": "keep-alive",
        'Host': 'captcha.jd.com',
    }
    try:
        resp = session.get(url=url, params=payload, headers=headers)
        if not response_status(resp):
            logger.error('获取订单验证码失败')
            return ''
        logger.info('解析验证码开始')
        image = Image.open(BytesIO(resp.content))
        image.save('captcha.jpg')
        result = analysis_captcha(resp.content)
        if not result:
            logger.error('解析订单验证码失败')
            return ''
        global submit_captcha_text, submit_captcha_rid
        submit_captcha_text = result
        submit_captcha_rid = acid
        return result
    except Exception as e:
        logger.error('订单验证码获取异常：%s', e)
    return ''


def analysis_captcha(session, captchaUrl, pic):
    for i in range(1, 10):
        try:
            url = captchaUrl
            resp = session.post(url, pic)
            if not response_status(resp):
                logger.error('解析验证码失败')
                continue
            logger.info('解析验证码[%s]', resp.text)
            return resp.text
        except Exception as e:
            print(traceback.format_exc())
            continue
    return ''
