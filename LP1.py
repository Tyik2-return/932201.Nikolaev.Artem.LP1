import argparse
import io
import os
import sys
import time
import tarfile
import bz2
from compression import zstd
from pathlib import Path
from typing import Optional


def print_progress(cur: int, total: int, prefix: str = "", width: int = 50) -> None:
    if total <= 0:
        return
    progress = min(cur / total, 1.0)
    filled = int(width * progress)
    bar = "█" * filled + "░" * (width - filled)
    sys.stdout.write(f"\r{prefix} |{bar}| {progress:6.1%} ({cur}/{total})")
    sys.stdout.flush()


def count_files(path: Path) -> int:
    if path.is_file():
        return 1
    count = 0
    for root, dirs, files in os.walk(path):
        count += len(files)
    return count


def create_tar_archive(src: Path, buf: io.BytesIO, show_progress: bool = False) -> None:
    with tarfile.open(fileobj=buf, mode="w") as tar:
        if src.is_file():
            tar.add(src, arcname=src.name)
        else:
            for root, dirs, files in os.walk(src):
                for file in files:
                    file_path = Path(root) / file
                    arcname = file_path.relative_to(src)
                    tar.add(file_path, arcname=arcname)


def compress_with_zstd(data: bytes, output_path: Path, show_progress: bool = False) -> None:
    compressor = zstd.ZstdCompressor()
    
    if show_progress:
        total = len(data)
        compressed = b""
        chunk_size = 8192
        
        for i in range(0, total, chunk_size):
            chunk = data[i:i + chunk_size]
            compressed += compressor.compress(chunk)
            print_progress(min(i + chunk_size, total), total, "Сжатие: ")
        
        compressed += compressor.flush()
        print_progress(total, total, "Сжатие: ")
        print()
    else:
        compressed = compressor.compress(data) + compressor.flush()
    
    output_path.write_bytes(compressed)


def compress_with_bz2(data: bytes, output_path: Path, show_progress: bool = False) -> None:
    if show_progress:
        total = len(data)
        compressed = bz2.compress(data)
        print_progress(total, total, "Сжатие: ")
        print()
        output_path.write_bytes(compressed)
    else:
        compressed = bz2.compress(data)
        output_path.write_bytes(compressed)


def decompress_zstd(input_path: Path, show_progress: bool = False) -> bytes:
    decompressor = zstd.ZstdDecompressor()
    data = input_path.read_bytes()
    
    if show_progress:
        total = len(data)
        decompressed = b""
        chunk_size = 8192
        
        for i in range(0, total, chunk_size):
            chunk = data[i:i + chunk_size]
            decompressed += decompressor.decompress(chunk)
            print_progress(min(i + chunk_size, total), total, "Распаковка: ")
        
        print_progress(total, total, "Распаковка: ")
        print()
        return decompressed
    else:
        return decompressor.decompress(data)


def decompress_bz2(input_path: Path, show_progress: bool = False) -> bytes:
    data = input_path.read_bytes()
    
    if show_progress:
        total = len(data)
        decompressed = bz2.decompress(data)
        print_progress(total, total, "Распаковка: ")
        print()
        return decompressed
    else:
        return bz2.decompress(data)


def archive(src: Path, dst: Path, progress: bool = False, benchmark: bool = False) -> Optional[float]:
    start_time = time.perf_counter() if benchmark else None
    
    if not src.exists():
        print(f"Ошибка: {src} не найден", file=sys.stderr)
        return None
    
    dst_name = dst.name.lower()
    
    if dst_name.endswith(('.tar.zst', '.tar.bz2')):
        archive_type = 'tar'
        if dst_name.endswith('.tar.zst'):
            compression = 'zst'
        else:
            compression = 'bz2'
    elif dst_name.endswith('.zst'):
        archive_type = 'single'
        compression = 'zst'
    elif dst_name.endswith('.bz2'):
        archive_type = 'single'
        compression = 'bz2'
    else:
        print("Ошибка: поддерживаются только форматы .bz2, .zst, .tar.bz2, .tar.zst", file=sys.stderr)
        return None
    
    if src.is_dir() and archive_type != 'tar':
        print("Ошибка: для папок используйте .tar.bz2 или .tar.zst", file=sys.stderr)
        return None
    
    try:
        if archive_type == 'tar':
            buf = io.BytesIO()
            
            if progress:
                total_files = count_files(src)
                print(f"Файлов для архивации: {total_files}")
                create_tar_archive(src, buf)
                print_progress(total_files, total_files, "Архивация: ")
                print()
            else:
                create_tar_archive(src, buf)
            
            data = buf.getvalue()
            
            if compression == 'zst':
                compress_with_zstd(data, dst, progress)
            else:
                if progress:
                    print_progress(0, 1, "Сжатие: ")
                    with tarfile.open(dst, "w:bz2") as tar:
                        tar.add(src, arcname=src.name if src.is_file() else src.name)
                    print_progress(1, 1, "Сжатие: ")
                    print()
                else:
                    with tarfile.open(dst, "w:bz2") as tar:
                        tar.add(src, arcname=src.name if src.is_file() else src.name)
        
        else:
            if progress:
                total_size = src.stat().st_size
                print(f"Размер файла: {total_size / (1024*1024):.2f} МБ")
                print_progress(0, total_size, "Архивация: ")
            
            data = src.read_bytes()
            
            if progress:
                print_progress(total_size, total_size, "Архивация: ")
                print()
            
            if compression == 'zst':
                compress_with_zstd(data, dst, progress)
            else:
                compress_with_bz2(data, dst, progress)
        
        if dst.exists():
            size_mb = dst.stat().st_size / (1024 * 1024)
            
            if benchmark:
                elapsed = time.perf_counter() - start_time
                src_size = src.stat().st_size / (1024 * 1024) if src.is_file() else \
                          sum(f.stat().st_size for f in src.rglob('*') if f.is_file()) / (1024 * 1024)
                ratio = (size_mb / src_size * 100) if src_size > 0 else 0
                
                print(f"\nАрхивация завершена за {elapsed:.2f} секунд")
                print(f"Исходный размер: {src_size:.2f} МБ")
                print(f"Размер архива: {size_mb:.2f} МБ")
                print(f"Степень сжатия: {ratio:.1f}%")
                return elapsed
            else:
                print(f"Архив создан: {dst} ({size_mb:.2f} МБ)")
        
        return None
        
    except Exception as e:
        print(f"Ошибка при архивации: {e}", file=sys.stderr)
        return None


