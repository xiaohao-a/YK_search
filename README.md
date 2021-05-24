
### 请求某酷的搜索页面需要哪些参数？
- 查询字符串：t时间戳、sign加密字符串、appkey、aaid、utdld（~~与cookie中的cna值相同~~，实际可以为null）、pg（页面参数）
- cookie：cna、_m_h5-tk、_m_h5-tk_enc

### t时间戳
- 时间戳需要精准才能正常请求，应该是和**sign字符串配合进行验证**   
示例：1621570855120

### sign是如何生成的？   
- js文件地址：
```
https://g.alicdn.com/某酷-node/activity-components/1.0.12/static/js/live-window.js
```
- 1855行，赋值sign
- 1850行，生成参数传入1712运算函数，生成32位加密字符串   
    **后端应该使用该加密方法（可能是md5，没有深究）进行对比验证**   
    需要注意两点
   - 去掉json.dumps的空格，添加参数**separators=(',',':')**
   - 避免中文自动转Unicode，添加参数**ensure_ascii=False**
- 传入的参数为：
**_m_h5_tk前半部分 + 时间戳 + appkey + 下面的json字符数据**
```
{"searchType":1,
"keyword":"love",  // 不要写死，动态传参
"pg":2,  //页码参数
"pz":20,
"site":1,
"appCaller":"pc",
"appScene":"mobile_multi",
"userTerminal":2,
"sdkver":313,
"userFrom":1,
"noqc":0,
"aaid":"f2e7c01bff7bac152d72a789d3be6cbc",  //在响应源码中获取window.__aaid__值
"ftype":0,
"duration":"",
"categories":"",
"ob":"",
"utdId": unll,  //也有和cookie cna值相同的情况
"userType":"guest",
"userNumId":0,
"searchFrom":"1",
"sourceFrom":"home"}
```
需要分析的参数如下：
- **appkey**；
- 传入的参数包含两个cookie数据：
   - **_m_h5_tk**;
   - **utdld**(~~与cookies中cna相同~~，实际可以为null);   
      **python没有null，这里可以考虑用None，使用json.dumps可以转换为null**
- 还有一个藏在页面源码中**aaid**

### appkey   
appkey在js文件中是固定值**23774304**

### _m_h5_tk如何获取？   
**可以考虑使用session保持cookie**
- 获取令牌：将appkey作为查询字符串进行请求
```
GET https://acs.某酷.com/h5/mtop.某酷.soku.yksearch/2.0/?appKey=23774304 HTTP/1.1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36
Host: acs.某酷.com
Content-Length: 2
```
- 获取结果：   
```
Response sent 114 bytes of Cookie data:
	Set-Cookie: _m_h5_tk=7f64920a835200980c4b34cba403ca48_1621601677406;Path=/;Domain=某酷.com;Max-Age=86400;SameSite=None;Secure   
Response sent 104 bytes of Cookie data:
	Set-Cookie: _m_h5_tk_enc=816546d38c4d03fcf82c80224f9111dd;Path=/;Domain=某酷.com;Max-Age=86400;SameSite=None;Secure
```
### aaid如何获取？
**考虑拿取源码使用正则匹配**   
aaid来自页面中的window.\_\_aaid__ ="0cb7eabe95579f16f0cbeba7d948434a"   

- 请求如下：（**URL中包含了搜索的关键字、携带cookie数据cna**）
```
GET https://so.某酷.com/search_video/q_love?searchfrom=1 HTTP/1.1
User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36
Referer: https://so.某酷.com/search_video/q_love?searchfrom=1
Cookie: cna=P4MuGQ8AFBECAdOi2uF/uK6p
Host: so.某酷.com
```

### cna是如何生成的？
cna的过期时间非常久，有20年
- 现获取一小段js文件，赋值给window
- 地址 https://log.mmstat.com/eg.js?t=1621614322834
```
window.goldlog=(window.goldlog||{});goldlog.Etag="1PzVGIkuR1wCAbff1iDG8uj9";goldlog.stag=1;
```
- 检查cookie值cna如果不等于上面的Etag值，则将cookie值赋值为Etag值

### 模拟请求逻辑整理
获取cna ==> 获取aaid ==> 获取令牌 ==> 计算sign ==> 发起搜索请求







