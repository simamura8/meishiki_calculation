"""
nenun.py
========
算命学 年運（毎年の運気）算出モジュール
"""

from yousen import JUDAI_SHUSEI_MASTER, JUNIDAI_JUSEI_MASTER
from isouhou import get_isouhou, get_sangou

# 干支のリスト
KANSHI_LIST = [
    "甲子", "乙丑", "丙寅", "丁卯", "戊辰", "己巳", "庚午", "辛未", "壬申", "癸酉",
    "甲戌", "乙亥", "丙子", "丁丑", "戊寅", "己卯", "庚辰", "辛巳", "壬午", "癸未",
    "甲申", "乙酉", "丙戌", "丁亥", "戊子", "己丑", "庚寅", "辛卯", "壬辰", "癸巳",
    "甲午", "乙未", "丙申", "丁酉", "戊戌", "己亥", "庚子", "辛丑", "壬寅", "癸卯",
    "甲辰", "乙巳", "丙午", "丁未", "戊申", "己酉", "庚戌", "辛亥", "壬子", "癸丑",
    "甲寅", "乙卯", "丙辰", "丁巳", "戊午", "己未", "庚申", "辛酉", "壬戌", "癸亥"
]

def calc_nenun(day_kan: str, effective_birth_year: int, seihou_tenchusatsu: list, natal_kanshi: dict, count: int = 100) -> list:
    """
    年運を指定年数分（デフォルト100年）算出する。
    
    Args:
        day_kan: 日干（例: "辛"）
        effective_birth_year: 立春基準の有効な誕生年（0歳の年）
        seihou_tenchusatsu: 西方天中殺のリスト（例: ["申", "酉"]）
        count: 算出する年数
        
    Returns:
        list: 年運データのリスト
    """
    periods = []
    
    for age in range(count):
        current_year = effective_birth_year + age
        
        # 年干支番号の算出 (甲子=1984 -> idx=0)
        kanshi_idx = (current_year - 4) % 60
        nenun_kanshi = KANSHI_LIST[kanshi_idx]
        nenun_kan = nenun_kanshi[0]
        nenun_shi = nenun_kanshi[1]
        
        # 星の算出
        judai = JUDAI_SHUSEI_MASTER[day_kan][nenun_kan] + "星"
        junidai = JUNIDAI_JUSEI_MASTER[day_kan][nenun_shi] + "星"
        
        # 年運天中殺の判定
        is_tenchusaku = nenun_shi in seihou_tenchusatsu
        
        # 位相法の判定
        isouhou_vs_year = get_isouhou(nenun_kanshi, natal_kanshi["year"])
        isouhou_vs_month = get_isouhou(nenun_kanshi, natal_kanshi["month"])
        isouhou_vs_day = get_isouhou(nenun_kanshi, natal_kanshi["day"])
        
        # 三合判定
        all_shis = [natal_kanshi["year"][1], natal_kanshi["month"][1], natal_kanshi["day"][1], nenun_shi]
        sangou_list = get_sangou(all_shis)
        
        periods.append({
            "age": age,
            "year": current_year,
            "kanshi": {"no": kanshi_idx + 1, "name": nenun_kanshi},
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
        
    return periods
