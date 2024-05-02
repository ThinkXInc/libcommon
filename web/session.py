#!/usr/local/bin/python
# -*- coding:utf-8 -*-
#
# session.py
#
# This subclass replaces the flask session_interface.
#
# - Flask SessionInterface
# (http://flask.pocoo.org/docs/0.10/api/#session-interface)
#
# This gives you more flexibility, 
# like maybe you want to use the same redis.Redis instance for cache purpose too, 
# then you do not need to keep two redis.Redis instance in the same process.
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
import msgpack
from datetime import timedelta
from uuid import uuid4
import redis
from flask import session
from flask.sessions import SessionInterface, SessionMixin
from redis import StrictRedis, Redis
from werkzeug.datastructures import CallbackDict

from config import Config, check_config

# logger
from libcommon.logger import Logger
from libcommon.color import *

logger = Logger()
logger.setLevel(logger.DEBUG)


REDIS_SESSION_REQUIRED_KEYS = [
    'REDIS_SESSION_HOST',
    'REDIS_SESSION_PORT',
    'REDIS_SESSION_DB_NUMBER',
    'REDIS_SESSION_EXPIRATION_PERIOD'
]

# Check if all keys and values are satisfied
check_config(Config, REDIS_SESSION_REQUIRED_KEYS)

class RedisSession(CallbackDict, SessionMixin):
    def __init__(self, initial=None, sid=None, new=False):
        super().__init__(initial)
        self.modified = False
        self.sid = sid
        self.new = new

    def on_update(self):
        self.modified = True

class RedisSessionInterface(SessionInterface):
    def __init__(self, prefix='session:'):
        self.prefix = prefix

        self.serializer = msgpack
        self.session_class = RedisSession

        logger.info(magenta('Initializing Redis for session...'))
        self.pool = redis.ConnectionPool(
            host=Config.REDIS_SESSION_HOST,
            port=Config.REDIS_SESSION_PORT,
            db=Config.REDIS_SESSION_DB_NUMBER
        )
        self.__redis = Redis(connection_pool=self.pool)

        # Check if Redis is running by executing a simple command
        try:
            self.__redis.ping()
            logger.info(green("Successfully connected to Redis."))
        except (redis.ConnectionError, redis.TimeoutError) as e:
            logger.error(red("Failed to connect to Redis: {}".format(e)))

    def generate_session_id(self):
        """Generate session id
        Return an unique session id.
        """
        while True:
            session_id = str(uuid4())
            if not self.__redis.exists(self.prefix + session_id):
                break
        return session_id

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
        if self.serializer is None:
            logger.warning(f'[WARNING] No serializer found in RedisSessionInterface.')
            return None
        session_cookie_name = app.config.get('SESSION_COOKIE_NAME')
        session_id = request.cookies.get(session_cookie_name)
        if not session_id:
            session_id = self.generate_session_id()
            return self.session_class(sid=session_id, new=True)
        try:
            val = self.__redis.get(self.prefix + session_id)
            if val is not None:
                data = self.serializer.loads(val, raw=False)
                return self.session_class(data, sid=session_id)
        except redis.RedisError as e:
            logger.error(red(f'Failed to open session: {e}'))
            raise

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
            try:
                self.__redis.delete(self.prefix + session.sid)
            except redis.RedisError as e:
                logger.error(red(f'Failed to delete session: {e}'))
                raise
            if session.modified:
                logger.debug("Session modified and empty, deleting session cookie.")
                response.delete_cookie(app.session_cookie_name,
                                       domain=domain)
            return

        cookie_exp = self.get_expiration_time(app, session)
        redis_exp = self.get_redis_expiration_time(app, session)
        session_cookie_name = app.config.get('SESSION_COOKIE_NAME', 'session')

        try:
            val = self.serializer.dumps(dict(session), use_bin_type=True)
            self.__redis.setex(self.prefix + session.sid,
                               int(redis_exp.total_seconds()),
                               val)
            logger.info(cyan(f"Session {session.sid} saved to Redis."))
        except redis.RedisError as e:
            logger.error(red(f'Failed to save session: {e}'))
            raise

        response.set_cookie(session_cookie_name, session.sid,
                            expires=cookie_exp, httponly=True,
                            domain=domain)

