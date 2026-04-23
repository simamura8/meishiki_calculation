"""
meishiki.py
===========
算命学 宿命算出プログラム
年干支・月干支・日干支を計算する

Usage:
    python meishiki.py 1996-08-12 14:30
    python meishiki.py 1996-08-12 23:30   # 夜子刻（翌日扱い）
"""

import sqlite3
from datetime import datetime, timedelta, date
from pathlib import Path

from zokan import calc_zokan
from yousen import calc_yousen

# -------------------------------------------------------
# 定数定義
# -------------------------------------------------------

DB_PATH = Path(__file__).parent / "sekki.db"

# 十干（天干）
KAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]

# 十二支（地支）
SHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

# 六十干支リスト（1番〜60番）
KANSHI_LIST = [
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
    "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
    "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
    "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
    "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥"
]

# 節気名 → 月支インデックス（寅=1, 卯=2, ... 丑=12）
# ※算命学上の月支の対応
SEKKI_TO_MONTH_SHI = {
    "立春": ("寅", 1),
    "啓蟄": ("卯", 2),
    "清明": ("辰", 3),
    "立夏": ("巳", 4),
    "芒種": ("午", 5),
    "小暑": ("未", 6),
    "立秋": ("申", 7),
    "白露": ("酉", 8),
    "寒露": ("戌", 9),
    "立冬": ("亥", 10),
    "大雪": ("子", 11),
    "小寒": ("丑", 12),
}

# -------------------------------------------------------
# Step 1: 月支の特定と年度の確定
# -------------------------------------------------------

def get_month_pillar_info(birth_dt: datetime, conn: sqlite3.Connection) -> dict:
    """
    誕生日時の直前の節入りを取得し、月支と effective_year を返す。

    Args:
        birth_dt: 誕生日時（JST・タイムゾーン付き）
        conn: SQLite 接続

    Returns:
        dict:
            sekki_name: 節気名
            shi: 月支（例: "寅"）
            shi_idx: 月支インデックス（寅=1〜丑=12）
            effective_year: 年干支算出に使う年
            sekki_jst: 節入り日時（文字列）
    """
    birth_str = birth_dt.strftime("%Y-%m-%d %H:%M:%S")

    cursor = conn.cursor()
    # 誕生日時直前の最新の節入りを取得
    row = cursor.execute(
        "SELECT year, name, jst FROM sekki WHERE jst <= ? ORDER BY jst DESC LIMIT 1",
        (birth_str,)
    ).fetchone()

    if row is None:
        raise ValueError(f"節気データが見つかりません（範囲外の日付: {birth_str}）")

    sekki_year, sekki_name, sekki_jst = row

    if sekki_name not in SEKKI_TO_MONTH_SHI:
        raise ValueError(f"未定義の節気名: {sekki_name}")

    shi, shi_idx = SEKKI_TO_MONTH_SHI[sekki_name]

    # 立春より前（＝丑月: 小寒が直前の節）であれば前年の年干支を使う
    # effective_year の決定: 小寒(丑月=12番)は前年扱い
    if sekki_name == "立春":
        effective_year = sekki_year
    elif sekki_name == "小寒":
        # 小寒は旧暦1月（年が変わる前）→ 前年の年干支を使う
        effective_year = sekki_year - 1
    else:
        effective_year = sekki_year

    return {
        "sekki_name": sekki_name,
        "shi":         shi,
        "shi_idx":     shi_idx,
        "effective_year": effective_year,
        "sekki_jst":   sekki_jst,
    }

# -------------------------------------------------------
# Step 2: 年干支の算出
# -------------------------------------------------------

def get_year_kanshi(effective_year: int) -> dict:
    """
    年干支を算出する。

    算出式: (year - 3) % 60 → 干支番号（0〜59 → +1 で 1〜60）

    Args:
        effective_year: 立春基準で補正済みの年

    Returns:
        dict: kanshi（干支名）, kan（天干）, shi（地支）, number（1〜60）
    """
    idx_0 = (effective_year - 4) % 60   # 0〜59 ※甲子基準年=1984
    kanshi = KANSHI_LIST[idx_0]
    return {
        "kanshi": kanshi,
        "kan":    kanshi[0],
        "shi":    kanshi[1],
        "number": idx_0 + 1,
        "kan_idx": idx_0 % 10,  # 天干インデックス（甲=0〜癸=9）
    }

# -------------------------------------------------------
# Step 3: 月干支の算出（五虎遁法）
# -------------------------------------------------------

