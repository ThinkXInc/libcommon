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

# Config
from config import Config, check_config
REQUIRED_KEYS_IN_CONFIG = [
    'ENCRYPT_KEY',
]
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

ENCRYPT_KEY = Config.ENCRYPT_KEY.encode('utf-8')

class Cipher:
    bs = 32
    key = (hashlib.md5(ENCRYPT_KEY).hexdigest()).encode('utf-8')

    @classmethod
    def encrypt(cls, raw):
        iv = Random.get_random_bytes(AES.block_size)
        cipher = AES.new(cls.key, AES.MODE_CBC, iv)
        data = Padding.pad(raw.encode('utf-8'), AES.block_size, 'pkcs7')
        return base64.b64encode(iv + cipher.encrypt(data))

    @classmethod
    def decrypt(cls, enc):
        enc = base64.b64decode(enc)
        iv = enc[:AES.block_size]
        cipher = AES.new(cls.key, AES.MODE_CBC, iv)
        data = Padding.unpad(cls.decrypt(enc[AES.block_size:]), AES.block_size, 'pkcs7')
        return data.decode('utf-8')

    @classmethod
    def compare(cls, plaintext, encrypted):
        if plaintext == cls.decrypt(encrypted):
            return True
        else:
            return False