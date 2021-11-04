#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# tools/cipher.py
#
# AES with CBC mode, ignored size = 32
#
# basic usage
#
# requirement: set ENCRYPT_KEY environment variable to whatever the key you use for encryption
#
# cipher = Cipher()
#
# encryption:
# enc_password = cipher.encrypt(raw_password)
#
# decryption:
# password = cipher.decrypt(enc_password)
#

from Crypto import Random
from Crypto.Cipher import AES
from Crypto.Util import Padding
import hashlib
import base64
from general.config import Config


class Cipher:
    def __init__(self):
        self.bs = 32
        self.key = (hashlib.md5(Config.ENCRYPT_KEY.encode('utf-8')).hexdigest()).encode('utf-8')

    def encrypt(self, raw):
        iv = Random.get_random_bytes(AES.block_size)
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        data = Padding.pad(raw.encode('utf-8'), AES.block_size, 'pkcs7')
        return base64.b64encode(iv + cipher.encrypt(data))

    def decrypt(self, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(self.key, AES.MODE_CBC, iv)
        data = Padding.unpad(cipher.decrypt(enc[AES.block_size:]), AES.block_size, 'pkcs7')
        return data.decode('utf-8')

    def iscorresponded(self, plaintext, encrypted):
        if plaintext == self.decrypt(encrypted):
            return True
        else:
            return False