def extract(archive_path: Path, dest_dir: Path, progress: bool = False, benchmark: bool = False) -> Optional[float]:
    start_time = time.perf_counter() if benchmark else None
    
    if not archive_path.exists():
        print(f"Ошибка: {archive_path} не найден", file=sys.stderr)
        return None
    
    archive_name = archive_path.name.lower()
    
    if archive_name.endswith(('.tar.zst', '.tar.bz2')):
        archive_type = 'tar'
        if archive_name.endswith('.tar.zst'):
            compression = 'zst'
        else:
            compression = 'bz2'
    elif archive_name.endswith('.zst'):
        archive_type = 'single'
        compression = 'zst'
    elif archive_name.endswith('.bz2'):
        archive_type = 'single'
        compression = 'bz2'
    else:
        print("Ошибка: поддерживаются только форматы .bz2, .zst, .tar.bz2, .tar.zst", file=sys.stderr)
        return None
    
    dest_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        if archive_type == 'tar':
            if compression == 'bz2':
                if progress:
                    print_progress(0, 1, "Распаковка: ")
                
                with tarfile.open(archive_path, "r:bz2") as tar:
                    members = tar.getmembers()
                    
                    if progress:
                        for i, member in enumerate(members):
                            tar.extract(member, path=dest_dir)
                            print_progress(i + 1, len(members), "Распаковка: ")
                        print()
                    else:
                        tar.extractall(path=dest_dir)
            
            else:
                if progress:
                    print_progress(0, 1, "Распаковка zstd: ")
                
                decompressed = decompress_zstd(archive_path, progress)
                
                if progress:
                    print_progress(1, 2, "Распаковка tar: ")
                
                buf = io.BytesIO(decompressed)
                with tarfile.open(fileobj=buf, mode="r:") as tar:
                    members = tar.getmembers()
                    
                    if progress:
                        for i, member in enumerate(members):
                            tar.extract(member, path=dest_dir)
                            print_progress(i + 1 + len(members), len(members) * 2, "Распаковка tar: ")
                        print()
                    else:
                        tar.extractall(path=dest_dir)
        
        else:
            if progress:
                print_progress(0, 1, "Распаковка: ")
            
            output_name = archive_path.stem
            output_path = dest_dir / output_name
            
            if compression == 'zst':
                data = decompress_zstd(archive_path, progress)
            else:
                data = decompress_bz2(archive_path, progress)
            
            output_path.write_bytes(data)
            
            if progress:
                print_progress(1, 1, "Распаковка: ")
                print()
        
        if benchmark:
            elapsed = time.perf_counter() - start_time
            print(f"\nРаспаковка завершена за {elapsed:.2f} секунд")
            return elapsed
        else:
            print(f"Распаковано в: {dest_dir}")
        
        return None
        
    except Exception as e:
        print(f"Ошибка при распаковке: {e}", file=sys.stderr)
        return None


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Архиватор/распаковщик с поддержкой bz2 и zstd",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:
  Архивация файла в zstd:           python LP1.py archive file.txt archive.zst
  Архивация файла в bz2:            python LP1.py archive file.txt archive.bz2
  Архивация папки в tar.zst:        python LP1.py archive folder/ archive.tar.zst
  Архивация с прогресс-баром:       python LP1.py archive bigfile.txt out.zst --progress
  Архивация с замером времени:      python LP1.py archive data/ backup.tar.bz2 --benchmark
  
  Распаковка zstd:                  python LP1.py extract archive.zst output/
  Распаковка tar.bz2:               python LP1.py extract backup.tar.bz2 restored/
  Распаковка с прогресс-баром:      python LP1.py extract large.tar.zst out/ --progress
  Распаковка с замером времени:     python LP1.py extract archive.bz2 . --benchmark
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", required=True, help="Команда")
    
    archive_parser = subparsers.add_parser("archive", help="Архивировать файл или директорию")
    archive_parser.add_argument("source", type=Path, help="Исходный файл или директория")
    archive_parser.add_argument("destination", type=Path, help="Путь к архиву")
    archive_parser.add_argument("--progress", action="store_true", help="Показать прогресс-бар")
    archive_parser.add_argument("--benchmark", action="store_true", help="Замерить время выполнения")
    
    extract_parser = subparsers.add_parser("extract", help="Распаковать архив")
    extract_parser.add_argument("archive", type=Path, help="Архив для распаковки")
    extract_parser.add_argument("destination", type=Path, nargs="?", default=Path("."),
                              help="Целевая директория (по умолчанию: текущая)")
    extract_parser.add_argument("--progress", action="store_true", help="Показать прогресс-бар")
    extract_parser.add_argument("--benchmark", action="store_true", help="Замерить время выполнения")
    
    args = parser.parse_args()
    
    if args.command == "archive":
        archive(args.source, args.destination, args.progress, args.benchmark)
    else:
        extract(args.archive, args.destination, args.progress, args.benchmark)


if __name__ == "__main__":
    main()
