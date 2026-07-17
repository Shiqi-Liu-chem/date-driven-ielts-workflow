"""
雅思单词背诵段落 TTS 生成脚本

用法:
    python tts.py 260612
    python tts.py 260612 --voice en-GB-SoniaNeural --rate -10%

依赖:
    pip install edge-tts

读取 words/<name>.txt, 抽取 "英文背诵段落" 段落, 生成 words/<name>.mp3
"""

import argparse
import asyncio
import re
import sys
from pathlib import Path

import edge_tts


WORDS_DIR = Path(__file__).parent / "words"

# 雅思口语推荐英式发音; 想要美式可换 en-US-AriaNeural / en-US-GuyNeural
DEFAULT_VOICE = "en-GB-SoniaNeural"
DEFAULT_RATE = "-5%"  # 略慢于正常语速, 便于跟读


def extract_english_paragraph(txt_path: Path) -> str:
    """从 txt 抽取 '英文背诵段落' 与下一节标题之间的内容"""
    content = txt_path.read_text(encoding="utf-8")

    pattern = re.compile(
        r"英文背诵段落\s*\n=+\s*\n(.*?)(?=\n[一-龥]+\s*\n=+|\Z)",
        re.DOTALL,
    )
    m = pattern.search(content)
    if not m:
        raise ValueError(f"在 {txt_path} 中未找到 '英文背诵段落' 段落")

    paragraph = m.group(1).strip()
    if not paragraph:
        raise ValueError(f"{txt_path} 的英文段落为空")
    return paragraph


def normalize_for_speech(text: str) -> str:
    """合并连续行, 只在句号/问号/感叹号后断行, 确保 edge-tts 按句子停顿"""
    # 去掉每行末尾的换行, 合并成一个连续段落
    collapsed = " ".join(line.strip() for line in text.splitlines() if line.strip())
    # 在句尾标点后插入换行, 让 edge-tts 只在这些地方停顿
    collapsed = re.sub(r"(?<=[.?!])\s+(?=[A-Z])", "\n", collapsed)
    return collapsed


async def synthesize(text: str, out_path: Path, voice: str, rate: str) -> None:
    communicate = edge_tts.Communicate(text=text, voice=voice, rate=rate)
    await communicate.save(str(out_path))


def main() -> int:
    parser = argparse.ArgumentParser(description="生成雅思背诵段落 MP3")
    parser.add_argument("name", help="txt 文件名(不带扩展名), 如 260612")
    parser.add_argument("--voice", default=DEFAULT_VOICE, help=f"语音(默认 {DEFAULT_VOICE})")
    parser.add_argument("--rate", default=DEFAULT_RATE, help=f"语速(默认 {DEFAULT_RATE})")
    args = parser.parse_args()

    txt_path = WORDS_DIR / f"{args.name}.txt"
    mp3_path = WORDS_DIR / f"{args.name}.mp3"

    if not txt_path.exists():
        print(f"[错误] 文件不存在: {txt_path}", file=sys.stderr)
        return 1

    text = extract_english_paragraph(txt_path)
    text = normalize_for_speech(text)
    print(f"[信息] 抽取到 {len(text)} 字符的英文段落（已按句子断行）")
    print(f"[信息] 语音: {args.voice}, 语速: {args.rate}")

    asyncio.run(synthesize(text, mp3_path, args.voice, args.rate))
    print(f"[完成] 已生成: {mp3_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
