"""
Astrophysical Anomaly & Narrative Report Japanese Translation Service.
Provides deterministic, rule-based bidirectional translation between English and Japanese
for astrophysical findings, everyday scale analogies, and narrative reports.
Adheres to Zero Speculation & SSOT guidelines without external LLM dependencies.
"""

from __future__ import annotations

import re
from typing import List, Optional

# Terminology mappings for everyday analogies and astrophysics concepts
ANALOGY_TRANSLATIONS = [
    # Distance analogies
    ("extreme close-in orbit, far closer than Mercury", "水星軌道よりも遥かに恒星に近い極超至近軌道"),
    ("comparable to Mercury's orbit", "水星の公転軌道に匹敵する至近距離"),
    ("similar to Earth-Sun distance (1 AU)", "地球-太陽間の距離 (1 AU) に類似"),
    ("comparable to Mars's orbit", "火星の公転軌道に匹敵"),
    ("comparable to Jupiter's orbit", "木星の公転軌道に匹敵"),
    ("comparable to Saturn's cold orbit", "土星の極寒軌道に匹敵"),
    ("AU from host", "AU (主星からの距離)"),
    ("from host; pair orbit:", "主星からの距離; ペア公転軌道:"),
    ("pair orbit:", "連星/ペア公転軌道:"),
    
    # Stellar Temperature evaluations (relative to spectral classification)
    ("cooling remnant state for a neutron star", "中性子星残骸としては冷却が進んだ極低温状態"),
    ("typical high-energy X-ray surface temperature for neutron star", "中性子星の標準的X線放射表面温度"),
    ("ultra-hot young energetic neutron star", "超高温・極めて若い高エネルギー中性子星"),
    ("very hot young white dwarf", "極超高温の若年性白色矮星"),
    ("standard cooling regime for white dwarf", "白色矮星の標準的冷却温度"),
    ("cool degenerate white dwarf", "冷却が進んだ晩期白色矮星"),
    ("hotter regime for M-class red dwarf (early M-type, high activity)", "M型赤色矮星としては高温（早期型M・高活動性）"),
    ("typical temperature for M-class red dwarf", "M型赤色矮星の標準的有効温度"),
    ("very cool regime for M-class dwarf (late M-type, ultra-low luminosity)", "M型赤色矮星としては低温（晩期型M・極超低光度）"),
    ("warm regime for K-class orange dwarf", "K型橙色矮星としては高温寄り"),
    ("typical temperature for K-class orange dwarf", "K型橙色矮星の標準的有効温度"),
    ("cool regime for K-class dwarf", "K型橙色矮星としては低温寄り"),
    ("solar-analog standard effective temperature", "太陽型恒星の標準的ソーラー有効温度"),
    ("hotter regime for G-class star", "G型恒星としては高温寄り"),
    ("cooler regime for G-class star", "G型恒星としては低温寄り"),
    ("standard effective temperature for F-class yellow-white star", "F型黄白色恒星の標準的有効温度"),
    ("hot luminous A-class white star", "高温・高光度のA型白色主系列星"),
    ("intense luminous blue star with high UV flux", "強烈な紫外線放射を放つ高光度B型青色星"),
    ("extreme hyper-luminous blue star", "極限的な超高光度O型青色超巨星"),
    ("sub-stellar brown dwarf cooling regime", "核融合限界下の褐色矮星・冷却準恒星"),

    # Planetary Temperature analogies
    ("reaching stellar interior / nuclear core temperatures", "恒星内部・核融合炉心レベルの超高温に到達"),
    ("hot enough to melt basalt and liquidate rock", "玄武岩を融解させ岩石を液状化させるほどの超灼熱"),
    ("warm, comparable to a hot desert summer", "温暖（地球の猛暑砂漠と同等）"),
    ("temperate, hospitable Earth-like climate", "温暖・生命居住に適した地球型気候"),
    ("deep cryogenic freeze, far colder than Antarctica", "極低温凍結環境（南極を遥かに下回る極寒）"),
    
    # Atmospheric pressure analogies
    ("immense crushing pressure; equal to deepest ocean trench floor", "超深度海底（マリアナ海溝最深部）に匹敵する猛烈な超高圧"),
    ("dense supercritical atmospheric crushing zone", "超臨界流体化する超濃厚大気圧破砕帯"),
    ("comparable to high mountain air at ~2,500m / 8,200ft", "標高約2,500mの山岳地帯と同等の希薄大気"),
    ("standard Earth sea-level breathing pressure", "地球の海抜0mと同等の標準呼吸気圧"),
    ("near-vacuum thin stratosphere", "成層圏上層〜宇宙空間に近い超希薄・準真空大気"),
    
    # Scale/Radius analogies
    ("~the size of a metropolitan city center / Manhattan", "大都市中心部・マンハッタン島規模"),
    ("giant planet scale", "巨大惑星スケール"),
    ("massive Super-Earth scale", "巨大地球型惑星 (メガ/スーパーアース) スケール"),
    ("standard terrestrial scale", "標準地球サイズ"),
    ("Mars-like or large moon scale", "火星または大型衛星サイズ"),
    ("small asteroid/moon scale", "小惑星または小型衛星サイズ"),
    ("x Solar radius", "倍の太陽半径"),
    ("x Earth radius", "倍の地球半径"),
    ("x Earth size", "倍の地球サイズ"),
    ("x Solar luminosity", "倍の太陽光度"),
]

