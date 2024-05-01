import os
import toml

class ApplicationConf:
    def __init__(self, workdir, filename):
        self.WORKDIR = workdir
        self._load_config(filename)

    def _load_config(self, filename):
        config_path = os.path.join(self.WORKDIR, filename)
        if not os.path.exists(config_path):
            raise FileNotFoundError(f"Конфигурационный файл {filename} не найден в {self.WORKDIR}")

        with open(config_path, 'r') as config_file:
            conf = toml.load(config_file)

        self.FLASK_LISTEN_IP = conf['FLASK_LISTEN_IP']
        self.FLASK_LISTEN_PORT = conf['FLASK_LISTEN_PORT']
        self.PROXY_SERVER_BASE_URL = conf['PROXY_SERVER_BASE_URL']
        self.REMOTE_INDEX_SIMPLE = conf['REMOTE_INDEX_SIMPLE']
        self.REMOTE_INDEX_JSON = conf['REMOTE_INDEX_JSON']
        self.CONNECTION_TIMEOUT = conf['CONNECTION_TIMEOUT']
        self.DOWNLOAD_TIMEOUT = conf['DOWNLOAD_TIMEOUT']
        self.MAX_RETRIES = conf['MAX_RETRIES']

        self.LOG_FILE_PATH = os.path.normpath(os.path.join(self.WORKDIR, "messages.log"))
        self.DB_FILE_PATH = os.path.normpath(os.path.join(self.WORKDIR, "remote_index.sqlite"))
        self.CACHE_DIR = os.path.normpath(os.path.join(self.WORKDIR, "cache"))

# Пример использования:
# conf = ApplicationConf('/path/to/workdir', 'config.toml')
# print(conf.FLASK_LISTEN_IP)
