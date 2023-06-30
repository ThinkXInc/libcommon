#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# tools/mail.py
#
# Amazon SES wrapper
#
# Basic usage:
#
# Mail.send_mail(
#     subject='How are you doing?',
#     text=MailTemplateClass.template(user, host_url, reset_code),
#     html=None,  # set if you send html mails
#     recipient_email=user.email)


import boto3
import logging
from re import sub
from general.config import Config


class Mail():
    __charset__ = "UTF-8"
    __ses_region__ = Config.SES_AWS_REGION
    __sender__ = Config.MAIL_SENDER
    __reply_to_addresses__ = Config.REPLY_TO_ADDRESSES

    def __init__(self):
        pass

    @classmethod
    def _client(cls):
        """This method is used by other method in this class.

        returns:
            - boto3 client object
        """
        return boto3.client('ses', region_name=cls.__ses_region__)

    @classmethod
    def send_mail(cls, subject, text, html, recipient_email):
        """Wrapper of boto3 client

        usage:
            send_mail(
                subject='How are you doing?',
                text=PasswordReminderMail.template(user_name, user_email, host_url, reset_code, expiration_day),
                html="",  # set if you send html mails
                recipient_email=user.email
            )

        args:
            - subject: str
            - text: str
            - html: str
            - recipient_email: str
        returns:
            - response:
        """
        client = cls._client()
        response = client.send_email(
            Destination={
                'ToAddresses': [
                    recipient_email,
                ],
            },
            Message={
                'Body': {
                    'Html': {
                        'Charset': cls.__charset__,
                        'Data': html,
                    },
                    'Text': {
                        'Charset': cls.__charset__,
                        'Data': text,
                    },
                },
                'Subject': {
                    'Charset': cls.__charset__,
                    'Data': subject,
                },
            },
            Source=cls.__sender__,
            ReplyToAddresses=cls.__reply_to_addresses__
        )
        return response