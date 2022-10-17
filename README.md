# rlibs2sigs

Плагин для IDA / Cutter / Rizin. Создает сигнатуры для собранных бинарных файлов на Rust на основе строк, содержащих названия и версии используемых библиотек

## Подготовка

Для использования с IDA:

```bash
pip install -r requirements-ida.txt
```

Для использования с Rizin / Cutter:

```bash
pip install -r requirements-rizin.txt
```

Перед запуском каждого скрипта нужно указать нужные параметры в `config.ini`. В этом файле поле `arch` можно оставлять пустым. Поля `pat` и `sigmake` нужны при запуске в IDA Pro. Там указываются пути по генератора `.pat` файла и до `sigmake`. В остальных случаях можно не указывать

В файле `libs2sigs.py` необходимо указать путь до `config.ini` в функции `rlib_to_sig`

## Установка и использование

### IDA Pro

Вызвать скрипт (alt+f7) `get_rust_libs_ida.py` из IDA Pro, открыв нужный файл для анализа

### Rizin

Вызвать скрипт `get_rust_libs_rizin.py`:

```bash
python get_rust_libs_rizin.py
```

### Cutter

1. Добавить в параметры запуска `Cutter` или запускать через консоль с флагом `--no-output-redirect`
2. Скопировать `libs2sigs.py` в папку `get_rust_libs_cutter`
3. Перенести эту папку в директорию для Python плагинов (обычно `path/to/Cutter/plugins/python`)
4. Скрипт запустится автоматически