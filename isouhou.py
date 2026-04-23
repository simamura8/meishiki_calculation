"""
isouhou.py
==========
位相法（Isouhou）算出モジュール
2つの干支、または複数の地支間の位相法や特殊条件（律音、納音、天剋地冲など）を判定する。
"""

# 五行と陰陽の定義
STEM_INFO = {
    "甲": {"element": "木", "polarity": "+"},
    "乙": {"element": "木", "polarity": "-"},
    "丙": {"element": "火", "polarity": "+"},
    "丁": {"element": "火", "polarity": "-"},
    "戊": {"element": "土", "polarity": "+"},
    "己": {"element": "土", "polarity": "-"},
    "庚": {"element": "金", "polarity": "+"},
    "辛": {"element": "金", "polarity": "-"},
    "壬": {"element": "水", "polarity": "+"},
    "癸": {"element": "水", "polarity": "-"}
}

# 五行の相剋関係 (key が value を剋す)
SOKOKU_MAP = {
    "木": "土",
    "土": "水",
    "水": "火",
    "火": "金",
    "金": "木"
}

def is_tenkokuchichu(kan1: str, kan2: str) -> bool:
    """天干が陽同士/陰同士の相剋（七殺）かどうかを判定する"""
    info1 = STEM_INFO[kan1]
    info2 = STEM_INFO[kan2]
    
    # 陰陽が一致しなければFalse
    if info1["polarity"] != info2["polarity"]:
        return False
        
    # 相剋関係か判定（どちらかがどちらかを剋す）
    if SOKOKU_MAP[info1["element"]] == info2["element"] or SOKOKU_MAP[info2["element"]] == info1["element"]:
        return True
        
    return False

# 地支間の位相法マトリックス (2支間)
# ユーザー指定: 三合 -> 半会, 冲 -> 対冲
# 画像の表に従ってマッピング
ISOUHOU_MATRIX = {
    "子": {"丑":"支合", "卯":"旺刑", "辰":"半会", "午":"対冲", "未":"害", "申":"半会", "酉":"破"},
    "丑": {"子":"支合", "辰":"破", "巳":"半会", "午":"害", "未":["庫刑", "対冲"], "酉":"半会", "戌":"庫刑"},
    "寅": {"巳":["貴刑", "害"], "午":"半会", "申":["貴刑", "対冲"], "戌":"半会", "亥":"支合"},
    "卯": {"子":"旺刑", "辰":"害", "午":"破", "未":"半会", "酉":"対冲", "戌":"支合", "亥":"半会"},
    "辰": {"子":"半会", "丑":"破", "卯":"害", "辰":"自刑", "酉":"支合", "戌":"対冲"},
    "巳": {"丑":"半会", "寅":["貴刑", "害"], "申":["貴刑", "支合"], "酉":"半会", "亥":"対冲"},
    "午": {"子":"対冲", "丑":"害", "寅":"半会", "卯":"破", "午":"自刑", "未":"支合", "戌":"半会"},
    "未": {"子":"害", "丑":["庫刑", "対冲"], "卯":"半会", "午":"支合", "戌":["庫刑", "破"], "亥":"半会"},
    "申": {"子":"半会", "寅":["貴刑", "対冲"], "巳":["貴刑", "支合"], "亥":"害"},
    "酉": {"子":"破", "丑":"半会", "卯":"対冲", "辰":"支合", "巳":"半会", "酉":"自刑", "戌":"害"},
    "戌": {"丑":"庫刑", "寅":"半会", "卯":"支合", "辰":"対冲", "午":"半会", "未":["庫刑", "破"], "酉":"害"},
    "亥": {"寅":"支合", "卯":"半会", "未":"半会", "申":"害", "亥":"自刑"}
}

def get_branch_isouhou(shi1: str, shi2: str) -> list:
    """2つの地支の位相法を取得する"""
    rel = ISOUHOU_MATRIX.get(shi1, {}).get(shi2, [])
    if isinstance(rel, str):
        return [rel]
    return rel.copy()

def get_isouhou(kanshi1: str, kanshi2: str) -> list:
    """
    2つの干支の間の位相法および特殊条件を判定してリストで返す。
    kanshi1, kanshi2: 例 "甲子", "丙寅"
    """
    if not kanshi1 or not kanshi2 or len(kanshi1) != 2 or len(kanshi2) != 2:
        return []
        
    kan1, shi1 = kanshi1[0], kanshi1[1]
    kan2, shi2 = kanshi2[0], kanshi2[1]
    
    results = get_branch_isouhou(shi1, shi2)
    
    # 律音 (同干支)
    if kanshi1 == kanshi2:
        results.append("律音")
        
    # 対冲がある場合の判定
    has_taichu = "対冲" in results
    
    # 納音 (天干が同じ & 地支が対冲)
    if kan1 == kan2 and has_taichu:
        results.append("納音")
        
    # 天剋地冲 (天干が同陰陽相剋 & 地支が対冲)
    if has_taichu and is_tenkokuchichu(kan1, kan2):
        results.append("天剋地冲")
        
    return results

def get_sangou(shi_list: list) -> list:
    """
    指定された地支のリストから、三合会局が成立するか判定する。
    成立した場合は ["三合"] または複数成立時のリストを返す。
    """
    unique_shi = set(shi_list)
    results = []
    
    if {"申", "子", "辰"}.issubset(unique_shi):
        results.append("三合(水局)")
    if {"亥", "卯", "未"}.issubset(unique_shi):
        results.append("三合(木局)")
    if {"寅", "午", "戌"}.issubset(unique_shi):
        results.append("三合(火局)")
    if {"巳", "酉", "丑"}.issubset(unique_shi):
        results.append("三合(金局)")
        
    return results
