"""
zokan.py
========
算命学 蔵干（二十八宿）算出モジュール
年支・月支・日支と節入りからの経過秒数に基づき、それぞれの蔵干を特定する。
"""

from datetime import datetime

# 蔵干判定テーブル
# 各十二支に対し、(累積日数, 干) のリストを定義
# 累積日数は初元、中元、本元の切り替わりタイミング
# ※日数が30日を超える場合や条件に合致しない場合は最後の要素(本元)を採用する
ZOKAN_TABLE = {
    "子": [(30, "癸")],
    "丑": [(9, "癸"), (12, "辛"), (30, "己")],
    "寅": [(7, "戊"), (14, "丙"), (30, "甲")],
    "卯": [(30, "乙")],
    "辰": [(9, "乙"), (12, "癸"), (30, "戊")],
    "巳": [(5, "戊"), (14, "庚"), (30, "丙")],
    "午": [(19, "己"), (30, "丁")],
    "未": [(9, "丁"), (12, "乙"), (30, "己")],
    "申": [(10, "戊"), (13, "壬"), (30, "庚")],
    "酉": [(30, "辛")],
    "戌": [(9, "辛"), (12, "丁"), (30, "戊")],
    "亥": [(12, "甲"), (30, "壬")],
}

def get_single_zokan(shi: str, elapsed_sec: float) -> str:
    """
    1つの十二支に対する蔵干を判定する。
    
    Args:
        shi: 十二支 (例: "寅")
        elapsed_sec: 節入りからの経過秒数
        
    Returns:
        str: 蔵干（天干）
    """
    if shi not in ZOKAN_TABLE:
        raise ValueError(f"不正な十二支です: {shi}")
        
    for days, kan in ZOKAN_TABLE[shi]:
        # elapsed_sec < (日数 * 86400) が真となった瞬間の干を採用
        if elapsed_sec < days * 86400:
            return kan
            
    # 全ての条件から外れた場合（日数が30日を超えるなど）は「本元」（リストの最後）を採用
    return ZOKAN_TABLE[shi][-1][1]

def calc_zokan(year_shi: str, month_shi: str, day_shi: str, birth_jst: datetime, setsunyu_jst: datetime) -> dict:
    """
    年・月・日の各支に対する蔵干を一括で算出する。
    
    Args:
        year_shi: 年支
        month_shi: 月支
        day_shi: 日支
        birth_jst: ユーザーの誕生日時
        setsunyu_jst: その月の節入り日時
        
    Returns:
        dict: 蔵干とデバッグ情報を含む辞書
    """
    # 節入りからの経過秒数を算出
    elapsed_sec = (birth_jst - setsunyu_jst).total_seconds()
    
    # 経過日数を算出 (デバッグ用)
    elapsed_days = elapsed_sec / 86400.0
    
    # 各支の蔵干を判定
    year_zokan = get_single_zokan(year_shi, elapsed_sec)
    month_zokan = get_single_zokan(month_shi, elapsed_sec)
    day_zokan = get_single_zokan(day_shi, elapsed_sec)
    
    return {
        "year_zokan": year_zokan,
        "month_zokan": month_zokan,
        "day_zokan": day_zokan,
        "debug_info": {
            "elapsed_days": round(elapsed_days, 4),
            "target_month_setsunyu": setsunyu_jst.strftime("%Y-%m-%d %H:%M:%S")
        }
    }

if __name__ == "__main__":
    # 簡単な動作テスト
    from datetime import timezone, timedelta
    JST = timezone(timedelta(hours=9))
    
    # テストデータ: 2026年2月20日 12:00（立春が2026-02-04 11:42:00と仮定）
    b_dt = datetime(2026, 2, 20, 12, 0, 0, tzinfo=JST)
    s_dt = datetime(2026, 2, 4, 11, 42, 0, tzinfo=JST)
    
    # 年支=午, 月支=寅, 日支=申 と仮定
    res = calc_zokan("午", "寅", "申", b_dt, s_dt)
    
    import json
    print(json.dumps(res, ensure_ascii=False, indent=4))
