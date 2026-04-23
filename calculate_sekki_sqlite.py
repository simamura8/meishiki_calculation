"""
calculate_sekki_sqlite.py
=========================
算命学・三命学向け 12節気（節のみ）計算 & SQLite保存スクリプト
対象期間: 1600年 〜 2100年
出力形式: SQLite データベース (sekki.db)

依存ライブラリ:
    pip install skyfield tqdm
"""

import sqlite3
import os
from datetime import datetime, timezone, timedelta
from pathlib import Path

from skyfield.api import load
from tqdm import tqdm

# -------------------------------------------------------
# 定数・設定
# -------------------------------------------------------

# 日本標準時 (JST = UTC+9)
JST = timezone(timedelta(hours=9))

# データベースファイル名
DB_NAME = "sekki.db"
DB_PATH = Path(__file__).parent / DB_NAME

# 12節気の定義
SEKKI_TABLE = [
    (285, "小寒",  1),
    (315, "立春",  2),
    (345, "啓蟄",  3),
    (15,  "清明",  4),
    (45,  "立夏",  5),
    (75,  "芒種",  6),
    (105, "小暑",  7),
    (135, "立秋",  8),
    (165, "白露",  9),
    (195, "寒露", 10),
    (225, "立冬", 11),
    (255, "大雪", 12),
]

ANGLE_TO_SEKKI = {angle: (name, month) for angle, name, month in SEKKI_TABLE}

# -------------------------------------------------------
# データベース準備
# -------------------------------------------------------

def init_db():
    """データベースとテーブルを初期化する"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 既存のテーブルがあれば削除（クリーンな状態から開始する場合）
    cursor.execute("DROP TABLE IF EXISTS sekki")
    
    # テーブル作成
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sekki (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            year INTEGER,
            month INTEGER,
            name TEXT,
            angle INTEGER,
            jst TEXT
        )
    """)
    
    # 検索を高速化するためのインデックス
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_jst ON sekki(jst)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_year ON sekki(year)")
    
    conn.commit()
    return conn

# -------------------------------------------------------
# 天文計算ロジック
# -------------------------------------------------------

def setup_skyfield():
    ts = load.timescale()
    # 1600年を扱うため DE430t を使用
    try:
        eph = load("de430t.bsp")
    except Exception:
        eph = load("de421.bsp")
    return ts, eph

def solar_longitude(t, earth, sun):
    astrometric = earth.at(t).observe(sun).apparent()
    lat, lon, dist = astrometric.ecliptic_latlon()
    return lon.degrees % 360

def find_sekki_time(ts, earth, sun, target_angle_deg, t_start, t_end, tolerance_sec=0.5):
    def angle_diff(lon, target):
        return (lon - target + 180) % 360 - 180

    t0_jd = t_start.tt
    t1_jd = t_end.tt

    lon0 = solar_longitude(ts.tt_jd(t0_jd), earth, sun)
    lon1 = solar_longitude(ts.tt_jd(t1_jd), earth, sun)
    d0 = angle_diff(lon0, target_angle_deg)
    d1 = angle_diff(lon1, target_angle_deg)

    if d0 * d1 > 0:
        return None

    tol_jd = tolerance_sec / 86400.0
    for _ in range(60):
        t_mid_jd = (t0_jd + t1_jd) / 2.0
        lon_mid = solar_longitude(ts.tt_jd(t_mid_jd), earth, sun)
        d_mid = angle_diff(lon_mid, target_angle_deg)
        if abs(t1_jd - t0_jd) < tol_jd:
            return ts.tt_jd(t_mid_jd)
        if d0 * d_mid <= 0:
            t1_jd = t_mid_jd
            d1 = d_mid
        else:
            t0_jd = t_mid_jd
            d0 = d_mid
    return ts.tt_jd((t0_jd + t1_jd) / 2.0)

def calc_year_sekki(year, ts, earth, sun):
    events = []
    # 1600年対応の下限チェック
    t_range_start = ts.utc(year - 1, 12, 1) if year > 1600 else ts.utc(1600, 1, 1)
    t_range_end   = ts.utc(year + 1,  1, 31)

    current_jd = t_range_start.tt
    end_jd     = t_range_end.tt
    found_sekki = []

    lon_start = solar_longitude(ts.tt_jd(current_jd), earth, sun)
    next_15 = (int(lon_start / 15) + 1) * 15
    if (next_15 // 15) % 2 == 1:
        first_target = next_15 % 360
    else:
        first_target = (next_15 + 15) % 360

    target_angles_ordered = []
    ang = first_target
    for _ in range(16):
        target_angles_ordered.append(ang % 360)
        ang = (ang + 30) % 360

    search_start_jd = current_jd
    for target_ang in target_angles_ordered:
        search_end_jd = search_start_jd + 32
        if search_end_jd > end_jd: break
        t_s, t_e = ts.tt_jd(search_start_jd), ts.tt_jd(search_end_jd)
        t_sekki = find_sekki_time(ts, earth, sun, target_ang, t_s, t_e)
        if t_sekki is not None:
            found_sekki.append((t_sekki.tt, target_ang))
            search_start_jd = t_sekki.tt + 1
        else:
            search_start_jd += 29

    jst_year_start = datetime(year, 1, 1, 0, 0, 0, tzinfo=JST)
    jst_year_end   = datetime(year, 12, 31, 23, 59, 59, tzinfo=JST)
    t_ys = ts.from_datetime(jst_year_start.astimezone(timezone.utc))
    t_ye = ts.from_datetime(jst_year_end.astimezone(timezone.utc))

    for jd, angle in found_sekki:
        if t_ys.tt <= jd <= t_ye.tt:
            if angle in ANGLE_TO_SEKKI:
                name, month = ANGLE_TO_SEKKI[angle]
                t_obj = ts.tt_jd(jd)
                y, mo, d, h, mi, s = t_obj.utc
                utc_dt = datetime(int(y), int(mo), int(d), int(h), int(mi), int(s), tzinfo=timezone.utc)
                jst_dt = utc_dt.astimezone(JST)
                events.append((year, month, name, angle, jst_dt.strftime("%Y-%m-%d %H:%M:%S")))
    
    events.sort(key=lambda x: x[4])
    return events

# -------------------------------------------------------
# メイン実行
# -------------------------------------------------------

def main():
    START_YEAR = 1600
    END_YEAR   = 2100

    print("=" * 60)
    print("  12節気 SQLite保存システム (1600-2100)")
    print("=" * 60)

    # DB初期化
    conn = init_db()
    cursor = conn.cursor()

    # Skyfield準備
    ts, eph = setup_skyfield()
    earth, sun = eph["earth"], eph["sun"]

    # 計算実行
    for year in tqdm(range(START_YEAR, END_YEAR + 1), desc="計算中", unit="年"):
        try:
            year_data = calc_year_sekki(year, ts, earth, sun)
            # まとめて挿入
            cursor.executemany(
                "INSERT INTO sekki (year, month, name, angle, jst) VALUES (?, ?, ?, ?, ?)",
                year_data
            )
            # 1年ごとにコミット
            conn.commit()
        except Exception as e:
            tqdm.write(f"Error in {year}: {e}")

    conn.close()
    print(f"\n[完了] データを {DB_NAME} に保存しました。")

if __name__ == "__main__":
    main()
