import random
import time
import json

import requests

from jd_utils import logger
from jd_utils import parse_json

def remove_unuse_id(skuids,unuse_ids):
    """移除已下架的商品，不用再去监控"""
    for id in unuse_ids:
        skuids.remove(id)


def get_avilable_id(checksession, skuids, area):
    """获取可购买的商品id"""

    start = int(time.time() * 1000)
    skuidString = ','.join(skuids)
    callback = 'jQuery' + str(random.randint(1000000, 9999999))
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "https://cart.jd.com/cart.action",
        "Connection": "keep-alive",
        "Host":"c0.3.cn"
    }
    #
    url = 'https://c0.3.cn/stocks'
    payload = {
        'type': 'getstocks',
        'skuIds': skuidString,
        'area': area,
        'callback': callback,
        '_': int(time.time() * 1000),
    }
    resp = checksession.get(url=url, params=payload, headers=headers)
    inStockSkuid = []
    nohasSkuid = []
    unUseSkuid = []
    for sku_id, info in parse_json(resp.text).items():
        sku_state = info.get('skuState')  # 商品是否上架
        stock_state = info.get('StockState')  # 商品库存状态
        if sku_state == 1 and stock_state in (33, 40):
            inStockSkuid.append(sku_id)
        if sku_state == 0:
            unUseSkuid.append(sku_id)
        if stock_state == 34:
            nohasSkuid.append(sku_id)
    logger.info('检测[%s]个口罩有货，[%s]个口罩无货，[%s]个口罩下柜，耗时[%s]ms', len(inStockSkuid), len(nohasSkuid), len(unUseSkuid),
                int(time.time() * 1000) - start)

    if len(unUseSkuid) > 0:
        logger.info('[%s]口罩已经下架', ','.join(unUseSkuid))
        remove_unuse_id(skuids,unUseSkuid)
        logger.info('[%s]已经移除下架商品', ','.join(unUseSkuid))
    return inStockSkuid


def item_removed(sku_id):
    """下架商品检测"""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/75.0.3770.100 Safari/531.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3",
        "Referer": "http://trade.jd.com/shopping/order/getOrderInfo.action",
        "Connection": "keep-alive",
        'Host': 'item.jd.com',
    }
    url = 'https://item.jd.com/{}.html'.format(sku_id)
    page = requests.get(url=url, headers=headers)
    return '该商品已下柜' not in page.text





