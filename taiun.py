"""
daiun.py
========
算命学 大運（10年ごとの運気の切り替わり）算出モジュール
"""

from datetime import datetime
from yousen import JUDAI_SHUSEI_MASTER, JUNIDAI_JUSEI_MASTER
from isouhou import get_isouhou, get_sangou

# 十干と十二支のリスト（kanshi_listは1-indexedとするため別途計算用に用意）
KAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
SHI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]

KANSHI_LIST = [
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
    "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
    "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
    "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
    "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥"
]

def is_yang_stem(stem: str) -> bool:
    """天干が陽(+)かどうかを判定する"""
    return stem in ["甲", "丙", "戊", "庚", "壬"]

def get_direction(year_kan: str, gender: str) -> str:
    """
    大運の運行方向（順回り/逆回り）を決定する。
    Args:
        year_kan: 年干（例: "丙"）
        gender: "m" (男性) または "f" (女性)
    """
    is_yang = is_yang_stem(year_kan)
    if gender.lower() == 'm':
        return "Forward" if is_yang else "Reverse"
    elif gender.lower() == 'f':
        return "Reverse" if is_yang else "Forward"
    else:
        raise ValueError(f"不正な性別です: {gender}")

def calculate_unsu(birth_jst: datetime, prev_setsunyu_jst: datetime, next_setsunyu_jst: datetime, 
                   direction: str, is_shukugaku_style: bool = False) -> int:
    """
    大運の運数（開始年齢）を計算する。
    """
    if direction == "Forward":
        # 順回り: 誕生日から次節入りまでの日数
        diff_sec = (next_setsunyu_jst - birth_jst).total_seconds()
    else:
        # 逆回り: 前節入りから誕生日までの日数
        diff_sec = (birth_jst - prev_setsunyu_jst).total_seconds()
    
    diff_days = diff_sec / 86400.0
    val = diff_days / 3.0
    
    if is_shukugaku_style:
        import math
        unsu = math.ceil(val)
    else:
        # 四捨五入（高尾式）: 小数点第一位で四捨五入
        # Pythonのroundは偶数丸めなので、より一般的な四捨五入を実装
        from decimal import Decimal, ROUND_HALF_UP
        unsu = int(Decimal(str(val)).quantize(Decimal('0'), rounding=ROUND_HALF_UP))
    
    # 例外処理
    if unsu <= 0:
        unsu = 1
    elif unsu >= 11:
        unsu = 10
        
    return unsu

def get_natal_tenchusatsu(day_kanshi_idx: int) -> list:
    """
    日干支から宿命天中殺の地支のペアを取得する。
    (day_kanshi_idx は 1〜60)
    """
    # 干支番号から天中殺グループを特定
    # 1〜10 (甲子〜癸酉) -> 戌亥
    # 11〜20 (甲戌〜癸未) -> 申酉
    # 21〜30 (甲申〜癸巳) -> 午未
    # 31〜40 (甲午〜癸卯) -> 辰巳
    # 41〜50 (甲辰〜癸丑) -> 寅卯
    # 51〜60 (甲寅〜癸亥) -> 子丑
    group = (day_kanshi_idx - 1) // 10
    tenchusatsu_groups = [
        ["戌", "亥"],
        ["申", "酉"],
        ["午", "未"],
        ["辰", "巳"],
        ["寅", "卯"],
        ["子", "丑"]
    ]
    return tenchusatsu_groups[group]

def calc_taiun(gender: str, day_kan: str, day_kanshi_idx: int, year_kan: str, month_kanshi_idx: int, 
               birth_jst: datetime, prev_setsunyu_jst: datetime, next_setsunyu_jst: datetime,
               natal_kanshi: dict,
               is_shukugaku_style: bool = False) -> dict:
    """
    大運の1旬〜10旬までのデータを生成する。
    Args:
        gender: "m" (Male) or "f" (Female)
        day_kan: 日干
        day_kanshi_idx: 日干支番号(1〜60)
        year_kan: 年干
        month_kanshi_idx: 月干支番号(1〜60)
        birth_jst: 誕生日時
        prev_setsunyu_jst: 直前の節入り日時
        next_setsunyu_jst: 次の節入り日時
        is_shukugaku_style: 切り上げ(朱学院式)オプション
    """
    direction = get_direction(year_kan, gender)
    start_age = calculate_unsu(birth_jst, prev_setsunyu_jst, next_setsunyu_jst, direction, is_shukugaku_style)
    
    # 宿命天中殺の特定
    natal_tenchusatsu = get_natal_tenchusatsu(day_kanshi_idx)
    
    periods = []
    
    # 月干支を起点にスライド（1旬〜10旬）
    # index 0 is first period
    current_idx = month_kanshi_idx - 1 # 0-indexed
    
    for i in range(10):
        if direction == "Forward":
            current_idx = (current_idx + 1) % 60
        else:
            current_idx = (current_idx - 1) % 60
            
        taiun_kanshi = KANSHI_LIST[current_idx]
        taiun_kan = taiun_kanshi[0]
        taiun_shi = taiun_kanshi[1]
        
        # 星の算出
        judai = JUDAI_SHUSEI_MASTER[day_kan][taiun_kan] + "星"
        junidai = JUNIDAI_JUSEI_MASTER[day_kan][taiun_shi] + "星"
        
        # 大運天中殺の判定
        is_tenchusaku = taiun_shi in natal_tenchusatsu
        
        # 位相法の判定
        isouhou_vs_year = get_isouhou(taiun_kanshi, natal_kanshi["year"])
        isouhou_vs_month = get_isouhou(taiun_kanshi, natal_kanshi["month"])
        isouhou_vs_day = get_isouhou(taiun_kanshi, natal_kanshi["day"])
        
        # 三合（3支揃う場合）の判定
        # 宿命の地支3つ ＋ 大運の地支
        all_shis = [natal_kanshi["year"][1], natal_kanshi["month"][1], natal_kanshi["day"][1], taiun_shi]
        sangou_list = get_sangou(all_shis)
        
        # 年齢範囲
        age_from = start_age + (i * 10)
        age_to = age_from + 9
        
        periods.append({
            "index": i + 1,
            "age_range": f"{age_from}-{age_to}",
            "kanshi": {"no": current_idx + 1, "name": taiun_kanshi},
            "judai_shusei": judai,
            "junidai_jusei": junidai,
            "is_tenchusaku": is_tenchusaku,
            "isouhou": {
                "vs_year": isouhou_vs_year,
                "vs_month": isouhou_vs_month,
                "vs_day": isouhou_vs_day,
                "sangou": sangou_list
            }
        })

    return {
        "taiun_config": {
            "direction": direction,
            "start_age": start_age,
            "gender": gender,
            "is_shukugaku_style": is_shukugaku_style,
            "natal_tenchusatsu": natal_tenchusatsu
        },
        "periods": periods
    }
