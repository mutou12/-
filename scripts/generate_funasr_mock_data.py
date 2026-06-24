#!/usr/bin/env python3
"""Generate mock ASR data for FunASR training smoke tests.

The generated audio is deterministic, mono 16-bit PCM WAV. It is not natural
speech, but it gives FunASR-style training/evaluation pipelines valid audio and
transcript files to exercise data loading, batching, and checkpoint plumbing.
"""

from __future__ import annotations

import argparse
import json
import math
import random
import re
import wave
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


DEFAULT_PHRASES = [
    "欢迎使用语音识别训练样例",
    "这是一个模拟音频数据集",
    "模型名称是funasr nano",
    "今天我们生成可复现的训练数据",
    "请检查数据加载和训练流程",
    "这段音频用于冒烟测试",
    "自动语音识别需要音频和文本",
    "样本数量可以通过参数调整",
    "验证集用于快速检查过拟合",
    "训练脚本读取清单文件",
    "每个说话人都有独立音色",
    "输出目录包含wav和标注",
    "模拟数据不能代表真实效果",
    "它适合调通funasr训练链路",
    "请在真实数据上训练正式模型",
]

PUNCTUATION_RE = re.compile(r"[，。！？、；：,.!?;:\s]+")


@dataclass(frozen=True)
class Sample:
    key: str
    speaker: str
    text: str
    wav_path: Path
    duration: float
    num_samples: int


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate FunASR-compatible mock ASR training data."
    )
    parser.add_argument(
        "--output-dir",
        default="funasr_mock_data",
        help="Directory to write the generated dataset.",
    )
    parser.add_argument(
        "--model",
        default="fun-asr-nano-1225",
        help="Model name recorded in metadata.",
    )
    parser.add_argument(
        "--num-train",
        type=int,
        default=100,
        help="Number of training utterances to generate.",
    )
    parser.add_argument(
        "--num-valid",
        type=int,
        default=20,
        help="Number of validation utterances to generate.",
    )
    parser.add_argument(
        "--num-speakers",
        type=int,
        default=4,
        help="Number of synthetic speakers.",
    )
    parser.add_argument(
        "--sample-rate",
        type=int,
        default=16000,
        help="WAV sample rate. FunASR ASR recipes commonly use 16000.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=1225,
        help="Random seed for reproducible audio and transcripts.",
    )
    parser.add_argument(
        "--duration-scale",
        type=float,
        default=1.0,
        help="Scale factor for per-character duration.",
    )
    parser.add_argument(
        "--text-file",
        type=Path,
        help="Optional UTF-8 text file. One transcript per line.",
    )
    parser.add_argument(
        "--relative-paths",
        action="store_true",
        help="Write paths in manifests relative to output-dir instead of absolute paths.",
    )
    return parser.parse_args()


def normalize_text(text: str) -> str:
    """Keep transcripts compact and friendly to ASR tokenization."""
    text = PUNCTUATION_RE.sub("", text.strip().lower())
    return text


def load_phrases(text_file: Path | None) -> list[str]:
    if text_file is None:
        return DEFAULT_PHRASES

    phrases = []
    for line in text_file.read_text(encoding="utf-8").splitlines():
        text = normalize_text(line)
        if text:
            phrases.append(text)

    if not phrases:
        raise ValueError(f"No usable transcripts found in {text_file}")
    return phrases


def ensure_positive_args(args: argparse.Namespace) -> None:
    checks = {
        "--num-train": args.num_train,
        "--num-valid": args.num_valid,
        "--num-speakers": args.num_speakers,
        "--sample-rate": args.sample_rate,
        "--duration-scale": args.duration_scale,
    }
    for name, value in checks.items():
        if value <= 0:
            raise ValueError(f"{name} must be positive, got {value!r}")


def char_frequency(char: str, speaker_index: int) -> float:
    # Stable pseudo-phoneme pitch per character and speaker.
    return 125.0 + ((ord(char) + speaker_index * 41) % 260)


