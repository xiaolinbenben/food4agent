---
name: tvc-transition-master
description: 'TVC级转场设计。实现丝滑转场、匹配剪辑、节奏蒙太奇等电影级转场效果，提升广告的视觉连续性和高级感。'
metadata:
  {
    "openclaw":
      {
        "emoji": "✂️",
        "requires": { "bins": ["python3", "ffmpeg"], "env": ["ARK_API_KEY"] },
        "primaryEnv": "ARK_API_KEY",
      },
  }
---

# TVC 转场设计 Skill

转场是区分"业余视频"和"品牌TVC"的关键标志。本Skill基于顶级广告片的转场规律，生成专业转场方案。

## 转场类型库

| 类型 | 说明 | 适用场景 | 难度 |
|------|------|----------|------|
| match_cut | 形状/动作/颜色匹配剪辑 | 产品与场景切换 | ⭐⭐⭐ |
| silk_smooth | 丝滑速度变化过渡 | 小红书/抖音种草 | ⭐⭐ |
| whip_pan | 急速甩镜头转场 | 节奏快的促销广告 | ⭐⭐ |
| morph | 形态渐变（A融入B） | 品牌片概念表达 | ⭐⭐⭐⭐ |
| light_leak | 光晕/光斑过渡 | 温暖感、复古感 | ⭐ |
| zoom_through | 穿越式缩放 | 科技、空间感 | ⭐⭐⭐ |
| rhythmic_cut | 节奏剪辑（压音乐拍） | 节奏型TVC、运动 | ⭐⭐ |
| invisible_cut | 隐形剪辑（伪一镜到底） | 高端品牌片 | ⭐⭐⭐⭐ |
| split_screen | 分屏对比 | A/B对比、时间对比 | ⭐⭐ |
| j_cut_l_cut | 声音先行/画面先行 | 叙事型广告 | ⭐⭐ |

## 使用方法

```bash
python3 scripts/generate_transitions.py \
  --storyboard ./storyboard.json \
  --style "cinematic" \
  --music-bpm 120 \
  --output ./transition_plan.json
```

## 参数说明

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `--storyboard` | string | ✅ | 分镜脚本 JSON 路径 |
| `--style` | string |  | 转场风格：cinematic/smooth/energetic/minimal/experimental |
| `--music-bpm` | number |  | 配乐 BPM（用于节奏剪辑） |
| `--output` | string |  | 输出路径 |

## 输出格式

```json
{
  "transitions": [
    {
      "from_scene": 1,
      "to_scene": 2,
      "type": "match_cut",
      "detail": "水滴涟漪→精华液瓶身曲线，形状匹配",
      "duration_ms": 500,
      "audio_sync": "在弦乐上升的第2拍切入",
      "prompt_hint": "匹配剪辑，水面涟漪的弧线自然过渡为瓶身曲线"
    }
  ]
}
```

## 事件发布

生成完成后发布 `transitions.generated` 事件。
