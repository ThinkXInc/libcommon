#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# tools/session.py
#
# This subclass replaces the flask session_interface.
#
# - Flask SessionInterface
# (http://flask.pocoo.org/docs/0.10/api/#session-interface)
#
# Session values are stored into redis db.
#
# - set up
# app = Flask(__name__)
# app.session_interface = RedisSessionInterface()
#
# - save, get id, clear, count
# Session.start(_id)
# Session.user_id()
# Session.clear()
# Session.count(_id)
#


import logging
import pickle
from datetime import timedelta
from uuid import uuid4

import redis
from flask import session
from flask.sessions import SessionInterface, SessionMixin
from redis import StrictRedis, Redis
from werkzeug.datastructures import CallbackDict

from general.config import Config


class RedisSession(CallbackDict, SessionMixin):
    def __init__(self, initial=None, sid=None, new=False):
        def on_update(self):
            self.modified = True

        CallbackDict.__init__(self, initial, on_update)
        self.sid = sid
        self.new = new
        self.modified = False


class RedisSessionInterface(SessionInterface):
    serializer = pickle
    session_class = RedisSession

    pool = redis.ConnectionPool(
        host=Config.REDIS_HOST_SESSION,
        port=Config.REDIS_PORT_SESSION,
        db=Config.REDIS_DB_NUMBER_SESSION
    )
    __redis = Redis(connection_pool=pool)

    def __init__(self, prefix='session:'):
        self.prefix = prefix

    def generate_session_id(self):
        """Generate session id
        Return an unique session id.
        """
        return str(uuid4())

    def get_redis_expiration_time(self, app, session):
        """Return redis expiration time.
        """
        if session.permanent:
            return app.permanent_session_lifetime
        return timedelta(days=Config.REDIS_SESSION_EXPIRATION_PERIOD)

    def open_session(self, app, request):
        """Overrides SessionInterface.open_session()
        Get session_id from cookie.
        If no session_id is found in cookie,
        return new session object with generated id.
        If session_id is found,
        return the session object with saved data in redis.
        """
        session_id = request.cookies.get(app.session_cookie_name)
        if not session_id:
            session_id = self.generate_session_id()
            return self.session_class(sid=session_id, new=True)
        val = self.__redis.get(self.prefix + session_id)
        if val is not None:
            data = self.serializer.loads(val)
            return self.session_class(data, sid=session_id)

        return self.session_class(sid=session_id, new=True)

    def save_session(self, app, session, response):
        """Overrides SessionInterface.save_session()
        ------------------------------------------------
        | session:{sid}
        | session:{sid}
        | session:{sid}
        ------------------------------------------------
        """
        domain = self.get_cookie_domain(app)
        if not session:
            self.__redis.delete(self.prefix + session.sid)
            if session.modified:
                response.delete_cookie(app.session_cookie_name,
                                       domain=domain)
            return
        redis_exp = self.get_redis_expiration_time(app, session)
        cookie_exp = self.get_expiration_time(app, session)
        val = self.serializer.dumps(dict(session))
        self.__redis.setex(self.prefix + session.sid,
                           int(redis_exp.total_seconds()),
                           val)
        response.set_cookie(app.session_cookie_name, session.sid,
                            expires=cookie_exp, httponly=True,
                            domain=domain)


