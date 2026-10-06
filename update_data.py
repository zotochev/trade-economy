"""Обновить кэш всех рядов из терминала: uv run python update_data.py [--force]"""
import sys

from core.data import update

if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    results = update(force="--force" in sys.argv)
    for r in results:
        print(f"{'OK ' if r.ok else 'ERR'} {r.key:<18} {r.rows if r.ok else r.error}")
    bad = [r for r in results if not r.ok]
    print(f"\nОбновлено: {len(results) - len(bad)}, ошибок: {len(bad)}")
    sys.exit(1 if bad else 0)
