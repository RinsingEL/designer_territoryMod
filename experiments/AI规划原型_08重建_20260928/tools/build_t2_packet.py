"""Sync the second task into its independent data directory; no archives."""
from pathlib import Path
root = Path(__file__).resolve().parents[1]
source = root / 'data/题目/02_奥伦选址判断.md'
target = root / 'data/第二题_领土内城市选址/题目.md'
target.write_text(source.read_text(encoding='utf-8'), encoding='utf-8')
print(target)

# Shared code-scale reference for future independent tasks.
from pathlib import Path as _Path
_preview_root = _Path(__file__).resolve().parents[1]
(_preview_root / 'data/第二题_领土内城市选址/07_城市尺度与预览.md').write_text((_preview_root / 'data/题目/07_城市尺度与预览.md').read_text(encoding='utf-8'), encoding='utf-8')
