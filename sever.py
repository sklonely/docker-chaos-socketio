#!/usr/bin/python3
# 文件名：server.py

import hashlib
import os
import random
import socket
import sys
import threading
import time

import copy
from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit
import json
import codecs

#import from lib
sys.path.append(sys.path[0] + '/mods/')
from AESmod import AEScharp
from HENMAP_chaos_model import Chaos
from flask_cors import CORS
from all_mod_main import chaos_decrypt_mod, Do_json, chaos_encrypt_mod

# local modules

X = []  # 混沌亂數
Y = []
sid_Y = {}
send_key = {}
Um = 0
sr_chaos = Chaos()
pc_flage = 0

app = Flask(__name__, template_folder='./')
app.config['SECRET_KEY'] = 'secret!'
# CORS(app)
socketio = SocketIO(app, path="chaos", pingTimeout=120)


# 副程式
def floor(num, t):
    if num < 0:
        return str(num)[:3 + t]
    else:
        return str(num)[:2 + t]


def chaos():
    # 初始化 準備Um buff
    sys_chaos = Chaos()
    global X, Um
    X = [random.random(), random.random(), random.random()]
    Um = []
    for i in range(32):
        Um.append(0)
    Um[0] = sys_chaos.createUm(X)
    X = sys_chaos.runMaster(0, X)
    # 進入迴圈開始跑渾沌
    while 1:
        for i in range(31, 0, -1):
            Um[i] = Um[i - 1]
        Um[0] = sys_chaos.createUm(X)
        X = sys_chaos.runMaster(1, X)
        time.sleep(0.002)


def chaos_S():  # 渾沌模組
    # 初始化 準備Um buff
    global Y
    Y = [random.random(), random.random(), random.random()]
    Y = sr_chaos.runSlave(0, Y, Um)


# HTTP 路由
@app.route('/')
def index():
    return render_template('web/index.html')


@app.route('/DeBug')
def DeBug():
    return render_template('web/generic.html')


@app.route('/check_sid_frome')
def check_sid_frome():
    t = {}

    print("DeBug mod get Key froms")
    for i in send_key.keys():
        t[i] = send_key[i].hex()

    return json.dumps(t)


# socketio 路由


# 傳輸格式規範
# _target   資料
# _key      使用者密鑰
# _Um       就只是Um
@socketio.on("e2eDecrypt")
def decrypt(msg):

    print("解密端 : 收到請求，來源-", request.sid)
    if str(request.sid) in send_key:
        try:
            do_json = Do_json(send_key[str(request.sid)])
            msg = do_json.de_json(msg)  # 解密json檔
            print("解密端 : 解包成功")
            decode_c = True
        except:
            print("解密端 : 解包失敗")
            decode_c = False
            emit("none_key", "There is not has key")
        if decode_c:
            de = chaos_decrypt_mod(msg)  # 初始化解碼資料
            de.decrypt_Um()  # 解密 Um
            de.sync_Key()  # 同步金鑰
            de.decrypt()  # 使用金鑰解密資料

            msg = de.pack_jason()  # 資料打包
            print("解密端 : 資料解密完成")
            print("解密完資料(給請求端):", msg['_target'], "長度:", len(msg['_target']))
            res = do_json.en_json(msg)  # 加密資料成json的字串

            emit('e2eDecryptReturn', res)  # 回傳
    else:
        print("解密端[-錯誤-] : 該使用者，未在伺服器申請過通訊金鑰")
        emit("none_key", "There is not has key")

    print("解密端: 已回應完請求\n---------------------------")


# 傳輸格式規範
# _target   資料
# _key      使用者密鑰
@socketio.on("e2eEncrypt")
def encrypt(msg):

    print("加密端 : 收到請求，來源-", request.sid)

    # 初始化加密資料
    temp_Um = copy.deepcopy(Um)
    key = copy.deepcopy(X[0])
    # 判斷使用者有沒有金鑰
    if str(request.sid) in send_key:
        # 解包
        do_json = Do_json(send_key[str(request.sid)])
        msg = do_json.de_json(msg)
        print("加密端 : 解包成功")

        en = chaos_encrypt_mod(msg, temp_Um, key)  # 加密準備

        en.encrypt_Um()  # Um加密

        en.encrypt()  # 加密資料

        msg = en.pack_jason()  # 打包jason
        print("加密端 : 資料加密完成")
        print("加密完資料:", msg['_target'], "長度:", len(msg['_target']))
        res = do_json.en_json(msg)
        # 傳送
        emit("e2eEncryptReturn", res)
    else:
        print("加密端[-錯誤-] : 該使用者，未在伺服器申請過通訊金鑰")
        emit("none_key", "There is not has key")
    print("加密端 : 已回應完請求\n---------------------------")


