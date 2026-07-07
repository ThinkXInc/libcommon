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
from typing import Optional
from uuid import uuid4
import redis
from flask import session
from flask.sessions import SessionInterface, SessionMixin
from redis import StrictRedis, Redis
from werkzeug.datastructures import CallbackDict

# logger
from libcommon.logger import Logger
from libcommon.color import *

logger = Logger()
logger.setLevel(logger.DEBUG)


class RedisSession(CallbackDict, SessionMixin):
    def __init__(self, initial=None, sid=None, new=False):
        super().__init__(initial)
        self.modified = False
        self.sid = sid
        self.new = new

    def on_update(self):
        self.modified = True

class RedisSessionInterface(SessionInterface):
    def __init__(self, host: str, port: int, db: int, expiration_time_sec: int, prefix='session:'):
        self.prefix = prefix
        self.expiration_time_sec = expiration_time_sec

        self.serializer = msgpack
        self.session_class = RedisSession

        logger.info(magenta('Initializing Redis for session...'))
        self.pool = redis.ConnectionPool(host=host, port=port, db=db)
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
        return timedelta(seconds=self.expiration_time_sec)

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
    """ログイン済みユーザーのローカルセッション(Redis 実体)。

    ThinkX Auth Protocol §2 手順6 の「ローカルセッションを開始」がこのクラスを指す。

    Redis のキー体系(逆引き):
      - ``session:{sid}``        → セッション本体(RedisSessionInterface が保存)
      - ``sessions:{user_id}``   → その user_id が持つ sid の集合(**逆引き**。多端末の
                                    同時セッション数カウント = ``count()`` に使う)
      - ``user_id:{sid}``        → sid から user_id への逆引きマップ
    user_id は MongoDB ObjectId の **str**(コーディングガイドが ``str(user.id)`` を指示。F-2)。
    """

    SESSION_PREFIX = 'session:'      # session:{sid} -> セッション本体
    SESSIONS_PREFIX = 'sessions:'    # sessions:{user_id} -> sid 集合(逆引き・多端末カウント用)
    SESSION_KEY = 'user_id'
    # N-7: start() が書く session:{sid} プレースホルダ本体の TTL(秒)。save_session が
    # 応答時に本体で上書きするまでの橋渡し。上書きが起きない経路でも漏れないよう TTL を付ける。
    PLACEHOLDER_TTL_SEC = 3600

    _redis = None

    @classmethod
    def configure(cls, host: str, port: int, db: int) -> None:
        pool = redis.ConnectionPool(host=host, port=port, db=db)
        cls._redis = StrictRedis(connection_pool=pool)

    @classmethod
    def _r(cls):
        if cls._redis is None:
            raise RuntimeError('Session.configure() must be called at app startup')
        return cls._redis

    @classmethod
    def user_id(cls) -> Optional[str]:
        """Get user_id from session.
        """
        user_id = session.get(cls.SESSION_KEY)
        if user_id:
            logger.debug(cyan(f"User ID retrieved from session: {user_id}"))
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
    def start(cls, user_id: str) -> None:
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
            cls._r().sadd(sessions_key, session.sid)
            cls._r().set(f"user_id:{session.sid}", user_id)  # Store reverse mapping
            # N-7: count() が start 直後の live セッションを反映できるよう、session:{sid} 本体を
            # TTL 付きプレースホルダ(空値)で先行作成する。save_session が応答時に本体で上書きする。
            cls._r().setex(f'{cls.SESSION_PREFIX}{session.sid}', cls.PLACEHOLDER_TTL_SEC, '')
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
                Session._r().delete(sessions_key)
                Session._r().delete(Session.SESSION_PREFIX + session.sid)
                Session._r().delete(f"user_id:{session.sid}")
                session.clear()
                logger.info(light_green(f"Session cleared for user {user_id}."))
            except redis.RedisError as e:
                logger.error(red(f"Error clearing session for user {user_id}: {e}"))

    @classmethod
    def count(cls, user_id: str) -> int:
        """get access count
        args:
            user_id : int  # User._id
        Returns:
            count: int  # access count
        """
        logger.debug('count sessions for {}:{}'.format(cls.SESSION_KEY, user_id))

        sessions_key = f'{cls.SESSIONS_PREFIX}{user_id}'
        try:
            user_sids = cls._r().smembers(sessions_key)
            count = 0
            for user_sid in user_sids:
                user_sid = user_sid.decode()
                if cls._r().exists(cls.SESSION_PREFIX + user_sid):
                    count += 1
                else:
                    cls._r().srem(sessions_key, user_sid)
            logger.info(bold(f"Active session count for user {user_id}: {count}"))
            return count
        except redis.RedisError as e:
            logger.error(f"Error counting sessions for user {user_id}: {e}")
            return 0

    @classmethod
    def get_user_id_from_session_id(cls, session_id: str) -> Optional[str]:
        """Retrieve user ID from a given session ID.

        Args:
            session_id (str): The session ID to query the user ID from.

        Returns:
            user_id (str): The user ID associated with the session or None if not found.
        """
        user_session_key = f'user_id:{session_id}'
        try:
            user_id = cls._r().get(user_session_key)
            if user_id is not None:
                user_id = user_id.decode('utf-8')  # Properly decode from bytes to string
                logger.info(f"User ID '{user_id}' retrieved from session ID '{session_id}'.")
                return user_id
            else:
                logger.debug(f"No user ID found for session ID '{session_id}'.")
                return None
        except redis.RedisError as e:
            logger.error(f"Error retrieving user ID from session ID '{session_id}': {e}")
            return None