# Section header translations
HEADER_TRANSLATIONS = [
    ("ASTROPHYSICAL EXPLORATION REPORT:", "天体物理・探査レポート:"),
    ("Rarity Score:", "天体物理レア度スコア:"),
    ("Galactic Sector :", "銀河セクター:"),
    ("from Sag A*", "Sagittarius A* (中心特異点) より"),
    ("[EXECUTIVE SUMMARY]", "【総合サマリー / 概況】"),
    ("[PRIMARY STELLAR ENGINE]", "【主星・恒星放射エンジン】"),
    ("[HABITABLE WORLDS (FAMILIAR SCALE BREAKDOWN)]", "【居住可能天体 (親しみやすい尺度での比較)】"),
    ("[DETECTED ASTROPHYSICAL ANOMALIES]", "【検出された天体物理特異点】"),
    ("Earth-like World", "地球型惑星 (ELW)"),
    ("Body:", "天体:"),
    ("Scale:", "物理規模:"),
    ("Effective Heat:", "実効温度:"),
    ("Radiative Flux:", "放射流束:"),
    ("Orbital Distance :", "公転軌道距離:"),
    ("Physical Radius  :", "物理半径:"),
    ("Surface Climate  :", "表面気候:"),
    ("Air Pressure     :", "大気圧:"),
    ("Tilted View      :", "軌道傾斜角:"),
    ("deg inclination", "度の傾斜角"),
]

