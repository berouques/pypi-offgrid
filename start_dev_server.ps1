# start_dev_server.ps1

$ProjectDir = $PSScriptRoot

# Путь к рабочему каталогу
$WorkDir = Join-Path $ProjectDir "workdir"
new-item -ItemType Directory -force $WorkDir -ErrorAction Stop

# Путь к виртуальному окружению
$VenvPath = join-path $ProjectDir "venv"

# Проверяем, существует ли активатор виртуального окружения
if (-Not (Test-Path "$VenvPath\Scripts\Activate.ps1")) {
    # Создаем виртуальное окружение, если оно не существует
    python -m venv $VenvPath

    # Активируем виртуальное окружение
    & "$VenvPath\Scripts\Activate.ps1"

    # Устанавливаем зависимости из файла requirements.txt
    pip install -r requirements.txt
} else {
    # Активируем виртуальное окружение
    & "$VenvPath\Scripts\Activate.ps1"
}

# Запускаем приложение
python .\app\pypi-offgrid.py run $WorkDir
