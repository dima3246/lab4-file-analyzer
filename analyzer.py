"""Анализатор файловой системы. Python 3.10+, без сторонних библиотек."""
import argparse
import os
from pathlib import Path
from collections import Counter

def analyze(source, output="report.txt"):
    source = Path(source).expanduser().resolve(strict=True)
    output = Path(output).expanduser().resolve()
    if not source.is_dir():
        raise ValueError("Укажите каталог")
    files, errors, extensions = [], [], Counter()
    # Ссылки пропускаются, чтобы избежать циклов.
    for directory, folders, names in os.walk(source, onerror=lambda e: errors.append(str(e)), followlinks=False):
        folders[:] = sorted(p for p in folders if not (Path(directory) / p).is_symlink())
        for name in sorted(names):
            file = Path(directory) / name
            try:
                if file.is_symlink() or file.resolve() == output:
                    continue
                size = file.stat().st_size
                files.append((file.relative_to(source).as_posix(), size))
                extensions[file.suffix.lower() or "(без расширения)"] += 1
            except OSError as error:
                errors.append(f"{file}: {error}")
    files.sort()
    total = sum(size for _, size in files)
    lines = [f"Каталог: {source}", f"Всего файлов: {len(files)}",
             f"Размер в байтах: {total}",
             f"Размер в МБ (1 МБ = 1 000 000 байт): {total / 1_000_000:.6f}",
             "", "Файлы (байты; относительный путь):"]
    lines += [f"{size}; {name}" for name, size in files]
    lines += ["", "Статистика расширений:"]
    lines += [f"{ext}: {count}" for ext, count in sorted(extensions.items())]
    lines += ["", f"Ошибок доступа: {len(errors)}"] + errors
    # Единая кодировка и переводы строк на обеих ОС.
    output.write_bytes(("\n".join(lines) + "\n").encode("utf-8"))
    return {"count": len(files), "bytes": total, "extensions": dict(extensions),
            "errors": errors, "report": str(output)}

def main():
    parser = argparse.ArgumentParser(description="Анализатор файловой системы")
    parser.add_argument("directory", nargs="?")
    parser.add_argument("--output", default="report.txt")
    args = parser.parse_args()
    path = args.directory or input("Путь к каталогу: ").strip()
    try:
        result = analyze(path, args.output)
    except (OSError, ValueError) as error:
        parser.exit(1, f"Ошибка: {error}\n")
    print(f"Файлов: {result['count']}; байт: {result['bytes']}")
    print(f"Отчёт: {result['report']}; ошибок доступа: {len(result['errors'])}")

if __name__ == "__main__":
    main()