def translate_anomaly_to_ja(anomaly_en: str) -> str:
    """Translates an English anomaly description string into Japanese."""
    text = anomaly_en.strip()

    # Galactic context
    m = re.match(r"Galactic Halo system \(height=([\d\.]+) ly above plane, Population II / low-metallicity regime\)", text)
    if m:
        return f"銀河ハロー星系 (銀河円盤から高度 {m.group(1)} ly、種族II / 低重元素天体領域)"

    m = re.match(r"Galactic Central Bar / Bulge proximity \(dist_SagA=([\d\.]+) ly, extreme stellar density zone\)", text)
    if m:
        return f"銀河バルジ・中心棒状構造至近 (Sag A*から {m.group(1)} ly、超高密度恒星密集領域)"

    # Stellar remnant
    if text.startswith("Exotic stellar remnant detected:"):
        remnants = text.replace("Exotic stellar remnant detected:", "").strip()
        remnants_ja = remnants.replace("Neutron Star", "中性子星") \
                              .replace("Black Hole", "ブラックホール") \
                              .replace("Supermassive Black Hole", "超大質量ブラックホール") \
                              .replace("Wolf-Rayet", "ウォルフ・ライエ星") \
                              .replace("White Dwarf", "白色矮星")
        return f"特殊恒星残骸/高密度天体を検出: {remnants_ja}"

    m = re.match(r"High-order multiple stellar system with (\d+) stars", text)
    if m:
        return f"極めて高次の連星系 ({m.group(1)} 連星)"

    m = re.match(r"Hierarchical triple/multiple stellar system \((\d+) stars\)", text)
    if m:
        return f"階層型多重連星系 ({m.group(1)} 連星)"

    # Close binary relative to size
    m = re.match(r"Close binary relative to body size: (.+) & (.+) \(separation=([\d\.]+) km, combined radius=([\d\.]+) km, ratio=([\d\.]+)\)", text)
    if m:
        return f"天体規模に比して極超接近した連星: {m.group(1)} & {m.group(2)} (主星間距離={m.group(3)} km, 合計半径={m.group(4)} km, 半径比={m.group(5)})"

    # Eccentricity
    m = re.match(r"Extreme orbital eccentricity on (.+) \(e=([\d\.]+)\) indicating dynamic scattering or capture", text)
    if m:
        return f"{m.group(1)} に極端な軌道離心率を検出 (e={m.group(2)}: 重力散乱または捕獲を示唆)"

    m = re.match(r"High orbital eccentricity on (.+) \(e=([\d\.]+)\)", text)
    if m:
        return f"{m.group(1)} に高離心率軌道を検出 (e={m.group(2)})"

    # Orbital Period
    m = re.match(r"Ultra-short orbital period on (.+) \(P=([\d\.]+) h\) at extreme stellar proximity", text)
    if m:
        return f"{m.group(1)} に極超短公転周期を検出 (P={m.group(2)} 時間: 恒星極至近距離)"

    m = re.match(r"Very short orbital period on (.+) \(P=([\d\.]+) h\)", text)
    if m:
        return f"{m.group(1)} に極短公転周期を検出 (P={m.group(2)} 時間)"

    # Inclination
    m = re.match(r"Retrograde orbit detected on (.+) \(inclination=([\d\.-]+) deg\)", text)
    if m:
        return f"{m.group(1)} に逆行軌道を検出 (軌道傾斜角={m.group(2)}°)"

    m = re.match(r"Orthogonal/polar orbit detected on (.+?)(?: relative to system reference plane)? \(inclination=([\d\.-]+) deg\)", text)
    if m:
        return f"天体 {m.group(1)}: 星系基準軌道面に対して直交する極軌道を検出 (軌道傾斜角={m.group(2)}°)"

    # Roche limit
    m = re.match(r"Critical tidal stress: (.+) periapsis \(([\d\.]+) Mm\) within fluid Roche limit of (.+) \(ratio=([\d\.]+)\)", text)
    if m:
        return f"破滅的潮汐応力: {m.group(1)} の近点距離 ({m.group(2)} Mm) が {m.group(3)} の流体ロシュ限界内 (比率={m.group(4)})"

    m = re.match(r"High tidal deformation zone: (.+) orbits close to fluid Roche limit of (.+) \(ratio=([\d\.]+)\)", text)
    if m:
        return f"強潮汐変形帯: {m.group(1)} が {m.group(2)} の流体ロシュ限界近傍を周回 (比率={m.group(3)})"

    # Close orbit
    m = re.match(r"Close Orbit: (.+) orbits at extreme proximity to (.+) \(periapsis=([\d\.]+) km, parent radius=([\d\.]+) km, ratio=([\d\.]+)\)", text)
    if m:
        return f"至近周回軌道: {m.group(1)} が {m.group(2)} の表面近傍を極限周回 (近点={m.group(3)} km, 主星半径={m.group(4)} km, 半径比={m.group(5)})"

    # Small object
    m = re.match(r"Small Object: (.+) has exceptionally small radius \(([\d\.]+) km\)", text)
    if m:
        return f"極小天体: {m.group(1)} は極めて微小な天体半径 ({m.group(2)} km)"

    # Wide Ring
    m = re.match(r"Wide Ring: (.+) \[(.+)\] width is ([\d\.]+) Mm \(([\d\.]+)x body radius\)", text)
    if m:
        return f"超巨大環: {m.group(1)} [{m.group(2)}] の環の幅は {m.group(3)} Mm (天体半径の {m.group(4)} 倍)"

    # Nested Moon
    m = re.match(r"Nested Moon: (.+) orbits moon (.+), which orbits planet (.+)", text)
    if m:
        return f"多重衛星 (孫衛星): {m.group(1)} は衛星 {m.group(2)} を周回 (惑星 {m.group(3)} の外郭)"

    # Shepherd Moon
    m = re.match(r"Shepherd Moon: (.+) orbits within or grazing rings of (.+) \(a=([\d\.]+) Mm, ring=\[([\d\.-]+)\] Mm\)", text)
    if m:
        return f"羊飼い衛星: {m.group(1)} が {m.group(2)} の環の内側または境界線を掠めて周回 (軌道長半径={m.group(3)} Mm, 環の範囲=[{m.group(4)}] Mm)"

    # Close belt
    m = re.match(r"Close belt proximity: (.+) orbits in close proximity to (.+) of (.+)", text)
    if m:
        return f"小惑星帯至近軌道: {m.group(1)} が {m.group(3)} の {m.group(2)} の直近を周回"

    # Fast rotation
    m = re.match(r"Non-locked body with fast rotation: (.+) \(rot_period=([\d\.]+) h, locked=(.+)\)", text)
    if m:
        return f"自転・公転非同期の超高速自転天体: {m.group(1)} (自転周期={m.group(2)} 時間, 潮汐固定={m.group(3)})"

    # Exotic planetary host
    m = re.match(r"Exotic planetary system: (.+) orbits remnant/exotic star (.+) \((.+)\)", text)
    if m:
        st_desc = m.group(3).replace("N", "中性子星").replace("H", "ブラックホール")
        return f"特異残骸周回系: {m.group(1)} が高密度残骸/特殊恒星 {m.group(2)} ({st_desc}) を周回"

    # Habitable world anomalies
    m = re.match(r"Earth-like World (.+) exhibits atypical thermal equilibrium \(T=([\d\.]+) K\)", text)
    if m:
        return f"地球型惑星 {m.group(1)} が特異な熱平衡状態を示す (表面温度={m.group(2)} K)"

    m = re.match(r"Earth-like World (.+) with extreme atmospheric pressure \(([\d\.]+) atm\)", text)
    if m:
        return f"地球型惑星 {m.group(1)} に極端な大気圧を検出 ({m.group(2)} atm)"

    # Kopparapu Habitable zone
    m = re.match(r"(.+) confirmed in conservative Habitable Zone \(Kopparapu 2013, S_eff=([\d\.]+)\)", text)
    if m:
        return f"{m.group(1)} は保守的ハビタブルゾーン（生命居住可能領域）内に位置することを確認 (Kopparapu 2013, 実効流束 S_eff={m.group(2)})"

    m = re.match(r"Life-bearing body (.+) outside Kopparapu \(2013\) Habitable Zone \(S_eff=([\d\.]+); anomalous radiative equilibrium\)", text)
    if m:
        return f"生命保持天体 {m.group(1)} が Kopparapu (2013) の標準生命居住可能域を逸脱 (S_eff={m.group(2)}: 異常な放射平衡状態)"

    # Gladman Hill instability
    m = re.match(r"Critical Hill instability: (.+) & (.+) \(Delta_H=([\d\.]+) < ([\d\.]+) Gladman limit; chaotic scattering imminent\)", text)
    if m:
        return f"破滅的ヒル不安定性: {m.group(1)} と {m.group(2)} (相互ヒル半径比 Delta_H={m.group(3)} < Gladman限界 {m.group(4)}: 軌道交差・カオス的散乱の危機)"

    # Kozai-Lidov
    m = re.match(r"Kozai-Lidov secular resonance on (.+) by companion (.+) \(inc=([\d\.]+) deg, theoretical e_max=([\d\.]+)\)", text)
    if m:
        return f"古在-リドフ長期共鳴: 伴星 {m.group(2)} の摂動により {m.group(1)} が共鳴状態 (傾斜角={m.group(3)}°, 理論最大離心率 e_max={m.group(4)})"

    # Weiss & Marcy 2014 Composition
    m = re.match(r"Mega-Earth anomaly: (.+) \(R=([\d\.]+) R_Earth > 1.6, density=([\d\.]+) g/cm\^3; Weiss & Marcy 2014 transition\)", text)
    if m:
        return f"メガ・アース特異点: {m.group(1)} (半径={m.group(2)} 地球半径 > 1.6, 密度={m.group(3)} g/cm³: Weiss & Marcy 2014 岩石-気体遷移境界突破)"

    m = re.match(r"Super-Mercury mantle stripping: (.+) \(density=([\d\.]+) g/cm\^3 > 8.0 g/cm\^3\)", text)
    if m:
        return f"スーパー・マーキュリー (マントル剥奪): {m.group(1)} (超高密度={m.group(2)} g/cm³ > 8.0 g/cm³: 巨大衝突等による外層喪失)"

    m = re.match(r"Puffy low-density terrestrial body: (.+) \(density=([\d\.]+) g/cm\^3 < 1.5 g/cm\^3\)", text)
    if m:
        return f"パフィー超低密度地球型天体: {m.group(1)} (密度={m.group(2)} g/cm³ < 1.5 g/cm³: 揮発性物質過多の多孔質構造)"

    # Fallback to dictionary replacements
    for en_sub, ja_sub in ANALOGY_TRANSLATIONS:
        text = text.replace(en_sub, ja_sub)
    return text


