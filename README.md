# 算命学 24節気・命式計算システム

算命学・三命学の命式（年干支・月干支・日干支）を正確に算出するPythonプログラム。

## ファイル構成

| ファイル | 説明 |
|---|---|
| `calculate_sekki_sqlite.py` | 12節気（節入り時刻）を天文計算し、SQLite DBに保存 |
| `meishiki.py` | 生年月日から年干支・月干支・日干支を算出 |

## セットアップ

```bash
pip install skyfield tqdm
```

## 使い方

### Step 1: 節気データベースを生成

```bash
python calculate_sekki_sqlite.py
```

- 対象期間: 1600〜2100年（12節気 × 501年 = 約6,000件）
- 出力: `sekki.db`（SQLite）
- エフェメリス `de430t.bsp` は初回起動時に自動ダウンロード（約130MB）

### Step 2: 命式の算出

```bash
python meishiki.py 1996-08-12 14:30
```

```python
from meishiki import calc_meishiki

result = calc_meishiki("1996-08-12 14:30")
print(result["year_pillar"])   # 丙子
print(result["month_pillar"])  # 戊申
print(result["day_pillar"])    # 辛巳
print(result["is_yashiko"])    # False（夜子刻フラグ）
```

## アルゴリズム

### 年干支
- `(year - 4) % 60` で干支番号を算出（甲子基準年 = 1984年）
- **立春**を境界として、立春前は前年の干支を使用

### 月干支
- SQLite DBから誕生日時の直前の節入りを検索
- 節気名から月支（寅・卯・辰…）を特定
- **五虎遁法**で年干から月干を算出

### 日干支
- 基準日（1800-01-01 = 庚寅/27番）からの経過日数で算出
- **夜子刻**（23:00以降）は翌日の干支を適用

## 使用ライブラリ

- [Skyfield](https://rhodesmill.org/skyfield/) - 天文計算
- JPL エフェメリス DE430t（1550〜2650年対応）
- sqlite3（Python標準）
