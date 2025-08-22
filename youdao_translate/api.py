

import base64
import json
import requests, hashlib, time
import re
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

HTTP_URL = "https://dict.youdao.com/webtranslate"

def getProductKeys(key="webfanyi", useTemp = False):
    """获取有道翻译产品ID与产品密钥"""
    if useTemp:
        return "webfanyi-key-getter-2025", "yU5nT5dK3eZ1pI4j"
    
    url           = "https://shared.ydstatic.com/dict/translation-website/0.6.6/js/app.78e9cb0d.js"
    data          = requests.get(url).text
    keyidPattern = r'async\(\{commit:e\},t\)\=\>\{const\s+a="'+key+'([^"]+)",n="([^"]+)"'
    match         = re.search(keyidPattern, data)
    if match:
        keyid      = key+match.group(1)
        constSign = match.group(2)
        return keyid, constSign
    
    else:
        return "webfanyi-key-getter-2025", "yU5nT5dK3eZ1pI4j" 

def getSign(constSign):
    """根据产品密钥生成加密签名"""

    mysticTime = str(int(time.time() * 1000))
    sign       = f"client=fanyideskweb&mysticTime={mysticTime}&product=webfanyi&key={constSign}"

    # print("==>get sign:", sign, hashlib.md5(sign.encode('utf-8')).hexdigest(),'\n')

    return hashlib.md5(sign.encode('utf-8')).hexdigest()

def getKeys():
    """获取有道secertKey和AES加密的密钥"""

    keyid, constSign = getProductKeys()
    sign             = getSign(constSign)

    req  = requests.get(
        "https://dict.youdao.com/webtranslate/key",
        params = {
            "keyid": keyid,
            "sign": sign,
            "client": "fanyideskweb",
            "product": "webfanyi",
            "appVersion": "1.0.0",
            "vendor": "web",
            "pointParam": "client,mysticTime,product",
            "mysticTime": str(int(time.time() * 1000)),
            "keyfrom": "fanyi.web",
            "mid": "1",
            "screen": "1",
            "model": "1",
            "network": "wifi",
            "abtest": "0",
            "yduuid": "abcdefg"
        },
        headers={
            "Accept": "application/json, text/plain, */*",
            "Accept-Language": "zh-CN,zh;q=0.9",
            "Connection": "keep-alive",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://fanyi.youdao.com",
            "Referer": "https://fanyi.youdao.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-site",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
            "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": "\"Windows\""
        }
    )
    # print("==>get keys:", req.json(), '\n')

    if not req.json().get("data"):
        return getKeys()
    return req.json()['data']

def translate(content):
    # 预处理内容，保持段落结构
    paragraphs = content.split('\n\n')
    if len(paragraphs) <= 1:
        paragraphs = content.split('\n')
    
    # 过滤空段落
    paragraphs = [p.strip() for p in paragraphs if p.strip()]
    
    if not paragraphs:
        return {
            "translation": "",
            "alignedOriginal": ""
        }
    
    # 如果段落太多，分批处理
    if len(paragraphs) > 10:
        # 分组处理，每组最多10个段落
        allTranslations = []
        allAlignedOriginals = []
        
        for i in range(0, len(paragraphs), 8):
            batch = paragraphs[i:i+8]
            batchContent = '\n'.join(batch)
            batchResult = translateBatch(batchContent)
            
            if isinstance(batchResult, dict) and 'translation' in batchResult:
                allTranslations.extend(batchResult['translation'].split('\n'))
                allAlignedOriginals.extend(batchResult['alignedOriginal'].split('\n'))
            else:
                # 处理错误情况
                allTranslations.extend(batch)
                allAlignedOriginals.extend(batch)
        
        return {
            "translation": '\n'.join(allTranslations),
            "alignedOriginal": '\n'.join(allAlignedOriginals)
        }
    else:
        # 直接翻译
        joinedContent = '\n'.join(paragraphs)
        return translateBatch(joinedContent)

