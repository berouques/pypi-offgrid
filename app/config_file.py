import os
import toml

class ConfigFile:
    def __init__(self, directory, filename):
        self.directory = directory
        self.filename = filename
        self.filepath = os.path.join(directory, filename)

        # Проверка существования директории
        if not os.path.isdir(directory):
            raise FileNotFoundError(f"Директория {directory} не найдена.")

    def get_config(self):
        # Проверка существования файла
        if not os.path.isfile(self.filepath):
            raise FileNotFoundError(f"Файл {self.filename} не найден в директории {self.directory}.")

        # Чтение файла конфигурации
        with open(self.filepath, 'r') as config_file:
            config_data = toml.load(config_file)
        return config_data

    def create_default_config(self):
        # Создание файла с дефолтным содержимым
        default_config = {
            'LISTEN_IP': '0.0.0.0',
            'LISTEN_PORT': 2222,
            'REMOTE_SIMPLE_INDEX_URL': 'https://pypi.org/simple/%s',
            'INDEX_SEARCH_TIMEOUT': 20,
            'PROXY_SERVER_URL': 'http://127.0.0.1:2222'
        }

        try:
            with open(self.filepath, 'w') as config_file:
                toml.dump(default_config, config_file)
        except Exception as e:
            raise IOError(f"Не удалось создать файл конфигурации: {e}")

    def check_config(self):
            # Ожидаемые ключи конфигурации
            expected_keys = [
                'FLASK_LISTEN_IP',
                'FLASK_LISTEN_PORT',
                'REMOTE_INDEX_SIMPLE',
                'REMOTE_INDEX_JSON',
                'CONNECTION_TIMEOUT',
                'DOWNLOAD_TIMEOUT',
                'MAX_RETRIES'
            ]

            # Получение текущей конфигурации
            config_data = self.get_config()

            # Проверка наличия всех необходимых ключей
            for key in expected_keys:
                if key not in config_data:
                    raise KeyError(f"Отсутствует обязательный ключ конфигурации: {key}")



# Пример использования:
# config = ConfigFile('/path/to/directory', 'config.toml')
# config_data = config.get_config()
# config.create_default_config()
