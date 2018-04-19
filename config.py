from redis import StrictRedis
import logging


class Config(object):
    SECRET_KEY = 'Q9zeIxdeJlnHj0tdohhK42Iq3I1arhbDRysgnfQfhxR5irg1qqlEurEBeFtCWAJp'
    SQLALCHEMY_DATABASE_URI = 'mysql://root:a@127.0.0.1:3306/information27'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    REDIS_HOST = '127.0.0.1'
    REDIS_PORT = 6379
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_TYPE = 'redis'
    SESSION_USE_SINGED = True
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 86400 * 2


class DevelopmentConfig(Config):
    DEBUG = True
    LOG_LEVEL = logging.DEBUG


class ProductionConfig(Config):
    DEBUG = False
    LOG_LEVEL = logging.ERROR


class TestingConfig(Config):
    DEBUG = True
    LOG_LEVEL = logging.DEBUG


config = {
    "development": DevelopmentConfig,
    "production": ProductionConfig,
    "testing": TestingConfig
}





