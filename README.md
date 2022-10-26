# rlibs2sigs

Plugin for IDA / Cutter / Rizin. Generate signatures for compiled binaries written in Rust using strings containing the names and versions of the used libraries

## Requirements

For IDA plugin:

```bash
pip install -r requirements-ida.txt
```

For Rizin / Cutter plugins:

```bash
pip install -r requirements-rizin.txt
```

Before running each script, you need to set the necessary parameters in `config.ini`. The `arch` field can be left empty. The `pat` and `sigmake` fields are needed when starting in IDA Pro. They specifies the paths from the generator of the `.pat` file and `sigmake` binary. In other cases, you don't need to set them

In `libs2sigs.py` you must specify path to `config.ini` in `rlib_to_sig` function

## Installion and usage

### IDA Pro

Run script (alt+f7) `get_rust_libs_ida.py` from IDA Pro after its analyze of necessary binary

### Rizin

Run `get_rust_libs_rizin.py` script:

```bash
python get_rust_libs_rizin.py
```

### Cutter

1. Add to startup options of `Cutter.exe` flag `--no-output-redirect` or use it when running from console
2. Copy `libs2sigs.py` into `get_rust_libs_cutter` directory
3. Move it to directory for Cutter Python plugins (`path/to/Cutter/plugins/python` by default)
4. Script will run automatically after starting `Cutter`

========================================================================================

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