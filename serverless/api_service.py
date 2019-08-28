# -*- coding: utf-8 -*-

import sys
import logging
import json
import xml.etree.ElementTree as ET
import time
import requests
import random
import hashlib
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO, stream=sys.stdout)
logger = logging.getLogger()
logger.setLevel(level=logging.INFO)

logger.info('Loading function')



def main_handler(event,content):
	logger.info('start main_handler')
	if event["path"] != "/DuoServer":
		return {"errorCode":411,"errorMsg":"request is not from setting api path"}
	else:
		if event["httpMethod"] == "POST":
			data = event['body']
			recMsg = parse_xml(data)
			if isinstance(recMsg, RequestMsg) and recMsg.MsgType == 'text':
				toUser = recMsg.FromUserName
				fromUser = recMsg.ToUserName
				content = getReplyMessage(recMsg.Content)
				replyMsg = ResponseTextMsg(toUser, fromUser, content)
				resp = replyMsg.send()
				logger.info("[SERVER] Sent: "+resp)
				return {
					"isBase64Encoded": False,
					"statusCode": 200,
					"headers": {"Content-Type":"text/html"},
					"body": resp
				}
			else:
				print("[SERVER] None-text message.")
				return "success"
		elif event["httpMethod"] == "GET":
			data = event['queryString']
			signature = data['signature']
			timestamp = data['timestamp']
			nonce = data['nonce']
			echostr = data['echostr']
			token = "duo"

			l = [token, timestamp, nonce]
			l.sort()
			sha1 = hashlib.sha1()
			sha1.update(''.join(l).encode('utf-8'))
			hashcode = sha1.hexdigest()
			logger.info('HASHCODE: %s\nSIGNATURE: %s'%(hashcode,signature))
			if hashcode == signature:
				return int(echostr)
			else:
				return ""
	return {"errorCode":413,"errorMsg":"request is not correctly executed."}




def parse_xml(web_data):
	if len(web_data) == 0:
		return None
	xmlData = ET.fromstring(web_data)
	msg_type = xmlData.find('MsgType').text
	if msg_type == 'text':
		return RequestTextMsg(xmlData)
	elif msg_type == 'image':
		return None
	#     return ImageMsg(xmlData)

class RequestMsg(object):
	def __init__(self, xmlData):
		self.ToUserName = xmlData.find('ToUserName').text
		self.FromUserName = xmlData.find('FromUserName').text
		self.CreateTime = xmlData.find('CreateTime').text
		self.MsgType = xmlData.find('MsgType').text
		self.MsgId = xmlData.find('MsgId').text
class RequestTextMsg(RequestMsg):
	def __init__(self, xmlData):
		RequestMsg.__init__(self, xmlData)
		self.Content = xmlData.find('Content').text.encode("utf-8")
# class RequestImageMsg(Msg):
#     def __init__(self, xmlData):
#         Msg.__init__(self, xmlData)
#         self.PicUrl = xmlData.find('PicUrl').text
#         self.MediaId = xmlData.find('MediaId').text


class ResponseMsg(object):
	def __init__(self):
		pass
	def send(self):
		return "success"
class ResponseTextMsg(ResponseMsg):
	def __init__(self, toUserName, fromUserName, content):
		self.__dict = dict()
		self.__dict['ToUserName'] = toUserName
		self.__dict['FromUserName'] = fromUserName
		self.__dict['CreateTime'] = int(time.time())
		self.__dict['Content'] = content
	def send(self):
		XmlForm = """
		<xml>
		<ToUserName><![CDATA[{ToUserName}]]></ToUserName>
		<FromUserName><![CDATA[{FromUserName}]]></FromUserName>
		<CreateTime>{CreateTime}</CreateTime>
		<MsgType><![CDATA[text]]></MsgType>
		<Content><![CDATA[{Content}]]></Content>
		</xml>
		"""
		return XmlForm.format(**self.__dict)
# class ResponseImageMsg(Msg):
#     def __init__(self, toUserName, fromUserName, mediaId):
#         self.__dict = dict()
#         self.__dict['ToUserName'] = toUserName
#         self.__dict['FromUserName'] = fromUserName
#         self.__dict['CreateTime'] = int(time.time())
#         self.__dict['MediaId'] = mediaId
#     def send(self):
#         XmlForm = """
#         <xml>
#         <ToUserName><![CDATA[{ToUserName}]]></ToUserName>
#         <FromUserName><![CDATA[{FromUserName}]]></FromUserName>
#         <CreateTime>{CreateTime}</CreateTime>
#         <MsgType><![CDATA[image]]></MsgType>
#         <Image>
#         <MediaId><![CDATA[{MediaId}]]></MediaId>
#         </Image>
#         </xml>
#         """
#         return XmlForm.format(**self.__dict)



def getReplyMessage(msg):

	access_token = "2.00I5AbVGggAvDC6965055b43ewYwNC" # Need to renew every 5 years
	headers = { 'Accept':'application/json, text/plain, */*',
		'Accept-Encoding':'gzip, deflate, sdch, br',
		'Accept-Language':'zh-CN,zh;q=0.8',
		'Connection':'keep-alive',
		'Cookie':'_T_WM=e6c87e2d385a294d5bd50b38dce06e8c; M_WEIBOCN_PARAMS=luicode%3D10000011%26lfid%3D1005056114898825%26fid%3D1005056114898825%26uicode%3D10000011',
		'Host':'m.weibo.cn',
		'Referer':'https://m.weibo.cn/u/6114898825/',
		'User-Agent':'Mozilla/5.0 (Windows NT 10.0; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/55.0.2883.87 Safari/537.36',
		'X-Requested-With':'XMLHttpRequest'}
	rand = random.randint(1,50)
	p = 1
	while rand > 0:
		url = 'https://m.weibo.cn/api/container/getIndex?containerid=1076035963683040&page=%d&count=100'%p
		r = requests.get(url,headers = headers)
		r.raise_for_status()
		data = json.loads(r.text,encoding='utf-8')
		if data['ok'] == 0:
			return "我自闭了"
		for c in data['data']['cards']:
			if c['card_type'] != 9 or 'retweeted_status' in c['mblog'] or '分享图片' in c['mblog']['text']:
				continue
			rand -= 1
			if rand == 0:
				return BeautifulSoup(c['mblog']['text'], 'html.parser').get_text()
