import AESmod
import PNG_io
import HENMAP_chaos_model
import hashlib
import random
from HENMAP_chaos_model import Chaos
from AESmod import AEScharp


class chaos_decrypt_mod:

    def __init__(self, msg, DEBUG=0):

        self.data = bytes.fromhex(msg['_target'])
        self.temp_Um = msg['_Um']
        self.temp_Um = self.temp_Um[1:-1].split(", ")
        self.use_key = hashlib.sha256(msg['_key'].encode('utf-8')).digest()
        self.use_key = list(self.use_key)
        self.msg = msg
        self.Y = [random.random(), random.random(), random.random()]
        self.getData = ""
        self.DEBUG = DEBUG

    def date_analyzing(self):
        pass

    def decrypt_Um(self):
        if self.DEBUG == 1:
            print("decrypt_Um.Um同步前值", self.temp_Um)
        for i in range(len(self.temp_Um)):
            self.temp_Um[i] = float(self.temp_Um[i])
            self.temp_Um[i] -= float(self.use_key[i])
        if self.DEBUG == 1:
            print("decrypt_Um.Um同後前值", self.temp_Um)

    def sync_Key(self):
        async_flag = False  # 同步旗標
        times = 0  # 同步失敗次數
        while async_flag is False:

            client = Chaos()
            US = 0
            for i in range(len(self.temp_Um) - 1, -1, -1):
                self.Y = client.runSlave(2, self.Y, self.temp_Um[i])
                if i == 1:
                    US = client.createUs(self.Y)
            # 判斷有沒有同步
            if round(self.temp_Um[0] + US, 6):  # 計算UK 若是0表示同步 反知
                async_flag = False
                if times > 12:  # 嘗試同步最高次數
                    break
                times += 1
            else:  # 同步成功
                async_flag = True

    def decrypt(self):
        aes = AEScharp()
        self.getData = aes.decrypt_ECB(self.data, round(self.Y[0], 4))

    def pack_jason(self):
        msg = self.msg
        msg['_target'] = self.getData
        if '_key' in msg: del msg['_key']
        if '_Um' in msg: del msg['_Um']
        return msg

    def show_data(self):
        print("-----Chaos_decrypt_mod DEBUG Show Data-----")
        print("msg : ", self.msg)
        print("-------------------------------------------")
        print("temp_Um : ", self.temp_Um)
        print("use_key : ", "".join("%02x" % b for b in self.use_key))
        print("Y : ", self.Y)
        print("msg : ", self.getData)


# 傳輸格式規範
# _target   資料
# _key      使用者密鑰
class chaos_encrypt_mod:

    def __init__(self, msg, temp_Um, key):
        self.data = msg['_target']  #
        self.temp_Um = temp_Um  #
        self.key = key
        self.use_key = hashlib.sha256(msg['_key'].encode('utf-8')).digest()
        self.use_key = list(self.use_key)
        self.getData = ""

        self.msg = msg

    def date_analyzing(self):
        pass

    def encrypt_Um(self):
        for i in range(32):
            self.temp_Um[i] = round(self.temp_Um[i] + self.use_key[i], 7)

    def encrypt(self):
        aes = AEScharp()
        self.getData = aes.encrypt_ECB(self.data, round(self.key, 4)).hex()

    def pack_jason(self):
        msg = self.msg
        msg['_target'] = self.getData
        msg['_Um'] = str(self.temp_Um)
        if '_key' in msg: del msg['_key']

        return msg

    def show_data(self):
        print("-----Chaos_encrypt_mod DEBUG Show Data-----")
        print("msg : ", self.msg)
        print("-------------------------------------------")
        print("temp_Um : ", self.temp_Um)
        print("use_key : ", "".join("%02x" % b for b in self.use_key))
        print("send_key : ", self.key)
        print("getData : ", self.getData)


class Do_json():

    def __init__(self, key, DEBUG=0):
        self.key = key
        self.DEBUG = DEBUG

    def de_json(self, msg):
        aes = AEScharp()
        msg = bytes.fromhex(msg)
        msg = aes.de_ECB(msg, self.key)

        if self.DEBUG == 1:
            print("未處理前: ", msg)

        msg = msg[:msg.find('\x00')]  # 除掉\x00

        if msg[-1] != "}":  # 有些}會不見 處理回來
            msg += "}"

        if self.DEBUG == 1:
            print("處理後: ", msg)
        msg = eval(msg)
        return msg

    def en_json(self, msg):
        aes = AEScharp()
        msg = aes.en_ECB(str(msg).encode('utf8'), self.key).hex()
        return msg

    def show_key(self):
        print(self.key)


if __name__ == "__main__":
    a = "{\"_key\":\"123\",\"_target\":\"a42f021ff92da7c33098e5b4968305feff148000de5a0988f8b8c9d87c78551e\",\"_Um\":\"[164.2950518, 99.9946069, 163.5828062, 86.2630644, 30.7453017, 65.8593988, 46.3803316, 154.7825802, 62.5499659, 125.6747811, 71.8237903, 100.6581949, 237.1025707, 219.814746, 75.8667899, 182.3496457, 159.9736891, 73.5129965, 29.5355083, 60.6298494, 254.3858611, 30.7546275, 158.9994515, 124.6135657, 152.296228, 139.0942435, 132.9723916, 246.9144103, 246.2579802, 160.1542444, 121.0210298, 226.5601541]\"}"
    de = chaos_decrypt_mod(a)
    de.decrypt_Um()
    de.sync_Key()
    de.decrypt()
    print(de.pack_jason())