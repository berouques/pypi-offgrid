#!/bin/bash

# start_dev_server.ps1

# Путь к рабочему каталогу
WorkDir="/data/pypi-offgrid-workdir"

# Путь к виртуальному окружению
VenvPath="./venv"

# Проверяем, существует ли активатор виртуального окружения
if [ ! -f "$VenvPath/bin/activate" ]; then
    # Создаем виртуальное окружение, если оно не существует
    python -m venv $VenvPath

    # Активируем виртуальное окружение
    source "$VenvPath/bin/activate"

    # Устанавливаем зависимости из файла requirements.txt
    pip install -r requirements.txt
else
    # Активируем виртуальное окружение
    source "$VenvPath/bin/activate"
fi

# Запускаем приложение
python ./app/pypi-offgrid.py run $WorkDir
