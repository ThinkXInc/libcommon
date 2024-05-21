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

# Logger
from libcommon.logger import Logger
logger = Logger()
logger.setLevel(logger.INFO)
from libcommon.color import *

# Config
from config import Config, check_config
REQUIRED_KEYS_IN_CONFIG = [
    'PASSWORD_ENCRYPT_KEY',
]
check_config(Config, REQUIRED_KEYS_IN_CONFIG)

ENCRYPT_KEY = Config.PASSWORD_ENCRYPT_KEY.encode('utf-8')

class Cipher:
    bs = 32
    key = (hashlib.md5(ENCRYPT_KEY).hexdigest()).encode('utf-8')

    @classmethod
    def encrypt(cls, raw):
        logger.debug("Starting encryption process.")
        iv = Random.get_random_bytes(AES.block_size)
        cipher = AES.new(cls.key, AES.MODE_CBC, iv)
        data = Padding.pad(raw.encode('utf-8'), AES.block_size, 'pkcs7')
        encrypted_data = iv + cipher.encrypt(data)
        encoded_encrypted_data = base64.b64encode(encrypted_data).decode('utf-8')
        logger.debug(f"Raw data: {raw}")
        logger.debug(f"Encrypted data: {encoded_encrypted_data}")
        return encoded_encrypted_data

    @classmethod
    def decrypt(cls, enc):
        logger.debug("Starting decryption process.")
        try:
            decoded_enc = base64.b64decode(enc)  # Decode the base64 string to bytes
            iv = decoded_enc[:AES.block_size]
            cipher = AES.new(cls.key, AES.MODE_CBC, iv)
            decrypted_data = cipher.decrypt(decoded_enc[AES.block_size:])
            plain_text = Padding.unpad(decrypted_data, AES.block_size, 'pkcs7').decode('utf-8')
            logger.debug(f"Decrypted text: {plain_text}")
            return plain_text
        except Exception as e:
            logger.error("Decryption failed", exc_info=True)
            raise e

    @classmethod
    def compare(cls, plaintext, encrypted):
        logger.debug("Comparing plaintext with decrypted text.")
        decrypted_text = cls.decrypt(encrypted)
        result = plaintext == decrypted_text
        logger.debug(f"Plaintext: {plaintext}, Decrypted text: {decrypted_text}, Comparison result: {result}")
        return result