class Session:
    SESSION_PREFIX = 'session:'
    SESSIONS_PREFIX = 'sessions:'

    pool = redis.ConnectionPool(
        host=Config.REDIS_HOST_SESSION,
        port=Config.REDIS_PORT_SESSION,
        db=Config.REDIS_DB_NUMBER_SESSION
    )
    __redis = StrictRedis(connection_pool=pool)

    def __init__(self):
        pass

    # @classmethod
    # def _client(cls):
    #     _client = StrictRedis(
    #         host=Config.REDIS_HOST_SESSION,
    #         port=Config.REDIS_PORT_SESSION,
    #         db=Config.REDIS_DB_NUMBER_SESSION)
    #     return _client

    @staticmethod
    def user_id():
        """Get user_id from session.
        If no session, return None.
        """
        return session.get('user_id')

    @staticmethod
    def exists_user_session():
        """Return if session exists.
        """
        return 'user_id' in session

    @staticmethod
    def start_user_session(user_id: int) -> None:
        """Save user session.
        -SET sessions:{user_id} ----------------------------
        | 6b48dfa3-83b5-4a05-bb31-08eddb701984 (sid)
        | 428d897d-19ae-4881-a086-df625957c5db (sid)
        | 2a7356cb-8a41-47e3-b165-40690cac740c (sid)
        ----------------------------------------------------
        args:
            user : User
        """

        # redisにsessionがない場合なりすまし防止の為にcookieから取得したsessionを使用せずに再生成する
        Session.clear()
        session.sid = str(uuid4())
        print(session)
        session['user_id'] = user_id

        sessions_key = '{}{}'.format(
            Session.SESSIONS_PREFIX, user_id)
        print(sessions_key)
        print(session.sid)
        Session.__redis.sadd(sessions_key, session.sid)

    @staticmethod
    def clear_user_session() -> None:
        """Clear session.
        """
        Session.__redis.delete(Session.SESSIONS_PREFIX + str(Session.user_id()))
        Session.__redis.delete(Session.SESSION_PREFIX + session.sid)
        session.clear()

    @staticmethod
    def user_access_count(user_id: int) -> int:
        """get access count
        args:
            user_id : int  # User._id
        Returns:
            count: int  # access count
        """
        logging.debug('count sessions for user_id:{}'.format(user_id))

        sessions_key = '{}{}'.format(
            Session.SESSIONS_PREFIX, user_id)
        user_sids = Session.__redis.smembers(sessions_key)

        # count session in redis
        if len(user_sids) == 0:
            # no session found
            logging.debug('no session found')
            return 0
        else:
            logging.debug('session found')
            sids = set()
            for user_sid in user_sids:
                user_sid = user_sid.decode()
                # if session:{sid} in session, count it
                if Session.__redis.exists(Session.SESSION_PREFIX +
                                                  user_sid):
                    sids.add(user_sid)
                else:
                    # if session:{sid} doesn't exist,
                    # remove the sid from sessions:
                    Session.__redis.srem(
                        sessions_key,
                        user_sid)

            count = len(sids)
            logging.debug(
                '{} session found for user {}'.format(count, user_id))
            return count

    @staticmethod
    def organization_member_id():
        """Get organization_member_id from session.
        If no session, return None.
        """
        return session.get('organization_member_id')

    @staticmethod
    def exists_organization_session():
        """Return if session exists.
        """
        return 'organization_member_id' in session

    @staticmethod
    def start_organization_session(organization_member_id: int) -> None:
        """Save organization session.
        -SET sessions:{organization_member_id} -------------
        | 6b48dfa3-83b5-4a05-bb31-08eddb701984 (sid)
        | 428d897d-19ae-4881-a086-df625957c5db (sid)
        | 2a7356cb-8a41-47e3-b165-40690cac740c (sid)
        ----------------------------------------------------
        args:
            organization_member : OrganizationMember
        """

        # redisにsessionがない場合なりすまし防止の為にcookieから取得したsessionを使用せずに再生成する
        Session.clear_organization_session()
        session.sid = str(uuid4())
        print(session)
        session['organization_member_id'] = organization_member_id

        sessions_key = '{}{}'.format(
            Session.SESSIONS_PREFIX, organization_member_id)
        print(sessions_key)
        print(session.sid)
        Session.__redis.sadd(sessions_key, session.sid)

    @staticmethod
    def clear_organization_session() -> None:
        """Clear organization session.
        """
        Session.__redis.delete(Session.SESSIONS_PREFIX + str(Session.organization_member_id()))
        Session.__redis.delete(Session.SESSION_PREFIX + session.sid)
        session.clear()

    @staticmethod
    def organization_access_count(organization_member_id: int) -> int:
        """get access count
        args:
            organization_member_id : int  # OrganizationMember.organization_member_id
        Returns:
            count: int  # access count
        """
        logging.debug('count sessions for user_id:{}'.format(organization_member_id))

        sessions_key = '{}{}'.format(
            Session.SESSIONS_PREFIX, organization_member_id)
        user_sids = Session.__redis.smembers(sessions_key)

        # count session in redis
        if len(user_sids) == 0:
            # no session found
            logging.debug('no session found')
            return 0
        else:
            logging.debug('session found')
            sids = set()
            for user_sid in user_sids:
                user_sid = user_sid.decode()
                # if session:{sid} in session, count it
                if Session.__redis.exists(Session.SESSION_PREFIX +
                                                  user_sid):
                    sids.add(user_sid)
                else:
                    # if session:{sid} doesn't exist,
                    # remove the sid from sessions:
                    Session.__redis.srem(
                        sessions_key,
                        user_sid)

            count = len(sids)
            logging.debug(
                '{} session found for user {}'.format(count, organization_member_id))
            return count        