class Session:
    SESSION_PREFIX = 'session:'
    SESSIONS_PREFIX = 'sessions:'
    SESSION_KEY = 'user_id'

    # Define __redis as a class attribute
    redis_pool = redis.ConnectionPool(
        host=Config.REDIS_SESSION_HOST,
        port=Config.REDIS_SESSION_PORT,
        db=Config.REDIS_SESSION_DB_NUMBER
    )
    __redis = StrictRedis(connection_pool=redis_pool)

    @classmethod
    def user_id(cls) -> int:
        """Get user_id from session.
        """
        user_id = session.get(cls.SESSION_KEY)
        if user_id:
            logger.debug(f"User ID retrieved from session: {user_id}")
        else:
            logger.debug("No user ID found in session.")
        return user_id

    @classmethod
    def exists_session(cls):
        """Check if a user session exists."""
        exists = cls.SESSION_KEY in session
        logger.debug(f"Session exists: {exists}")
        return exists

    @classmethod
    def start(cls, user_id: int) -> None:
        """Save user session.

        Allow a single user to have multiple simultaneous sessions.

        -SET sessions:{user_id} ----------------------------
        | 6b48dfa3-83b5-4a05-bb31-08eddb701984 (sid)
        | 428d897d-19ae-4881-a086-df625957c5db (sid)
        | 2a7356cb-8a41-47e3-b165-40690cac740c (sid)
        ----------------------------------------------------

        args:
            - user_id (int) : 
        """
        try:
            # redisにsessionがない場合なりすまし防止の為にcookieから取得したsessionを使用せずに再生成する
            cls.clear()  # Clear any existing session data first
            session[cls.SESSION_KEY] = user_id
            session.sid = str(uuid4())
            sessions_key = f'{cls.SESSIONS_PREFIX}{user_id}'
            cls.__redis.sadd(sessions_key, session.sid)
            cls.__redis.set(f"user_id:{session_id}", user_id)  # Store reverse mapping
            logger.info(cyan(f"Session started for user {user_id} with session ID {session.sid}."))
        except redis.RedisError as e:
            logger.error(red(f"Error starting session for user {user_id}: {e}"))

    @staticmethod
    def clear() -> None:
        """Clear the current session data from Redis."""
        user_id = Session.user_id()
        if user_id:
            try:
                sessions_key = f'{Session.SESSIONS_PREFIX}{user_id}'
                Session.__redis.delete(sessions_key)
                Session.__redis.delete(Session.SESSION_PREFIX + session.sid)
                Session.__redis.delete(f"user_id:{session.sid}")
                session.clear()
                logger.info(light_green(f"Session cleared for user {user_id}."))
            except redis.RedisError as e:
                logger.error(red(f"Error clearing session for user {user_id}: {e}"))

    @classmethod
    def count(cls, user_id: int) -> int:
        """get access count
        args:
            user_id : int  # User._id
        Returns:
            count: int  # access count
        """
        logger.debug('count sessions for {}:{}'.format(cls.SESSION_KEY, user_id))

        sessions_key = f'{cls.SESSIONS_PREFIX}{user_id}'
        try:
            user_sids = cls.__redis.smembers(sessions_key)
            count = 0
            for user_sid in user_sids:
                user_sid = user_sid.decode()
                if cls.__redis.exists(cls.SESSION_PREFIX + user_sid):
                    count += 1
                else:
                    cls.__redis.srem(sessions_key, user_sid)
            logger.info(bold(f"Active session count for user {user_id}: {count}"))
            return count
        except redis.RedisError as e:
            logger.error(f"Error counting sessions for user {user_id}: {e}")
            return 0

    @classmethod
    def get_user_id_from_session_id(cls, session_id: str) -> int:
        """Retrieve user ID using session ID from Redis."""
        reverse_session_key = f'user_id:{session_id}'
        try:
            user_id = cls.__redis.get(reverse_session_key)
            if user_id is not None:
                user_id = int(user_id.decode('utf-8'))
                logger.info(f"User ID {user_id} retrieved from session ID {session_id}.")
                return user_id
            else:
                logger.debug(f"No user ID found for session ID {session_id}.")
                return None
        except redis.RedisError as e:
            logger.error(f"Error retrieving user ID from session ID {session_id}: {e}")
            return None