def get_month_kanshi(year_kan_idx: int, month_shi_idx: int) -> dict:
    """
    五虎遁法で月干支を算出する。

    ■ 五虎遁法の規則:
        年干が甲・己 → 寅月の天干: 丙
        年干が乙・庚 → 寅月の天干: 戊
        年干が丙・辛 → 寅月の天干: 庚
        年干が丁・壬 → 寅月の天干: 壬
        年干が戊・癸 → 寅月の天干: 甲

    Args:
        year_kan_idx: 年干インデックス（甲=0, 乙=1, ... 癸=9）
        month_shi_idx: 月支インデックス（寅=1, 卯=2, ... 丑=12）

    Returns:
        dict: kanshi（干支名）, kan（天干）, shi（月支）
    """
    # 寅月の天干の開始インデックス（五虎遁法）
    # 年干が甲己(0,5)→丙(2), 乙庚(1,6)→戊(4), 丙辛(2,7)→庚(6), 丁壬(3,8)→壬(8), 戊癸(4,9)→甲(0)
    start_kan_idx = ((year_kan_idx % 5) * 2 + 2) % 10

    # 月支インデックス（寅=1〜丑=12）を0ベースにして天干を進める
    kan_idx = (start_kan_idx + (month_shi_idx - 1)) % 10

    # 月支（地支）: 寅=2, 卯=3, ... のSHIリスト上のインデックス
    # SHI = ["子","丑","寅","卯","辰","巳","午","未","申","酉","戌","亥"]
    # 寅月(1) → SHI[2], 卯月(2) → SHI[3], ... 丑月(12) → SHI[1]
    shi_list_idx = (month_shi_idx + 1) % 12  # 寅(1)→2, 卯(2)→3, ... 丑(12)→1
    shi = SHI[shi_list_idx]

    kan = KAN[kan_idx]
    kanshi = kan + shi

    return {
        "kanshi": kanshi,
        "kan": kan,
        "shi": shi,
    }

# -------------------------------------------------------
# Step 4: 日干支の算出
# -------------------------------------------------------

def get_day_kanshi(birth_dt: datetime) -> dict:
    """
    日干支を算出する。

    基準日: 1800年1月1日 = 庚寅（27番目, 0ベースindex=26）
    夜子刻: 23:00以降は翌日の干支を適用する。

    Args:
        birth_dt: 誕生日時（タイムゾーン付き）

    Returns:
        dict: kanshi, kan, shi, is_yashiko（夜子刻フラグ）
    """
    # 夜子刻（23時以降）の判定
    is_yashiko = birth_dt.hour >= 23

    # 日付の決定（夜子刻なら翌日扱い）
    target_date = birth_dt.date()
    if is_yashiko:
        target_date = target_date + timedelta(days=1)

    # 基準日: 1800年1月1日（庚寅 = 27番, index=26）
    base_date = date(1800, 1, 1)
    diff_days = (target_date - base_date).days

    idx_0 = (diff_days + 26) % 60
    kanshi = KANSHI_LIST[idx_0]

    return {
        "kanshi":    kanshi,
        "kan":       kanshi[0],
        "shi":       kanshi[1],
        "number":    idx_0 + 1,
        "is_yashiko": is_yashiko,
    }

# -------------------------------------------------------
# メイン関数: 命式算出
# -------------------------------------------------------

