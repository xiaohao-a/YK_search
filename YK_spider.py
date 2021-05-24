"""
某酷视频网的搜索请求模拟，有脱敏
"""
import re
import sys
import csv
import time
import json
# import execjs
import requests
import traceback
from fake_useragent import UserAgent
from urllib import parse


class YKSpider:
    def __init__(self, kw):
        self.url = 'https://acs.某酷.com/h5/mtop.某酷.soku.yksearch/2.0/'  # 最终请求xhr数据的地址
        self.kw = kw  # 搜索关键字
        self.appkey = '23774304'
        # sign的加密逻辑在js文件中
        # with open('sdks.js','r',encoding='utf8') as f:
        #     data = f.read()
        #     self.exec_obj = execjs.compile(data)
        # 打开一个Excel文件，准备写入数据
        self.f = open('%s_result.csv' % kw, 'w', newline='', encoding='utf8')
        self.writer = csv.writer(self.f)
        self.writer.writerow(['页数', '视频标题', '视频地址'])

    def fresh_token_and_feature(self):
        """ 更新令牌以及请求头等 """
        self.ua = UserAgent().random
        print('UA: ', self.ua)
        self.cna = self.get_cna()
        self.aaid = self.get_aaid()
        self.token = self.get_token()
        self.cookies = {
            'cna': self.cna,
            '_m_h5_tk': self.token['_m_h5_tk'],
            '_m_h5_tk_enc': self.token['_m_h5_tk_enc']
        }
        self.headers = {
            'Accept': 'application/json',
            'User-Agent': self.ua,
            'Content-type': 'application/x-www-form-urlencoded',
            'Referer': 'https://so.某酷.com/',
        }

    def get_cna(self):
        """获取cna值，后面会用到cookie中"""
        headers = {'User-Agent': self.ua}
        response = requests.get(url='https://log.mmstat.com/eg.js', headers=headers, verify=False).text
        try:
            cna = re.findall(r'goldlog.Etag="(.*?)";', response, re.S)[0]
        except:
            traceback.print_exc()
            sys.exit('message：can not get cna data')
        print('cna:', cna)
        return cna

    def get_aaid(self):
        """ 不同的搜索关键词有不同的aaid值，aaid藏在响应源码中"""
        kw = parse.quote(self.kw)  # 中文放在URL中需要编码
        url = 'https://so.某酷.com/search_video/q_{}?searchfrom=1'.format(kw)
        headers = {
            'User-Agent': self.ua,
            'Referer': url,
        }
        cookies = {'cna': self.cna}
        response = requests.get(url=url, headers=headers, cookies=cookies, verify=False).text
        try:
            aaid = re.findall(r'window.__aaid__ ="(.*?)";', response, re.S)[0]
        except:
            traceback.print_exc()
            print(response)
            sys.exit("message: can not get 'aaid' data")
        print('aaid:', aaid)
        return aaid

    def get_token(self):
        """ 只需要appkey就可以拿到令牌"""
        headers = {'User-Agent': self.ua}
        url = 'https://acs.某酷.com/h5/mtop.某酷.soku.yksearch/2.0/?appKey=%s' % self.appkey
        response = requests.get(url=url, headers=headers, verify=False)
        tokens = requests.utils.dict_from_cookiejar(response.cookies)
        print("tokens:", tokens)
        return tokens

    def get_time_stamp(self):
        """ 返回字符串类型时间戳 """
        time_now = time.time()
        time_sign = int(time_now * 1000)
        return str(time_sign)

    def create_sign_input(self, kw, pg, aaid):
        """ sign加密前出入的json数据部分，暴露传值方便调试 """
        data = {
            "searchType": 1,
            "keyword": kw,
            "pg": pg,
            "pz": 20,
            "site": 1,
            "appCaller": "pc",
            "appScene": "mobile_multi",
            "userTerminal": 2,
            "sdkver": 313,
            "userFrom": 1,
            "noqc": 0,
            "aaid": aaid,
            "ftype": 0,
            "duration": "",
            "categories": "",
            "ob": "",
            "utdId": None,
            "userType": "guest",
            "userNumId": 0,
            "searchFrom": "1",
            "sourceFrom": "home"
        }
        return json.dumps(data, separators=(',', ':'), ensure_ascii=False)

    # sign的加密调用
    def __js_sdk(self, data):
        # sign = self.exec_obj.call('sign_sdk', data)
        # 取消了execjs执行加密文件，在服务器上搭建了node服务来计算sign值，我的服务器地址就不透露了
        # 当然execjs是完全可行的，readme中已经告知了加密位置，扣下算法很简单的
        data = {'input_str': data}
        sign = requests.post(url='http://x.xx.xx.xx:3000/get_sign', data=data).text
        print('获取sign成功：', sign)
        return sign

    def get_sign(self, token, time_sign, data):
        """
        获取加密sign
        :param token:包含'_m_h5_tk'cookie数据的字典
        :param time_sign:字符串时间戳
        :param data:json字符串
        :return: 加密sign
        """
        try:
            token_tk = token['_m_h5_tk'].split('_')[0]
        except:
            traceback.print_exc()
            sys.exit("message: can not get token '_m_h5_tk'")
        # 拼接字符串，传入加密函数
        input_data = token_tk + '&' + time_sign + '&' + self.appkey + '&' + data
        sign = self.__js_sdk(input_data)
        return sign

    def run(self):
        self.fresh_token_and_feature()
        pg = 18
        error_times = 0
        while pg <= 20:
            # 多次抓取均在第11次抓取时被限制，暂时考虑在第11次请求直接更新特征
            if pg == 11:
                self.fresh_token_and_feature()
            time_sign = self.get_time_stamp()
            data = self.create_sign_input(self.kw, pg, self.aaid)
            sign = self.get_sign(self.token, time_sign, data)
            params = (
                ('jsv', '2.5.1'),
                ('appKey', self.appkey),
                ('t', time_sign),
                ('sign', sign),
                ('api', 'mtop.某酷.soku.yksearch'),
                ('type', 'originaljson'),
                ('v', '2.0'),
                ('ecode', '1'),
                ('dataType', 'json'),
                ('jsonpIncPrefix', 'headerSearch'),
                ('data',
                 '{"searchType":1,"keyword":"%s","pg":%s,"pz":20,"site":1,"appCaller":"pc","appScene":"mobile_multi","userTerminal":2,"sdkver":313,"userFrom":1,"noqc":0,"aaid":"%s","ftype":0,"duration":"","categories":"","ob":"","utdId":null,"userType":"guest","userNumId":0,"searchFrom":"1","sourceFrom":"home"}'
                 % (self.kw, str(pg), self.aaid)
                 ),
            )
            response_json = ''
            try:
                response = requests.get(self.url, headers=self.headers,
                                        params=params, cookies=self.cookies, verify=False)
                response_json = response.json()
                # 视频信息列表
                info_list = response_json['data']['nodes']
            except:
                traceback.print_exc()
                print('获取第%s页数据不正常：' % pg, response_json)
                print('更新特征后重试，更新token中。。。')
                time.sleep(3)
                self.fresh_token_and_feature()
                error_times += 1
                if error_times < 3:
                    continue
                else:
                    sys.exit('连续3次更新token未能获取正常数据！')
            print('第%s页数据获取成功：' % pg)
            # 解析数据，或打印，或存储
            json_data = self.parse_data(pg, info_list)
            self.save_json_data(json_data)
            # 最后一页isEnd值为1
            if response_json['data']['data']['isEnd']:
                self.f.close()
                print('=== 爬取结束，共爬取%s页数据 ===' % pg)
                break
            pg = pg + 1
            error_times = 0

    def parse_data(self, pg, data):
        """ 遍历json数据，返回新的json数据，包含标题和链接 """
        videos_str = ''
        print('原始视频节点数据：', data)
        # 源数据结构杂-_-!
        try:
            for item in data:
                nodes_list01 = item['nodes']
                for i in nodes_list01:
                    nodes_list02 = i['nodes']
                    json_str = self.create_json_str(nodes_list02)
                    videos_str += json_str
        except:
            traceback.print_exc()
            print('解析数据出错！')
        # 拼接json字符，每页数据输出一个字典
        videos_str = '[' + videos_str[0:-1] + ']'
        videos_json = json.loads(videos_str)
        result_json = {
            'page': pg,
            'data': videos_json
        }
        return result_json

    def create_json_str(self, data):
        # 一页中的一行视频内有多个URL，遍历处理
        json_str = ''
        for j in data:
            try:
                title = j['data']['titleDTO']['displayName']
                # video_id可以直接访问
                video_id = j['data'].get('videoId')
                # 同一行中并排多个视频，id为'realShowId'，URL会302跳转到最终页面
                real_show_id = j['data'].get('realShowId')
                if video_id:
                    url = 'https://v.某酷.com/v_show/id_%s.html' % video_id
                elif real_show_id:
                    url = 'https://v.某酷.com/v_nextstage/id_%s.html' % real_show_id
                else:
                    # 存在有标题但是没有关键特征的数据，当然浏览器上也看不到
                    continue
                single_video = {'title': title, 'url': url}
                json_str += (json.dumps(single_video, ensure_ascii=False) + ',')
            except:
                # 节点列表内也不一定全都有title
                continue
        if json_str:  # 仅仅打印查看节点列表内解析出的视频信息
            print(json_str)
        return json_str

    # 这里存储到excel文件
    def save_json_data(self, json_data):
        """ 将构造好的json数据再重新构造存入CSV文件 """
        try:
            page = json_data['page']
            data_list = json_data['data']
        except:
            return  # 存在最后一页没有数据的情况，直接return掉
        info_rows = []
        for info in data_list:
            title = info['title']
            url = info['url']
            info_one_row = (page, title, url)  # 单行数据
            info_rows.append(info_one_row)  # 构建多行数据
        print(info_rows)
        self.writer.writerows(info_rows)  # 多行数据写入文件
        # print(json_data)


if __name__ == '__main__':
    k = input('请输入需要搜索的视频：')
    spider = YKSpider(k)
    spider.run()
