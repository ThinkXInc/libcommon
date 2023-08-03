#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# api/responses/api_successes.py
#
#

from libcommon.response.api_response import SuccessCode, APISuccess

class OK(APISuccess):
    __http_success__ = SuccessCode.OK

    def __init__(self, message):
        self.__saved_data__ = None
        self.__message__ = message


class CREATED(APISuccess):
    __http_success__ = SuccessCode.CREATED

    def __init__(self, saved_data, message):
        self.__saved_data__ = saved_data
        self.__message__ = message