def calc_meishiki(birth_datetime_str: str, db_path: str = None) -> dict:
    """
    命式（年干支・月干支・日干支）を算出するメイン関数。

    Args:
        birth_datetime_str: "YYYY-MM-DD HH:MM" 形式の文字列
        db_path: SQLite DBのパス（省略時はデフォルトパスを使用）

    Returns:
        dict:
            year_pillar: 年干支
            month_pillar: 月干支
            day_pillar: 日干支
            is_yashiko: 夜子刻フラグ（23時以降True）
            _detail: 詳細情報（デバッグ用）
    """
    if db_path is None:
        db_path = str(DB_PATH)

    # 入力パース（JST として扱う）
    from datetime import timezone, timedelta
    JST = timezone(timedelta(hours=9))
    try:
        birth_dt = datetime.strptime(birth_datetime_str, "%Y-%m-%d %H:%M")
    except ValueError:
        birth_dt = datetime.strptime(birth_datetime_str, "%Y-%m-%d %H:%M:%S")
    birth_dt = birth_dt.replace(tzinfo=JST)

    conn = sqlite3.connect(db_path)

    try:
        # Step 1: 月支の特定
        month_info = get_month_pillar_info(birth_dt, conn)

        # Step 2: 年干支
        year_info = get_year_kanshi(month_info["effective_year"])

        # Step 3: 月干支（五虎遁法）
        month_kanshi = get_month_kanshi(year_info["kan_idx"], month_info["shi_idx"])

        # Step 4: 日干支
        day_info = get_day_kanshi(birth_dt)

        # Step 5: 蔵干（二十八宿）
        setsunyu_dt = datetime.strptime(month_info["sekki_jst"], "%Y-%m-%d %H:%M:%S").replace(tzinfo=JST)
        zokan_result = calc_zokan(year_info["shi"], month_kanshi["shi"], day_info["shi"], birth_dt, setsunyu_dt)

        # Step 6: 陽占（十大主星・十二大従星）
        yousen_result = calc_yousen(
            day_kan=day_info["kan"],
            year_kan=year_info["kan"],
            month_kan=month_kanshi["kan"],
            year_shi=year_info["shi"],
            month_shi=month_kanshi["shi"],
            day_shi=day_info["shi"],
            year_zokan=zokan_result["year_zokan"],
            month_zokan=zokan_result["month_zokan"],
            day_zokan=zokan_result["day_zokan"]
        )

    finally:
        conn.close()

    return {
        "year_pillar":  year_info["kanshi"],
        "month_pillar": month_kanshi["kanshi"],
        "day_pillar":   day_info["kanshi"],
        "year_zokan":   zokan_result["year_zokan"],
        "month_zokan":  zokan_result["month_zokan"],
        "day_zokan":    zokan_result["day_zokan"],
        "yousen":       yousen_result,
        "is_yashiko":   day_info["is_yashiko"],
        "_detail": {
            "effective_year":  month_info["effective_year"],
            "sekki_name":      month_info["sekki_name"],
            "sekki_jst":       month_info["sekki_jst"],
            "year_kan":        year_info["kan"],
            "year_shi":        year_info["shi"],
            "year_number":     year_info["number"],
            "month_shi":       month_info["shi"],
            "month_shi_idx":   month_info["shi_idx"],
            "day_number":      day_info["number"],
            "elapsed_days":    zokan_result["debug_info"]["elapsed_days"],
        }
    }

# -------------------------------------------------------
# CLI エントリーポイント
# -------------------------------------------------------

def print_result(result: dict, birth_str: str):
    """結果を見やすく表示する"""
    d = result["_detail"]
    print("=" * 50)
    print(f"  算命学 命式算出結果")
    print(f"  生年月日: {birth_str}")
    print("=" * 50)
    print(f"  年干支: {result['year_pillar']} (蔵干: {result['year_zokan']})")
    print(f"  月干支: {result['month_pillar']} (蔵干: {result['month_zokan']})")
    print(f"  日干支: {result['day_pillar']} (蔵干: {result['day_zokan']})")
    if result["is_yashiko"]:
        print(f"  ※ 夜子刻（23時以降）: 日干支は翌日扱い")
    print("-" * 50)
    print(f"  [陽占（十大主星・十二大従星）]")
    ys = result["yousen"]
    jd = ys["judai_shusei"]
    jn = ys["junidai_jusei"]
    print(f"  北 (親・目上)    : {jd['north']}")
    print(f"  東 (社会・兄弟)  : {jd['east']}")
    print(f"  中央 (自分自身)  : {jd['center']}")
    print(f"  西 (配偶者)      : {jd['west']}")
    print(f"  南 (子供・目下)  : {jd['south']}")
    print(f"  初年期 (右上)    : {jn['hatsunen']}")
    print(f"  中年期 (右下)    : {jn['chuunen']}")
    print(f"  晩年期 (左下)    : {jn['bannen']}")
    print("-" * 50)
    print(f"  [詳細]")
    print(f"  有効年: {d['effective_year']}年")
    print(f"  直前の節入り: {d['sekki_name']} ({d['sekki_jst']})")
    print(f"  節入りからの経過日数: {d['elapsed_days']}日")
    print(f"  月支: {d['month_shi']} ({d['month_shi_idx']}番)")
    print(f"  年干支番号: {d['year_number']}番")
    print(f"  日干支番号: {d['day_number']}番")
    print("=" * 50)


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        # コマンドライン引数から
        date_str = sys.argv[1]
        time_str = sys.argv[2]
        birth_str = f"{date_str} {time_str}"
    elif len(sys.argv) == 2:
        birth_str = sys.argv[1]
    else:
        # 引数なしの場合はテストデータで実行
        print("引数なし: テストデータで実行します。")
        print("Usage: python meishiki.py 1996-08-12 14:30\n")
        birth_str = "1996-08-12 14:30"

    result = calc_meishiki(birth_str)
    print_result(result, birth_str)
