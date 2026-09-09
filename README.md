# Elite Dangerous Journal Analyzer & Exploration Orrery (v0.0.5)

[日本語](#日本語) | [English](#english)

---

<a name="日本語"></a>
## 概要 (日本語)

Elite Dangerousのフライトジャーナルログ（`Journal.*.log`）を自動解析・リアルタイム監視し、過去に訪れた星系・天体の状態、位置関係・軌道情報、レア天体・特殊周回、着陸可否・重力・火山活動、Exobiology（植物・菌類）の生息予測と報酬額、FSS/DSS探査価値の精密計算、Rhino採掘支援（重力・温度表示）、天体ブックマーク・エイリアス・Markdownメモ、UIフォントサイズ実数値拡縮機能を提供するローカルデスクトップGUIアプリケーションです。

> **「あの時訪れたあの星は、どんな宙域だっただろう？」**  
> 銀河の遥かなる長旅の記録や、過去の深宇宙探索・初発見の思い出をいつでも鮮明に振り返ることができます。

> **⚠️ 使用上の注意・免責事項**: 本ツールはファンメイドの非公式オープンソースツールです。フロンティア・デベロップメンツ社とは一切関係ありません。ジャーナルログの解釈や探査・採掘データの完全性についてはいかなる保証も致しかねます。本ツールの使用によって生じたゲーム内での損失（機体喪失、採掘リグ耐久値損失、探査データ喪失など）を含むいかなる結果についても開発者は一切の責任を負いません。自己責任においてご利用ください。

### 🌐 日英バイリンガル対応 (One-Click Language Switch)
- アプリ画面右上の **`[JP] / [EN]`** ボタンから、日本語・英語をいつでも**ワンクリックで即座に切り替え可能**です。

### 💾 ポータブル設計 & 簡単アンインストール
- 本アプリは**レジストリやシステム領域への書き込みを一切行いません**。
- `ED_Journal_Analyzer.exe` を実行すると、実行ファイルと同じフォルダにデータベース保管用の **`data`** フォルダが自動生成されます。
- アンインストールしたい場合は、ダウンロードした **`ED_Journal_Analyzer.exe`** と **`data`** フォルダをそのまま手動で削除するだけで完全に削除されます。

### 主な機能 (Key Features)

- **UIフォントサイズ実数値拡縮機能 & セーフティ機構**:
  - 設定モーダルに「🖥️ 画面・文字サイズ」タブを新設。**18px**（標準中間サイズ）をデフォルトとし、最小目安 **14px** から任意のpx実数値を直接指定可能。
  - バッジやパネルが一列から自然に折り返され、文字数や情報を欠落させずに縦長にフィット。
  - 右上「⚙️ 設定」ボタンは常に最前面に固定表示され、極端な数値入力時でも <kbd>Ctrl + 0</kbd> で即座に標準 (18px) に復旧可能。
- **採掘支援 重力 (G)・温度 (K) 可視化 & 採掘パネル併記**:
  - 採掘ビューの天体カードにおいて、表面温度・大気欄に加えて **重力 (G)** も一行に並べて表示。
  - 採掘Rig耐久値管理に直結する重力 (G)・表面温度 (K) の表示トグルを左パネルに完備。
  - 星系カード最下段のLandableバッジは、左パネルでオンにした採掘フィルターに該当する天体のみがスマートに表示されるよう連動。
- **LIVE（リアルタイム）ボタンの配置最適化**:
  - 訪問期間プルダウンと1次ソートの間に配置換えし、押しやすい横幅と直感的な操作動線を実現。
  - ジャンプ到着待機（Honk待機）中であっても、LIVEボタンを押すことで即座に最新星系の現状データを閲覧可能。
- **天体ブックマーク・エイリアス（別名・通称）・Markdownメモ帳**:
  - 天体単位でのブックマーク登録、ユーザー定義通称（例: `採掘拠点 Alpha`, `TF候補1`）、Markdown形式メモ（リアルタイムプレビュー対応）。
  - 星系検索欄で、星系名だけでなく **「天体名」「エイリアス名」「メモ本文」を横断した全文検索** が可能。
  - フィルターチップ「🔖 ブックマーク」による登録天体星系の瞬時絞り込み。
- **5大銀河ランドマーク距離表示**:
  - CMDR現在地、Sol、Colonia、Rainbow's End (DW3)、Explorer's Anchorage (Sgr A*) からの直線距離（Ly）を星系カードおよびインスペクターに自動算出・表示。
- **星系 & 天体の過去ログ遡り・タイムライン**:
  - 過去に訪れた際のスキャン状況、訪問回数、ジャンプ距離・消費燃料・搭乗船ログの復元。
- **位置関係 & 軌道階層ツリー & System Map**:
  - 恒星・惑星・衛星の階層親子ツリー構造、連星系共通重心（Barycentre）、軌道長半径（AU / ls）、離心率、公転・自転周期、傾斜角、潮汐固定の可視化。
- **レア天体 & 特殊周回の自動検出 (Anomaly Detector)**:
  - ELW (地球型), WW (海洋惑星), Ammonia World, Terraformable, 高離心率 (e >= 0.8), 超短公転周期, 高速自転, 巨大リング等の自動タグ付け。
- **地表・着陸・重力 & 火山活動**:
  - 着陸可否 (Landable)、表面重力 (G値 & 着陸可能天体限定の高重力危険警告)、火山活動の種類・地質シグナル数。
- **Exobiology（植物・菌類）解析 & 報酬予測**:
  - 大気組成・表面温度・重力・天体種別から生息可能性のある植物/菌類候補（Stratum, Bacterium, Clypeus等）と通常報酬 + 初回採取5倍ボーナス額の算出。
  - サンプル採取に必要なコロニー間隔の表示。
- **探査価値精密計算**:
  - FSSスキャン価値、DSSマッピング価値（効率ボーナス含む）、初回発見ボーナス (x2.6)、初回マッピングボーナスを精密算出。
  - 星系ごとの「FSSスキャン合計」と「最大見込み（FD+FM）」の並列表示。
- **リアルタイム監視**:
  - ゲームプレイ中のジャーナル差分を自動検知して即座に画面へ反映。

### 起動方法

```powershell
# デスクトップGUIウィンドウとして起動
python run.py

# ブラウザで起動する場合
python run.py --browser
```

起動後、右上の「**ログ再スキャン (Rescan Logs)**」をクリックすると、全ジャーナルファイルが一括インデックス化されます。

---

<a name="english"></a>
## Overview (English)

A local desktop GUI application that automatically parses and monitors Elite Dangerous flight journals (`Journal.*.log`). It provides comprehensive exploration insights including historical system/body records, orbital hierarchy trees, rare celestial anomalies, surface gravity & volcanism, Exobiology habitat predictions & payouts, precise FSS/DSS exploration value calculations, Rhino SRV mining support (gravity & temperature toggles), celestial body bookmarks with custom aliases, and Markdown notes.

> **"What kind of world was that memorable planet I visited long ago?"**  
> Relive and explore your epic expedition memories, first discoveries, and galaxy travels anytime with complete offline privacy.

> **⚠️ Disclaimer**: This tool is an unofficial, fan-made open-source companion and is not affiliated with or endorsed by Frontier Developments plc. No warranties are provided regarding data accuracy or game log interpretation. The developer assumes no responsibility or liability for any in-game losses or damages (including loss of ships, mining rig durability, or exploration data). Use at your own discretion.

### 🌐 Instant Bilingual Support (JP / EN Switch)
- Switch seamlessly between **English** and **Japanese** at any time with a single click on the **`[JP] / [EN]`** toggle in the top-right corner.

### 💾 100% Portable & Clean Uninstall
- **Zero registry or system modifications**: Everything runs strictly in user space.
- Running `ED_Journal_Analyzer.exe` will create a local **`data`** directory in the same folder to store the SQLite database.
- To uninstall, simply delete the **`ED_Journal_Analyzer.exe`** file and the **`data`** folder. No uninstaller or leftover files.

### Key Features

- **UI Font Size Direct Numeric Scaling & Safety Reset**:
  - New "🖥️ Display & Font Size" tab in Settings. Set standard base font size (**18px** default recommended, **14px** minimum guidance) with direct numeric input for custom values.
  - Fluid responsive wrapping allows badges and cards to fold vertically without truncation or loss of critical information.
  - Always-on-top Settings button and emergency <kbd>Ctrl + 0</kbd> shortcut instantly restores the default standard 18px size.
- **Mining Support: Gravity (G) & Temperature (K) Display & Mining View Integration**:
  - Surface gravity ($G$) is displayed directly alongside temperature and atmosphere in the mining body cards.
  - Dedicated checkboxes to toggle surface gravity ($G$) and surface temperature ($K$) across all views.
  - System card bottom landable bar automatically synchronizes to display only bodies matching active mining filter chips.
- **Optimized LIVE (Real-time) Button Relocation**:
  - Relocated between the Visit Period dropdown and 1st Sort dropdown in the left pane for smooth navigation and visibility.
  - Easily dismisses Honk waiting screens to inspect current known star system data immediately.
- **Body Bookmarks, Custom Aliases & Markdown Notes**:
  - Bookmark individual celestial bodies, assign user-defined aliases (e.g. `Mining Base Alpha`), and keep rich Markdown notes with instant live preview.
  - Search across star systems, body names, custom aliases, and Markdown note contents simultaneously via the global search bar.
  - Filter chip for quick navigation to bookmarked systems (`🔖 Bookmarks`).
- **5 Key Galactic Landmark Distances**:
  - Instant distance calculations ($Ly$) to CMDR current location, Sol, Colonia, Rainbow's End (DW3), and Explorer's Anchorage (Sgr A*).
- **Exploration History & Flight Logs**:
  - Track scanned bodies, visit timestamps, jump distance, fuel used, and ship details for every visited system.
- **Orbital Hierarchy & Planetary Tree & System Map**:
  - Visual hierarchy tree of stars, planets, and moons with circumbinary barycentres, orbital semi-major axis (AU / ls), eccentricity, orbital/rotational periods, inclination, and tidal locking.
- **Celestial Anomaly & Rare Body Detector**:
  - Automatic detection of Earth-like Worlds (ELW), Water Worlds (WW), Ammonia Worlds, Terraformables, high orbital eccentricity ($e \ge 0.8$), ultra-short orbits, fast rotators, and giant rings.
- **Surface Conditions, Gravity & Volcanism**:
  - Landable indicator, precise surface gravity ($g$), dangerous High-G landing warnings (landable bodies only), volcanism type, and geological signals.
- **Exobiology Predictor & Vista Genomics Rewards**:
  - Predicts potential organic species (Stratum, Bacterium, Clypeus, Tubus, etc.) based on atmosphere composition, temperature, gravity, and planet class.
  - Displays standard payouts and $5\times$ First Discovery bonuses, along with minimum sample colony distances.
- **Exploration Payout Engine**:
  - Exact formula-based calculations for FSS scan values, DSS mapped values (including efficiency bonus), First Discovered ($2.6\times$), and First Mapped bonuses.
  - Side-by-side display of **FSS Scan Total** and **Max Potential (FD+FM)**.
- **Real-Time Journal Watcher**:
  - Lightweight background thread automatically detects new in-game journal entries and updates the UI live.

### Installation & Run

```powershell
# Clone the repository
git clone https://github.com/SuzuneYonaki/ED_Journal_Analyzer.git
cd ED_Journal_Analyzer

# Install dependencies
pip install -r requirements.txt

# Launch GUI App
python run.py

# Or launch in default web browser
python run.py --browser
```

Or simply download the pre-built standalone executable from [GitHub Releases](https://github.com/SuzuneYonaki/ED_Journal_Analyzer/releases).

---

## Credits & Acknowledgements

- **AI Assisted Development**: Developed with the assistance of AI (Google Antigravity / Gemini).
- **Game Data & Assets**: *Elite Dangerous* is a registered trademark of Frontier Developments plc.
- **Formulas & Science**: Payout calculations and Exobiology condition matrices are based on Frontier Developments specifications and ED community research (EDSM, Canonn Research, MattG).

---

## License

This project is licensed under the Apache License 2.0.