def synthesize_text(
    text: str,
    speaker_index: int,
    sample_rate: int,
    rng: random.Random,
    duration_scale: float,
) -> list[int]:
    samples: list[float] = []

    leading_silence = int(sample_rate * rng.uniform(0.04, 0.10))
    samples.extend([0.0] * leading_silence)

    for position, char in enumerate(text):
        base_freq = char_frequency(char, speaker_index)
        char_duration = rng.uniform(0.075, 0.15) * duration_scale
        char_samples = max(1, int(sample_rate * char_duration))
        vibrato_rate = rng.uniform(3.0, 6.0)
        vibrato_depth = rng.uniform(0.006, 0.018)
        amplitude = rng.uniform(0.30, 0.55)

        for i in range(char_samples):
            t = i / sample_rate
            progress = i / max(1, char_samples - 1)
            envelope = math.sin(math.pi * progress)
            vibrato = 1.0 + vibrato_depth * math.sin(2.0 * math.pi * vibrato_rate * t)
            freq = base_freq * vibrato
            # A few harmonics make the signal less like a pure beep.
            value = (
                math.sin(2.0 * math.pi * freq * t)
                + 0.45 * math.sin(2.0 * math.pi * freq * 2.0 * t)
                + 0.18 * math.sin(2.0 * math.pi * freq * 3.0 * t)
            )
            noise = rng.uniform(-0.018, 0.018)
            samples.append((value * envelope * amplitude) + noise)

        if position < len(text) - 1:
            pause = int(sample_rate * rng.uniform(0.012, 0.035))
            samples.extend([0.0] * pause)

    trailing_silence = int(sample_rate * rng.uniform(0.04, 0.10))
    samples.extend([0.0] * trailing_silence)

    peak = max((abs(sample) for sample in samples), default=1.0)
    if peak <= 0:
        peak = 1.0

    return [
        max(-32768, min(32767, int((sample / peak) * 28000)))
        for sample in samples
    ]


