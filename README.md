# Архиватор на Python 3.14
Архиватор/распаковщик с поддержкой bz2 и zstd

**команды:**
  {archive,extract}  Команда
    archive          Архивировать файл или директорию
    extract          Распаковать архив

**доп опции:**
  -h, --help         помощь

**Примеры использования:**
  Архивация файла в zstd:           python LP1.py archive file.txt archive.zst
  Архивация файла в bz2:            python LP1.py archive file.txt archive.bz2
  Архивация папки в tar.zst:        python LP1.py archive folder/ archive.tar.zst
  Архивация с прогресс-баром:       python LP1.py archive bigfile.txt out.zst --progress
  Архивация с замером времени:      python LP1.py archive data/ backup.tar.bz2 --benchmark

  Распаковка zstd:                  python LP1.py extract archive.zst output/
  Распаковка tar.bz2:               python LP1.py extract backup.tar.bz2 restored/
  Распаковка с прогресс-баром:      python LP1.py extract large.tar.zst out/ --progress
  Распаковка с замером времени:     python LP1.py extract archive.bz2 . --benchmark



  Примеры простой архивации:
  
<img width="552" height="124" alt="image" src="https://github.com/user-attachments/assets/694ed643-c1ed-41c8-9fce-acef77e0e127" />

Примеры архивации с линией прогресса и результатами загрузки (время, исходный размер, размер после обработки, степень сжатия = до обработки/после обработки):

<img width="686" height="259" alt="image" src="https://github.com/user-attachments/assets/ccfe16f6-77ea-4cc8-ac82-ff953a7288eb" />

Распаковка:

<img width="688" height="135" alt="image" src="https://github.com/user-attachments/assets/3edeefdb-9347-4faf-aab3-5e9bc64e4918" />

Результат:

<img width="587" height="176" alt="image" src="https://github.com/user-attachments/assets/43a24c3a-4be3-4ffc-8762-1fe2d15dad87" />


