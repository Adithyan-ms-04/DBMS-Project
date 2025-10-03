import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or 'localhost'
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'fprms_user'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'fprms_pass'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'fprms'
    
class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}