#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# tools/mail.py
#
# Amazon SES wrapper adapted for configurable instances with error handling and usage example
#
# Usage:
#     mail = Mail(ses_region=Config.SES_AWS_REGION)
#     mail.send(
#         sender=Config.SENDER,
#         reply_to=Config.REPLY_TO,
#         recipient=user.email,
#         subject='How are you doing?',
#         text="Hello, this is a text email.",
#         html="<h1>Hello, this is an HTML email.</h1>"
#     )

import boto3

from libcommon.logger import Logger
logger = Logger('Mail')
logger.setLevel(logger.DEBUG)
from libcommon.color import *

class MailSendError(Exception):
    pass

class Mail:
    def __init__(
        self,
        aws_access_key_id: str,
        aws_secret_access_key: str,
        region_name: str,
        charset="UTF-8"):
        """
        Initialize Mail class with specific SES region and charset.

        Args:
            ses_region (str): AWS region for the SES service.
            charset (str): Charset for the email encoding.

        Raises:
            Exception: If the SES client initialization fails.
        """
        self.charset = charset
        try:
            logger.info(f'Mail client initialize with\nAWS_ACCESS_KEY_ID:{aws_access_key_id} SES_REGION:{region_name}')
            self.client = boto3.client(
                'ses',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=region_name)
        except Exception as e:
            logger.error(red(f"Failed to initialize SES client: {e}"))
            raise Exception(f"Failed to initialize SES client: {e}")

    def send(self, sender, reply_to, recipient, subject, text, html, bcc=None):
        """
        Send an email using the provided parameters.

        Args:
            sender (str): The email address of the sender.
            reply_to (str): The reply-to email address.
            recipient (str): The recipient's email address.
            subject (str): The subject of the email.
            text (str): The plain text version of the email.
            html (str): The HTML version of the email.
            bcc (list, optional): List of email addresses for Bcc. Defaults to None.


        Returns:
            dict: The response from the AWS SES service.

        Raises:
            MailSendError: If the email cannot be sent.
        """
        try:
            destination = {
                'ToAddresses': [recipient],
            }
            if bcc:
                destination['BccAddresses'] = bcc

            response = self.client.send_email(
                Destination=destination,
                Message={
                    'Body': {
                        'Html': {
                            'Charset': self.charset,
                            'Data': html,
                        },
                        'Text': {
                            'Charset': self.charset,
                            'Data': text,
                        },
                    },
                    'Subject': {
                        'Charset': self.charset,
                        'Data': subject,
                    },
                },
                Source=sender,
                ReplyToAddresses=[reply_to]
            )
            return response
        except Exception as e:
            logger.error(red(f"Failed to send email: {e}"))
            raise MailSendError(f"Failed to send email: {e}")