def write_wav(path: Path, samples: Iterable[int], sample_rate: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        frames = bytearray()
        for sample in samples:
            frames.extend(int(sample).to_bytes(2, byteorder="little", signed=True))
        wav_file.writeframes(frames)


def path_for_manifest(path: Path, output_dir: Path, relative_paths: bool) -> str:
    if relative_paths:
        return path.relative_to(output_dir).as_posix()
    return str(path.resolve())


def build_samples(
    split: str,
    count: int,
    phrases: list[str],
    output_dir: Path,
    sample_rate: int,
    rng: random.Random,
    num_speakers: int,
    duration_scale: float,
) -> list[Sample]:
    samples = []
    for index in range(count):
        speaker_index = index % num_speakers
        speaker = f"spk{speaker_index:04d}"
        phrase = normalize_text(rng.choice(phrases))
        key = f"{split}_{index:06d}"
        wav_path = output_dir / "wav" / split / f"{key}.wav"
        waveform = synthesize_text(
            phrase,
            speaker_index=speaker_index,
            sample_rate=sample_rate,
            rng=rng,
            duration_scale=duration_scale,
        )
        write_wav(wav_path, waveform, sample_rate)
        samples.append(
            Sample(
                key=key,
                speaker=speaker,
                text=phrase,
                wav_path=wav_path,
                duration=len(waveform) / sample_rate,
                num_samples=len(waveform),
            )
        )
    return samples


def write_split_manifests(
    split: str,
    samples: list[Sample],
    output_dir: Path,
    sample_rate: int,
    relative_paths: bool,
) -> None:
    split_dir = output_dir / "data" / split
    split_dir.mkdir(parents=True, exist_ok=True)

    spk_to_utts: dict[str, list[str]] = defaultdict(list)
    for sample in samples:
        spk_to_utts[sample.speaker].append(sample.key)

    with (split_dir / "wav.scp").open("w", encoding="utf-8") as f_wav, (
        split_dir / "text"
    ).open("w", encoding="utf-8") as f_text, (
        split_dir / "utt2spk"
    ).open("w", encoding="utf-8") as f_utt2spk, (
        split_dir / "data.list"
    ).open("w", encoding="utf-8") as f_data_list, (
        split_dir / "manifest.jsonl"
    ).open("w", encoding="utf-8") as f_manifest:
        for sample in samples:
            wav_path = path_for_manifest(sample.wav_path, output_dir, relative_paths)
            f_wav.write(f"{sample.key} {wav_path}\n")
            f_text.write(f"{sample.key} {sample.text}\n")
            f_utt2spk.write(f"{sample.key} {sample.speaker}\n")

            data_row = {
                "key": sample.key,
                "source": wav_path,
                "target": sample.text,
            }
            manifest_row = {
                **data_row,
                "speaker": sample.speaker,
                "duration": round(sample.duration, 4),
                "sample_rate": sample_rate,
                "num_samples": sample.num_samples,
            }
            f_data_list.write(json.dumps(data_row, ensure_ascii=False) + "\n")
            f_manifest.write(json.dumps(manifest_row, ensure_ascii=False) + "\n")

    with (split_dir / "spk2utt").open("w", encoding="utf-8") as f_spk2utt:
        for speaker, utterances in sorted(spk_to_utts.items()):
            f_spk2utt.write(f"{speaker} {' '.join(utterances)}\n")


def write_dataset_readme(output_dir: Path, model: str) -> None:
    readme = f"""# FunASR mock dataset

Target model: `{model}`

This directory contains synthetic WAV files and ASR transcripts for quickly
checking a FunASR training pipeline. The audio is generated, not real speech,
so it is only suitable for smoke tests and debugging data loading.

## Layout

```text
wav/train/*.wav
wav/valid/*.wav
data/train/wav.scp
data/train/text
data/train/utt2spk
data/train/spk2utt
data/train/data.list
data/train/manifest.jsonl
data/valid/...
metadata.json
```

Use `data/<split>/wav.scp` + `data/<split>/text` for Kaldi-style recipes, or
`data/<split>/data.list` for JSONL-style loaders.
"""
    (output_dir / "README.md").write_text(readme, encoding="utf-8")


def main() -> None:
    args = parse_args()
    ensure_positive_args(args)

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    phrases = load_phrases(args.text_file)
    rng = random.Random(args.seed)

    train_samples = build_samples(
        split="train",
        count=args.num_train,
        phrases=phrases,
        output_dir=output_dir,
        sample_rate=args.sample_rate,
        rng=rng,
        num_speakers=args.num_speakers,
        duration_scale=args.duration_scale,
    )
    valid_samples = build_samples(
        split="valid",
        count=args.num_valid,
        phrases=phrases,
        output_dir=output_dir,
        sample_rate=args.sample_rate,
        rng=rng,
        num_speakers=args.num_speakers,
        duration_scale=args.duration_scale,
    )

    write_split_manifests(
        "train",
        train_samples,
        output_dir,
        args.sample_rate,
        args.relative_paths,
    )
    write_split_manifests(
        "valid",
        valid_samples,
        output_dir,
        args.sample_rate,
        args.relative_paths,
    )

    metadata = {
        "model": args.model,
        "seed": args.seed,
        "sample_rate": args.sample_rate,
        "num_speakers": args.num_speakers,
        "num_train": args.num_train,
        "num_valid": args.num_valid,
        "duration_scale": args.duration_scale,
        "format": [
            "kaldi wav.scp/text/utt2spk/spk2utt",
            "jsonl data.list",
            "jsonl manifest.jsonl",
        ],
    }
    (output_dir / "metadata.json").write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    write_dataset_readme(output_dir, args.model)

    print(f"Generated mock FunASR dataset at: {output_dir.resolve()}")
    print(f"  train utterances: {len(train_samples)}")
    print(f"  valid utterances: {len(valid_samples)}")
    print(f"  train wav.scp: {output_dir / 'data' / 'train' / 'wav.scp'}")
    print(f"  train text:    {output_dir / 'data' / 'train' / 'text'}")
    print(f"  train jsonl:   {output_dir / 'data' / 'train' / 'data.list'}")


if __name__ == "__main__":
    main()