def translate_narrative_report_to_ja(report_en: str) -> str:
    """Translates the full narrative astrophysical exploration report into Japanese."""
    if not report_en:
        return ""

    lines = report_en.split("\n")
    translated_lines: List[str] = []

    for line in lines:
        s = line
        
        # Check if line is anomaly in the summary section
        m_anom = re.match(r"^(\s*\[\d+\]\s*)(.+)$", s)
        if m_anom:
            prefix = m_anom.group(1)
            anom_text = m_anom.group(2)
            translated_lines.append(f"{prefix}{translate_anomaly_to_ja(anom_text)}")
            continue

        # Header replacements
        for en_h, ja_h in HEADER_TRANSLATIONS:
            s = s.replace(en_h, ja_h)

        # Analogy replacements
        for en_a, ja_a in ANALOGY_TRANSLATIONS:
            s = s.replace(en_a, ja_a)

        # Executive summary narrative lines
        m_exec = re.match(r"^A profound astronomical anomaly featuring (\d+) star\(s\) and (\d+) planetary body/bodies\.$", s)
        if m_exec:
            s = f"恒星 {m_exec.group(1)} 個、惑星・衛星 {m_exec.group(2)} 個で構成される、極めて特異な天体物理学的アノマリー星系です。"

        m_coexist = re.match(r"^Extraordinary coexistence: (\d+) Earth-like habitable world\(s\) thriving within an exotic stellar graveyard \((.+)\)\.$", s)
        if m_coexist:
            graveyard_ja = m_coexist.group(2).replace("Neutron Star", "中性子星").replace("Black Hole", "ブラックホール")
            s = f"驚異的な共存現象: 高密度恒星残骸の墓場 ({graveyard_ja}) の只中に、{m_coexist.group(1)} 個の地球型生命居住可能惑星が息づいています。"

        m_std = re.match(r"^Standard stellar system survey with (\d+) star\(s\) and (\d+) scanned planetary bodies\.$", s)
        if m_std:
            s = f"恒星 {m_std.group(1)} 個およびスキャン済み惑星・天体 {m_std.group(2)} 個からなる標準的な星系サーベイ結果です。"

        translated_lines.append(s)

    return "\n".join(translated_lines)


def translate_anomalies_list_to_ja(anomalies_en: List[str]) -> List[str]:
    """Translates a list of English anomalies into Japanese."""
    return [translate_anomaly_to_ja(a) for a in anomalies_en]