@socketio.on('test')
def connected_msg(msg):
    emit("test_reply", msg)


@socketio.on('SyncReady')
def chaos_ready(msg):
    global Y, sid_Y
    print("收到同步請求")
    chaos_S()
    print("初始化混沌: ", round(Y[0], 6))

    um = round(float(msg), 6)
    us = round(sr_chaos.createUs(Y), 6)
    sid_Y[str(request.sid)] = sr_chaos.runSlave(2, Y, um)
    print("第一次計算完成")
    emit('UmCatch', False)
    print("送出請求", sid_Y)


@socketio.on('UmPush')
def chaos_um(msg):
    global Y, sid_Y, send_key
    Y = sid_Y[str(request.sid)]
    um = round(float(msg), 6)
    us = round(sr_chaos.createUs(Y), 6)

    print("請求來源:", str(request.sid))

    if um + us == 0:
        print("同步完成: ", um + us, round(Y[0], 6))
        emit('UmCatch', True)

        print("金鑰建立:")
        Y123 = (floor(Y[0], 4) + "/" + floor(Y[1], 4) + "/" + floor(Y[2], 4))
        temp_key = hashlib.sha256(Y123.encode('utf-8')).digest()

        print("hash前(字串)", Y123)
        print("hash前(16禁制)", Y123.encode('utf8').hex())
        print("hash完", temp_key.hex())
        print("------------------以上金鑰取得通訊完成--------------------")

        send_key[str(request.sid)] = temp_key
        Y = temp_key
    else:
        Y = sr_chaos.runSlave(2, Y, um)
        sid_Y[str(request.sid)] = Y
        print("同步中: ", um + us, round(sid_Y[str(request.sid)][0], 6))
        emit('UmCatch', False)
        # print("送出請求")


@socketio.on('data_test')
def c(msg):
    print("資料來源端:")
    print("密文: ", msg)
    print(type(msg))

    aes = AEScharp()
    key = Y
    print("現在端口的key", key.hex())
    # 將STR 換成 BIN
    msg = bytes.fromhex(msg)
    print("現在端口轉換完MSG(整串)", msg, "長度:", len(msg))
    msg = aes.de_ECB(msg, key)

    print("結果:")
    a = "{\"_target\":\"456\",\"_key\":\"123\"}"
    print(msg.find('\x00'), msg[:msg.find('\x00')])
    msg = msg[:msg.find('\x00')]
    msg = eval(msg)
    print(type(msg), msg)

    # print("\n測試加密:")
    # res = aes.en_ECB("123".encode('utf8'), key)
    # print("加密123 UTF8 解碼後:", "123".encode('utf8'), "123".encode('utf8').hex())
    # print("加密完的密文:", res, "len", len(res), res.hex(), "len", len(res.hex()))


# socket 原生emit
@socketio.on('connect')
def test_connect():
    print("伺服器 : 來源", str(request.sid), '連接成功。')


@socketio.on('disconnect')
def test_disconnect():
    if str(request.sid) in send_key:
        del send_key[str(request.sid)]
        print("伺服器 : 來源", str(request.sid), '斷開連線，刪除該金鑰。')
    if str(request.sid) in sid_Y:
        del sid_Y[str(request.sid)]
        print("伺服器 : 來源", str(request.sid), '斷開連線，刪除該金鑰。')


# 主程式
if __name__ == '__main__':

    print("SYS_Chaos主端 初始化中...", end="\r")
    sys_chaos = threading.Thread(target=chaos)
    sys_chaos.setDaemon(True)
    sys_chaos.start()
    print("SYS_Chaos主端 初始化完成!")

    try:
        print("運行成功，等待連接...")
        port = int(os.environ.get('PORT', 8080))
        socketio.run(app, host='0.0.0.0', port=port)

    except:
        print("伺服器退出")