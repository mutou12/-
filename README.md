# FunASR mock data generator

这个仓库提供一个纯 Python 脚本，用来生成可给 FunASR 训练流程冒烟测试的模拟 ASR 数据。

目标模型默认记录为：`fun-asr-nano-1225`。

> 注意：生成的是“类语音”合成 WAV，不是真人语音。它适合调通数据加载、训练命令、batch、checkpoint 等工程链路，不适合训练可用识别效果。

## 快速生成

```bash
python3 scripts/generate_funasr_mock_data.py \
  --output-dir funasr_mock_data \
  --model fun-asr-nano-1225 \
  --num-train 100 \
  --num-valid 20 \
  --num-speakers 4
```

生成后目录结构：

```text
funasr_mock_data/
  wav/
    train/*.wav
    valid/*.wav
  data/
    train/
      wav.scp
      text
      utt2spk
      spk2utt
      data.list
      manifest.jsonl
    valid/
      wav.scp
      text
      utt2spk
      spk2utt
      data.list
      manifest.jsonl
  metadata.json
  README.md
```

## 给 FunASR 使用

脚本同时生成两类常见输入：

1. Kaldi 风格：

```text
data/train/wav.scp
data/train/text
data/valid/wav.scp
data/valid/text
```

2. JSONL 风格：

```text
data/train/data.list
data/valid/data.list
```

`data.list` 每行格式：

```json
{"key": "train_000000", "source": "/abs/path/train_000000.wav", "target": "欢迎使用语音识别训练样例"}
```

如果你的 FunASR recipe 需要相对路径，可以加：

```bash
python3 scripts/generate_funasr_mock_data.py --relative-paths
```

## 常用参数

```bash
python3 scripts/generate_funasr_mock_data.py --help
```

关键参数：

- `--num-train`：训练集条数
- `--num-valid`：验证集条数
- `--num-speakers`：模拟说话人数
- `--sample-rate`：采样率，默认 `16000`
- `--seed`：随机种子，默认 `1225`
- `--text-file`：自定义文本，每行一条 transcript
- `--duration-scale`：放大或缩短音频时长

自定义文本例子：

```bash
python3 scripts/generate_funasr_mock_data.py \
  --text-file my_transcripts.txt \
  --output-dir funasr_mock_data_custom
```
