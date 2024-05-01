# __init__.py
from flask import Flask
import logging
import werkzeug

def create_app():
    
    app = Flask(__name__)
    app.logger.propagate = True

    # режим отладки с перезагрузкой приложухи если изменены файлы проекта       
    app.debug = True
       
       
    app.register_blueprint(main)
    return app
