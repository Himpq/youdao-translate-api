import base64
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
    keyid_pattern = r'async\(\{commit:e\},t\)\=\>\{const\s+a="'+key+'([^"]+)",n="([^"]+)"'
    match         = re.search(keyid_pattern, data)
    if match:
        keyid      = key+match.group(1)
        const_sign = match.group(2)
        return keyid, const_sign
    
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
            "sec-ch-ua-platform": "\"Windows\"",
            "cookie": "OUTFOX_SEARCH_USER_ID=1514108552@111.58.53.137; _uetsid=faadcbd0598411f0a082c1e8b007b95c; _uetvid=faadec80598411f0905aa19b0415a81d; OUTFOX_SEARCH_USER_ID_NCOO=1314097494.1249926; DICT_DOCTRANS_SESSION_ID=YWI5ZGFiZjMtYWZjYS00NmRmLThlMzYtYTM3NDU5OTBmNTFk"
        }
    )
    # print("==>get keys:", req.json(), '\n')
    return req.json()['data']

def translate(content):
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
        #"cookie": "OUTFOX_SEARCH_USER_ID=1514108552@111.58.53.137; _uetsid=faadcbd0598411f0a082c1e8b007b95c; _uetvid=faadec80598411f0905aa19b0415a81d; OUTFOX_SEARCH_USER_ID_NCOO=1314097494.1249926; DICT_DOCTRANS_SESSION_ID=YWI5ZGFiZjMtYWZjYS00NmRmLThlMzYtYTM3NDU5OTBmNTFk"
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

    #print(req.content)
    
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
    return decrypted.decode('utf-8')

if __name__ == "__main__":
  print(translate("World is just a large loop."))  # Example usage
  