def translateBatch(content):
    """对多行翻译文本进行对齐处理"""
    keyid, constSign = getProductKeys()
    keys = getKeys()
    aeskey, aesiv, secretKey = keys['aesKey'], keys['aesIv'], keys['secretKey']
    sign, mysticTime = getSign(secretKey), str(int(time.time() * 1000))

    headers = {
        "Accept": "application/json, text/plain, */*",
        "Accept-Language": "zh-CN,zh;q=0.9",
        "Connection": "keep-alive",
        "Content-Type": "application/x-www-form-urlencoded",
        "Origin": "https://fanyi.youdao.com",
        "Referer": "https://fanyi.youdao.com/",
        "Sec-Fetch-Dest": "empty",
        "Sec-Fetch-Mode": "cors",
        "Sec-Fetch-Site": "same-site",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
        "sec-ch-ua": "\"Google Chrome\";v=\"131\", \"Chromium\";v=\"131\", \"Not_A Brand\";v=\"24\"",
        "sec-ch-ua-mobile": "?0",
        "sec-ch-ua-platform": "\"Windows\"",
        "cookie": "OUTFOX_SEARCH_USER_ID=1514108552@111.58.53.137; _uetsid=faadcbd0598411f0a082c1e8b007b95c; _uetvid=faadec80598411f0905aa19b0415a81d; OUTFOX_SEARCH_USER_ID_NCOO=1314097494.1249926; DICT_DOCTRANS_SESSION_ID=YWI5ZGFiZjMtYWZjYS00NmRmLThlMzYtYTM3NDU5OTBmNTFk"
    }

    data = {
        "i": content,
        "from": "auto",
        "to": "",
        "useTerm": "false",
        "dictResult": "true",
        "keyid": "webfanyi",
        "sign": sign,
        "client": "fanyideskweb",
        "product": "webfanyi",
        "appVersion": "1.0.0",
        "vendor": "web",
        "pointParam": "client,mysticTime,product",
        "mysticTime": mysticTime,
        "keyfrom": "fanyi.web",
        "mid": "1",
        "screen": "1",
        "model": "1",
        "network": "wifi",
        "abtest": "0",
        "yduuid": "abcdefg"
    }

    req = requests.post(
        "https://dict.youdao.com/webtranslate",
        data=data,
        headers=headers
    )

    # print(req.content)
    
    # 多个getKeys请求会被拒绝

    encodeAesKey, encodeAesIv = hashlib.md5(
        aeskey.encode()
    ).digest(), hashlib.md5(
        aesiv.encode()
    ).digest()

    cipher = AES.new(encodeAesKey, AES.MODE_CBC, encodeAesIv)
    ctxs   = base64.urlsafe_b64decode(req.text)

    decrypted = unpad(cipher.decrypt(ctxs), AES.block_size)
    # print(decrypted.decode())
    data = json.loads(decrypted.decode('utf-8'))
    
    translatedCtx = ""

    try:
        # 获取翻译结果 - 同时返回翻译文本和对齐的原文
        if 'translateResult' in data and data['translateResult'] and len(data['translateResult']) > 0:
            paras = data['translateResult'][0]
            
            # 提取翻译文本和对应的原文
            translatedParts = []
            alignedOriginalParts = []
            
            for para in paras:
                if 'tgt' in para and 'src' in para:
                    translatedParts.append(para['tgt'])
                    alignedOriginalParts.append(para['src'])
            
            # 用换行符连接
            translatedCtx = '\n'.join(translatedParts)
            alignedOriginal = '\n'.join(alignedOriginalParts)
            
            # 返回包含翻译文本和对齐原文的字典
            return {
                "translation": translatedCtx,
                "alignedOriginal": alignedOriginal
            }
                
        else:
            return {
                "translation": "",
                "alignedOriginal": ""
            }

    except Exception as e:
        return {
            "error": f"Translation failed: {data}, Error: {str(e)}",
        }
