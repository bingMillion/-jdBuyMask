import traceback


def sendMail(mail, msgtext):
    try:
        import smtplib
        from email.mime.text import MIMEText
        # email 用于构建邮件内容
        from email.header import Header

        # 用于构建邮件头
        # 发信方的信息：发信邮箱，QQ 邮箱授权码
        from_addr = 'jdbuymask@163.com'
        password = 'alpsneahcyz123'

        # 收信方邮箱
        to_addr = mail
        # 发信服务器
        smtp_server = 'smtp.163.com'
        # 邮箱正文内容，第一个参数为内容，第二个参数为格式(plain 为纯文本)，第三个参数为编码
        msg = MIMEText(msgtext, 'plain', 'utf-8')
        # 邮件头信息
        # msg['From'] = Header(from_addr)
        msg['From'] = Header(u'from Mark<{}>'.format(from_addr), 'utf-8')
        msg['To'] = Header(to_addr)
        msg['Subject'] = Header('京东口罩监控','utf-8')
        # 开启发信服务，这里使用的是加密传输
        server = smtplib.SMTP_SSL(host=smtp_server)
        server.connect(smtp_server, 465)
        # 登录发信邮箱
        server.login(from_addr, password)
        # 发送邮件
        server.sendmail(from_addr, to_addr, msg.as_string())
        # 关闭服务器
        server.quit()
    except Exception as e:
        print(traceback.format_exc())

#!/usr/bin/env python
# -*- encoding=utf8 -*-
import datetime
import json

import requests

from jd_utils import logger


def sendWechat(sc_key, text='京东商品监控', desp=''):
    if not text.strip():
        logger.error('Text of message is empty!')
        return

    now_time = str(datetime.datetime.now())
    desp = '[{0}]'.format(now_time) if not desp else '{0} [{1}]'.format(desp, now_time)

    try:
        resp = requests.get(
            'https://sc.ftqq.com/{}.send?text={}&desp={}'.format(sc_key, text, desp)
        )
        resp_json = json.loads(resp.text)
        if resp_json.get('errno') == 0:
            logger.info('Message sent successfully [text: %s, desp: %s]', text, desp)
        else:
            logger.error('Fail to send message, reason: %s', resp.text)
    except requests.exceptions.RequestException as req_error:
        logger.error('Request error: %s', req_error)
    except Exception as e:
        logger.error('Fail to send message [text: %s, desp: %s]: %s', text, desp, e)

class message(object):
    """消息推送类"""

    def __init__(self, messageType, sc_key, mail):
        if messageType == '2':
            if not sc_key:
                raise Exception('sc_key can not be empty')
            self.sc_key = sc_key
        elif messageType == '1':
            if not mail:
                raise Exception('mail can not be empty')
            self.mail = mail
        self.messageType = messageType

    def send(self, desp='', is_purchased=False):
        desp = str(desp)
        if is_purchased:
            msg = desp + ' 类型口罩，已经下单了。24小时内付款'
        else:
            msg = desp + ' 类型口罩，下单失败了'
        if self.messageType == '1':
            sendMail(self.mail, msg)
        if self.messageType == '2':
            sendWechat(sc_key=self.sc_key, desp=msg)

    def sendAny(self, desp=''):
        desp = str(desp)
        msg = desp
        if self.messageType == '1':
            sendMail(self.mail, msg)
        if self.messageType == '2':
            sendWechat(sc_key=self.sc_key, desp=msg)
