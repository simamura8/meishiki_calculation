import sys
import json
from pathlib import Path
from sanmei.meishiki import calc_meishiki
from sanmei.zokan import ZOKAN_TABLE

def print_result(result: dict, birth_str: str):
    """結果を見やすく表示する"""
    d = result["_detail"]
    
    # 二十八宿の全蔵干を取得し、本元（1つ目）とその他に分ける関数
    def get_zokan_list(shi):
        all_z = [z[1] for z in ZOKAN_TABLE[shi]]
        primary = all_z[-1] # 本元は常に最後
        others = all_z[:-1] # それ以外
        others_str = "<br>".join(reversed(others)) if others else " "
        return primary, others_str
        
    dz_pri, dz_oth = get_zokan_list(result['day_pillar'][1])
    mz_pri, mz_oth = get_zokan_list(result['month_pillar'][1])
    yz_pri, yz_oth = get_zokan_list(result['year_pillar'][1])

    print("=" * 50)
    print(f"  算命学 命式算出結果")
    print(f"  生年月日: {birth_str}")
    print("=" * 50)
    
    print("\n## 陰占")
    print("| 陰占 | | | |")
    print("| --- | --- | --- | --- |")
    print(f"| No. | {d['day_number']} | {d['month_shi_idx']} | {d['year_number']} |")
    print(f"| 天干 | {result['day_pillar'][0]} | {result['month_pillar'][0]} | {result['year_pillar'][0]} |")
    print(f"| 地支 | {result['day_pillar'][1]} | {result['month_pillar'][1]} | {result['year_pillar'][1]} |")
    print(f"| 蔵干 | {dz_pri} | {mz_pri} | {yz_pri} |")
    print(f"| | {dz_oth} | {mz_oth} | {yz_oth} |")
    print("")
    
    if result["is_yashiko"]:
        print(f"※ 夜子刻（23時以降）: 日干支は翌日扱い\n")
        
    ys = result["yousen"]
    jd = ys["judai_shusei"]
    jn = ys["junidai_jusei"]
    
    print("## 陽占")
    print("| 陽占 | | | |")
    print("| --- | --- | --- | --- |")
    print(f"| 　　　 | {jd['north']} | {jn['hatsunen']} |")
    print(f"| {jd['west']} | {jd['center']} | {jd['east']} |")
    print(f"| {jn['bannen']} | {jd['south']} | {jn['chuunen']} |")
    print("")
    
    dc = result["taiun"]["taiun_config"]
    print(f"西方天中殺: {dc['seihou_tenchusatsu'][0]}{dc['seihou_tenchusatsu'][1]}天中殺")
    
    if result["shukumei_tenchusatsu"]:
        print(f"宿命天中殺: {'、'.join(result['shukumei_tenchusatsu'])}")
    
    # 宿命の位相法を表示
    ni = result["natal_isouhou"]
    natal_isouhou_display = []
    if ni["year_month"]:
        natal_isouhou_display.append(f"年月:{','.join(ni['year_month'])}")
    if ni["month_day"]:
        natal_isouhou_display.append(f"月日:{','.join(ni['month_day'])}")
    if ni["year_day"]:
        natal_isouhou_display.append(f"年日:{','.join(ni['year_day'])}")
    if ni["sangou"]:
        natal_isouhou_display.append(f"三合会局")
        
    if natal_isouhou_display:
        print(f"宿命位相法: {' / '.join(natal_isouhou_display)}")
    print("")
    
    print("## 大運")
    gender_str = "男性" if dc['gender'] == 'm' else "女性"
    dir_str = "順回り" if dc['direction'] == 'Forward' else "逆回り"
    print(f"性別: {gender_str}, 回り: {dir_str}, 立運: {dc['start_age']}歳運\n")
    print("| 旬 | 年齢 | 干支 | 十大主星 | 十二大従星 | 天中殺 | 位相法 |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for p in result["taiun"]["periods"]:
        t_satsu = "天中殺" if p["is_tenchusaku"] else ""
        i_dict = p["isouhou"]
        i_parts = []
        if i_dict["vs_year"]: i_parts.append(f"年:{','.join(i_dict['vs_year'])}")
        if i_dict["vs_month"]: i_parts.append(f"月:{','.join(i_dict['vs_month'])}")
        if i_dict["vs_day"]: i_parts.append(f"日:{','.join(i_dict['vs_day'])}")
        if i_dict["sangou"]: i_parts.append("三合会局")
        i_str = f"{', '.join(i_parts)}" if i_parts else ""
        
        print(f"| {p['index']}旬 | {p['age_range']}歳 | {p['kanshi']['name']} | {p['judai_shusei']} | {p['junidai_jusei']} | {t_satsu} | {i_str} |")
    
    print("\n## 年運 (0歳〜99歳)")
    print("| 年齢 | 西暦 | 干支 | 十大主星 | 十二大従星 | 天中殺 | 位相法 |")
    print("| --- | --- | --- | --- | --- | --- | --- |")
    for p in result["nenun"]:
        t_satsu = "天中殺" if p["is_tenchusaku"] else ""
        i_dict = p["isouhou"]
        i_parts = []
        if i_dict["vs_year"]: i_parts.append(f"年:{','.join(i_dict['vs_year'])}")
        if i_dict["vs_month"]: i_parts.append(f"月:{','.join(i_dict['vs_month'])}")
        if i_dict["vs_day"]: i_parts.append(f"日:{','.join(i_dict['vs_day'])}")
        if i_dict["sangou"]: i_parts.append("三合会局")
        i_str = f"{', '.join(i_parts)}" if i_parts else ""
        
        print(f"| {p['age']}歳 | {p['year']}年 | {p['kanshi']['name']} | {p['judai_shusei']} | {p['junidai_jusei']} | {t_satsu} | {i_str} |")
    print("")
    print(f"  [詳細]")
    print(f"  有効年: {d['effective_year']}年")
    print(f"  直前の節入り: {d['sekki_name']} ({d['sekki_jst']})")
    print(f"  節入りからの経過日数: {d['elapsed_days']}日")
    print(f"  月支: {d['month_shi']} ({d['month_shi_idx']}番)")
    print(f"  年干支番号: {d['year_number']}番")
    print(f"  日干支番号: {d['day_number']}番")
    print("=" * 50)

if __name__ == "__main__":
    if len(sys.argv) >= 4:
        date_str = sys.argv[1]
        time_str = sys.argv[2]
        gender = sys.argv[3].lower()
        birth_str = f"{date_str} {time_str}"
    elif len(sys.argv) == 3:
        arg1 = sys.argv[1]
        arg2 = sys.argv[2].lower()
        if arg2 in ['m', 'f']:
            gender = arg2
            if " " in arg1:
                birth_str = arg1
            else:
                birth_str = f"{arg1} 12:00"
        else:
            birth_str = f"{sys.argv[1]} {sys.argv[2]}"
            gender = "m"
    elif len(sys.argv) == 2:
        birth_str = f"{sys.argv[1]} 12:00"
        gender = "m"
    else:
        print("引数不足: テストデータで実行します。")
        print("Usage: python main.py \"1996-08-12 14:30\" m\n")
        birth_str = "1996-08-12 14:30"
        gender = "f"
        
    result = calc_meishiki(birth_str, gender)
    
    import io
    from contextlib import redirect_stdout
    
    f_io = io.StringIO()
    with redirect_stdout(f_io):
        print_result(result, birth_str)
        
    md_str = f_io.getvalue()
    print(md_str, end="")
    
    json_dir = Path("jsonoutput")
    json_dir.mkdir(exist_ok=True)
    md_dir = Path("markdownoutput")
    md_dir.mkdir(exist_ok=True)
    
    safe_birth_str = birth_str.replace(" ", "_").replace(":", "")
    
    json_path = json_dir / f"{safe_birth_str}_{gender}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
        
    md_path = md_dir / f"{safe_birth_str}_{gender}.md"
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_str)
    
    print(f"\n[INFO] 詳細JSONデータを {json_path} に出力しました。")
    print(f"[INFO] Markdown形式の出力を {md_path} に保存しました。")
