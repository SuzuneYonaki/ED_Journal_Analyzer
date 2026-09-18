# Elite Dangerous Journal Analyzer & Exploration Orrery

[![Version](https://img.shields.io/badge/version-v0.8.1-orange.svg)](https://github.com/SuzuneYonaki/ED_Journal_Analyzer/releases)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)

[日本語](#日本語) | [English](#english)

---

<a name="日本語"></a>
## 概要 (日本語)

> 「FSSだけして過ぎ去ったあの星系は、どんな星系だっただろう？ いつ訪れただろう？」
> 
> FSSの奥に置き忘れてきた星々を、もう一度手のひらに。
> 
> かつて駆け抜けた宙域の記録を呼び覚ます、あなたの航路日誌です。
> 
> ジャーナルの奥底に眠っていた旅のログを掘り起こし、過去の探査履歴や観測データを鮮明に可視化します。

**Elite Dangerous Journal Analyzer** は、宇宙シミュレーションゲーム『Elite Dangerous』のフライトジャーナルログ（`Journal.*.log`）をリアルタイムに自動解析・監視し、星系構造の可視化、探査価値の精密算出、Exobiology（生体スキャン）予測、採掘支援、天体ブックマーク・メモ機能を提供する**ローカルファースト型デスクトップGUIアプリケーション**です。

---

### 🛡️ 設計思想：ローカルファースト & コミュニティ連携

- **完全ローカル完結・プライバシー保護**:
  フライトジャーナルログ、CMDRの航跡、所持金・搭乗船データ、天体メモ、ブックマーク等は、すべて**あなたのPC上のローカルSQLiteデータベースのみ**に保存されます。常時通信や強制アップロード、アカウント登録等は一切不要です。
- **コミュニティ知見のオンデマンド照会**:
  必要に応じて、EDSMやSpanshから天体物理データや環ホットスポット（Hotspots）、惑星採掘地点（PML）をオンデマンド照会・補完できます。未スキャン天体の公転軌道や価値を事前に把握可能です（未訪問星系にはエクスポート遮断等の安全ロック機構を完備）。
- **多彩な探査データ共有 (CMDR Data Share)**:
  自力で探査・観測した成果は、スタンドアロンHTML、観測データを内包したComfyUI方式PNGカード、Twitch/SNS向けテキスト短評として自由に外部へ共有・復元できます。

---

### 🚀 主な機能 (Core Features)

1. **リアルタイム・フライトログ解析 & 探査価値計算**:
   - ジャンプイン、Honk（FSS）、DSS、着陸、生体スキャンを完全自動トラッキング。
   - FSSスキャン価値、DSSマッピング価値（効率ボーナス含む）、初回発見ボーナス（×2.6）、初回マッピングボーナスを精密算出。
2. **多重連星系対応 Orrery & 軌道階層ツリー**:
   - 恒星・惑星・衛星の階層親子ツリー構造、多重連星系共通重心（Barycentre）、周連星惑星（`AB 1` 等）、周回恒星（`A 1`, `B 1` 等）、特殊命名天体（`Sagittarius A*`, `Founders World`, `Earth` 等）を正確な軌道順で描画。
   - 自由な拡大縮小（0.12x〜40x）・ドラッグ操作に対応したインタラクティブ星系儀（Orrery）。
3. **Exobiology（植物・菌類）解析 & 報酬予測**:
   - 大気組成・表面温度・重力・天体種別から生息可能性のある植物/菌類候補と通常報酬＋初回採取5倍ボーナス額を自動算出。規定の必要コロニー離隔距離（m）も常時表示。
4. **天体ブックマーク・エイリアス（別名）・Markdownメモ帳**:
   - 天体単位でのブックマーク登録、ユーザー定義通称（エイリアス）、リアルタイムプレビュー対応のMarkdownメモ。
   - 星系名・天体名・エイリアス名・メモ本文を対象とした高速グローバル検索。
5. **🤝 CMDR Data Share（3系統の探査データ共有・出力）**:
   - **🌐 Web共有HTML生成**: ワンクリックで単一の美しい星系図HTML（`exports/{星系名}_share.html`）を出力。外部通信なし・オフラインでブラウザ閲覧可能。天体観測JSONを完全内包。
   - **🖼️ 共有用画像生成**: 観測メタデータをPNGチャンクに埋め込んだ **ComfyUI方式サマリー画像カード** を出力。本アプリにドラッグ＆ドロップするだけで星系データを瞬時にインポート・復元可能。
   - **📋 星系短評投稿文**: 特殊軌道、地質、生体、環情報などの見どころをまとめたテキストをワンクリックでクリップボードへコピー。Twitch配信コメントやDiscord、X（旧Twitter）への投稿に最適。
6. **天体物理レア度スコア & 2014年天文学モデル査読**:
   - 軌道力学（ヒル球・ロッシュ限界・古在共鳴）やハビタブルゾーン（Kopparapu 2013）、質量分類（Weiss & Marcy 2014）に基づく天体物理レア度スコア（100点満点）の自動算出とサマリーレポート生成。
7. **地表・着陸・重力 & 採掘支援 (Rhino Mining Support)** ※デフォルトOFF:
   - 着陸可能天体（Landable）限定の高重力警告（3G+危険）、地質・火山活動シグナル。
   - EDSM天体データに基づく採掘有望度スコア判定（**⛏️ Scout: High / Med**）。
   - Spansh連携によるリングホットスポットおよび惑星採掘地点（PML）の自動照会。
   - 大型着艦パッド（Large Pad）装備ステーション保有星系・到達距離フィルター。
   - リング天体のDSSスキャン結果（ホットスポット）のMarkdownメモ自動記録、CMDR現在地座標のワンクリック挿入。
   - ※探査特化のため初期状態では非表示。設定モーダル（拡張機能モジュール表示設定）からいつでも有効化可能。
8. **モジュール表示の自由カスタマイズ**:
   - **Exobiology**、**Rhino採掘**、**星系人口・支配勢力/BGS** を設定画面から個別にON/OFF切り替え可能（デフォルトでは探査に特化し、採掘や勢力情報はOFF）。
9. **音声読み上げ通知 (TTS)**:
   - 新星系到着時の未発見（1st Discover）や高額生物天体（40M+ Cr）の発見を、音声合成（Web Speech API または ローカルVOICEVOX）で自動アナウンス。画面表示と音声通知は独立してON/OFF可能。
10. **UIカスタマイズ & 日英バイリンガル対応**:
    - **Modern Deep Space**、**Elite Classic Amber HUD**、**Cyan Explorer HUD** のテーマ切り替え。
    - 画面レイアウトの1列（標準）/ 2列（Orrery＋天体ツリー常時並列表示）切り替え。
    - UIフォントサイズの自由変更および緊急リセット（<kbd>Ctrl + 0</kbd>）。
    - 画面右上の **`[JP] / [EN]`** ボタンからいつでもワンクリックで全画面言語切替。

---

### 📖 使用方法 (Usage & Workflow)

#### 1. インストールと起動
- **配布パッケージ（推奨）**:
  [GitHub Releases](https://github.com/SuzuneYonaki/ED_Journal_Analyzer/releases) より最新の `ED_Journal_Analyzer_v0.8.1.zip`（または `ED_Journal_Analyzer.exe`）をダウンロードし、任意のフォルダに展開して実行します。
- **Pythonソースから実行**:
  ```powershell
  git clone https://github.com/SuzuneYonaki/ED_Journal_Analyzer.git
  cd ED_Journal_Analyzer
  pip install -r requirements.txt
  python run.py          # GUIアプリとして起動
  python run.py --browser # 既定のブラウザで起動
  ```

#### 2. 基本ワークフロー
1. **初回ログスキャン**: 起動後、画面右上の「**ログスキャン (Rescan Logs)**」をクリックして過去のフライトログをインデックスします。
2. **ゲームプレイ中の自動追跡**: *Elite Dangerous* を起動してプレイするだけで、ジャンプ・スキャン・着陸などの最新イベントがリアルタイムに画面へ反映されます。
3. **星系の閲覧**: 画面左側の星系リストから星系を選択してツリーやOrreryを表示します。

#### 3. 🤝 CMDR Data Share（探査データのエクスポートと共有）
星系ヘッダーの「**🤝 CMDR Data Share**」メニューから、用途に応じた3種類の形式でエクスポート・共有できます。

- **🌐 Web共有HTML生成**:
  - 単一の自己完結型HTMLファイル（`exports/{星系名}_share.html`）を出力します。
  - 外部サーバーやCDNに一切依存せず、オフライン環境のブラウザで軽快に全軌道Orreryや天体詳細を展開・閲覧可能。完全な天体観測JSONを内包しています。
- **🖼️ 共有用画像生成（PNG画像による星系データの共有）**:
  - ツール内で生成したPNG画像（`exports/{星系名}_summary.png`）には探査データがメタデータチャンク（`ed_journal_data`）として完全記録されています。
  - SNS等で配布・交換した画像を本ツールにドラッグ＆ドロップするだけで、他のCMDRが訪れた星系のデータを手軽に閲覧・復元できます。
  > [!WARNING]
  > **⚠️ 注意：探査データの取り扱いについて**  
  > Universal Cartographics（UC）へ売却が完了していない星系のPNG画像は、**絶対に第三者へ公開・共有しないでください**。  
  > 売却前に星系名や座標が漏洩した場合、他のCMDRに先に売却されてFirst Discovery（初回発見権利）や売却クレジットを喪失する恐れがあります。データ共有は必ずゲーム内で売却を済ませた後に行ってください。
- **📋 星系短評投稿文**:
  - 特殊軌道、地質、生体、環情報などの見どころをまとめたテキストをワンクリックでクリップボードへコピーします。Twitch配信コメントやDiscord、X（旧Twitter）への投稿に最適です。

#### 4. 応用的な使い方
- **ブックマーク & メモ**: 天体詳細パネルから「★ ブックマーク」やエイリアス名（例: `採掘拠点 Alpha`）、Markdown形式のメモを保存できます。
- **採掘スポット・地表座標の記録（Rhinoモジュール有効時）**:
  - リング天体をDSSスキャンすると、ホットスポット一覧が自動で天体メモに追記されます。
  - 着陸中にメモ欄右下の「📍 現在地座標挿入」を押すと、現在CMDRがいる緯度・経度が瞬時に挿入されます。
- **AI による星系の深層査読**:
  - 出力した Web 共有 HTML または 共有用PNG画像（内部に天体・軌道JSONを完全保持）を ChatGPT、Claude、Gemini 等にドラッグ＆ドロップし、下記の**天体物理リアリティチェック・プロンプト**を併用することで、星系の物理的実在性やハビタビリティの学術的検証レポートを生成できます。

#### 💾 ポータブル設計 & `data` フォルダの管理
- **レジストリ完全非依存**: すべての設定・インデックスデータ・メモ・ブックマークは、実行ファイルと同じ階層の `data/` フォルダ内に保存されます。
- **アップデート時**: 新バージョンへ移行する際は、**既存の `data/` フォルダをそのまま残し**、実行ファイル（またはソースコード）のみを上書きしてください。すべてのフライト履歴やメモが自動で引き継がれます。
- **アンインストール**: アプリ本体と `data/` フォルダを削除するだけで、PC環境を一切汚さず完全に消去できます。

---

<details>
<summary><b>🌌 天体物理学的実在妥当性チェック・プロンプト (for LLMs) を展開</b></summary>

<br>

本アプリケーションが出力する **Web共有HTML（`{星系名}_share.html`）** および **共有用PNG画像（`{星系名}_summary.png`）** には、星系内の全天体の完全な天体物理・軌道パラメータがJSON形式で埋め込まれています（HTML内 `<script id="ed-system-astrophysics-data" type="application/json">` または PNG内 `ed_journal_data` チャンク）。

このHTMLファイルまたはPNG画像（あるいは展開したJSON）を **ChatGPT、Claude、Gemini 等の生成AIにドラッグ＆ドロップで添付** し、以下のプロンプトを入力することで、現代の天体物理学・惑星科学の観点から厳密な実在妥当性チェックを行うことができます。

```text
添付したファイルは、宇宙シミュレーション『Elite Dangerous』で実際に観測・記録された星系の天体物理観測データです。

あなたには【天体物理学および比較惑星科学の専門家・学術査読者】として振る舞っていただきます。
本星系に含まれる恒星および全天体の物理量（質量・半径・密度・表面温度・光度・大気圧・組成比）および軌道要素（軌道長半径・離心率・公転周期・軌道傾斜角）を厳密に精査し、以下の5項目について専門的かつ論理的な分析レポートを作成してください。

---

### 1. 天体物理学的・力学的実在妥当性の総合判定 (Physical Reality Check)
- **判定結果**: 【実在可能】/【理論上は成立し得るが極めて稀】/【物理的矛盾（ゲーム的デフォルメ）】のいずれかを明示してください。
- **力学的安定性**:
  - ヒル球（Hill Sphere）および惑星間相互作用から見て、この軌道配置は数億年〜数十億年のタイムスケールで軌道共鳴や重力散乱を起こさずに安定して存続可能か（Gladman 1993等の軌道安定条件の観点）。
  - ロッシュ限界（Roche Limit）の内側に侵入して潮汐破壊されるべき天体が残存していないか。
  - 離心率と軌道長半径から見て、軌道交差や近点通過時の極端な潮汐加熱・潮汐破壊のリスクはないか。

### 2. 恒星放射・ハビタビリティ・大気の物理的整合性
- **平衡温度と大気保持**:
  - 主星・伴星の光度および天体の軌道距離から算出される平衡温度（Kopparapu 2013等のハビタブルゾーン計算）と、観測された表面温度・大気圧・温室効果の整合性。
  - 天体の脱出速度と熱運動速度（Jeans逃散の観点）から見て、この重力と温度下でその大気（水蒸気、アンモニア、メタン、希ガス等）を数十億年間保持し続けられるか。
- **地球型天体（ELW）/ 海洋惑星（WW）/ アンモニア天体の実在性**:
  - 該当する天体が存在する場合、その気圧・温度・主星スペクトル型の下で液体の水や液体アンモニアが地表に安定して存在し続けられるか。

### 3. プロシージャル生成の癖・ゲーム的デフォルメの指摘
- 現代天文学の観点から「自然界ではまずあり得ない、ゲームのプロシージャル生成特有の歪みやバグ、物理法則の簡略化」と思われる箇所を具体的に指摘してください。
- 逆に、「一見不自然に見えるが、物理理論上は奇跡的な条件が重なれば説明がつく現象（例: 超新星フォールバック円盤によるパルサー周囲の第二世代惑星形成、極端な離心率による周期的な潮汐加熱など）」があれば、その理論的根拠を提示してください。

### 4. 星系形成史シナリオの推論 (Formation & Evolution Narrative)
- もしこの星系が実在すると仮定した場合、主星の誕生から前駆星の進化、原始惑星系円盤（またはフォールバック円盤）からの微惑星集積、惑星移動（Migration）、軌道の真円化や潮汐固定に至るまでの時系列シナリオを天文学的に論理構築してください。

### 5. 地表・軌道上からの天球・景観描写 (Astronomical Landscape)
- 最も特徴的な天体（地球型天体、または極端な巨大リング天体・近接連星等）の地表または低軌道に人類の観測者が立った場合、肉眼や観測機器でどのような天球・空・景観が見えるかを、天文学的数値を踏まえてリアルに描写してください。

---

※お世辞や定型的な前置きは不要です。学術論文の査読コメントや専門的な探査フィールドノートのような、冷徹かつ論理的なトーンで記述してください。
```

</details>

---

---

<a name="english"></a>
## Overview (English)

> *"What was that star system really like—the one I just honked with FSS and flew right past? When did I visit?"*
> 
> Bringing the stars you left behind in the depth of FSS back into your hands.
> 
> This is your flight logbook, awakening the forgotten records of sectors you once traversed.
> 
> Unearthing journey logs sleeping deep within your flight journals, vividly visualizing your past exploration history and astronomical observations.

**Elite Dangerous Journal Analyzer** is a standalone, local-first desktop GUI application designed to parse and monitor *Elite Dangerous* flight journal logs (`Journal.*.log`) in real time. It offers orbital hierarchy visualization, precise exploration payout calculations, Exobiology predictions, mining reconnaissance, and celestial bookmarking/notes.

---

### 🛡️ Core Philosophy: Local-First & Community Connectivity

- **Strict Local-First & Privacy Protection**:
  Flight journal logs, CMDR travel histories, credit balances, current ship data, planetary notes, and bookmarks are stored **exclusively in a local SQLite database on your machine**. No persistent cloud communication, forced telemetry uploads, or account registrations are required.
- **On-Demand Community Intelligence**:
  When needed, you can query EDSM and Spansh on-demand to supplement astrophysical data, ring hotspots, and planetary mining locations (PML), enabling you to preview orbital elements and estimated values of unscanned bodies (with built-in export lockout and stat isolation for unvisited systems).
- **Rich CMDR Data Sharing (CMDR Data Share)**:
  Easily share and restore your exploration and observational discoveries via standalone Web HTML, ComfyUI-style PNG cards with embedded observation metadata, or short text summaries formatted for Twitch, Discord, and SNS.

---

### 🚀 Core Features

1. **Real-Time Journal Tracking & Exploration Payouts**:
   - Automated live tracking of system jumps, Honk (FSS), DSS mapping, surface landings, and bio-scans.
   - Exact payout calculation for FSS scans, DSS mapping (including efficiency bonus), First Discovery bonus (×2.6), and First Mapped bonus.
2. **Multi-Star Orrery & Orbital Hierarchy Tree**:
   - True parent-child hierarchy representing stellar barycentres, circumbinary planets (`AB 1`), circumstellar companion stars (`A 1`, `B 1`), and custom-named bodies (`Sagittarius A*`, `Founders World`, `Earth`, `Moon`).
   - Interactive system orrery with smooth continuous zoom (0.12x - 40x), drag pan, and stellar jump navigation.
3. **Exobiology Predictions & Reward Modeling**:
   - Predicts bio-genus candidates (Stratum, Bacterium, etc.) and calculates standard payouts plus 5x First Sampler bonuses based on atmosphere, surface temperature, gravity, and planet type. Displays required minimum colony distance (m).
4. **Celestial Bookmarks, Aliases & Markdown Notes**:
   - Bookmark celestial bodies, assign user aliases (e.g. `Mining Base Alpha`), and edit rich Markdown notes with live preview.
   - Lightning-fast global search across star systems, body names, custom aliases, and note contents.
5. **🤝 CMDR Data Share (3-Way Exploration Data Sharing & Export)**:
   - **🌐 Generate Web Share HTML**: Exports a single, self-contained HTML file (`exports/{System}_share.html`) with embedded astrophysical JSON that opens offline in any browser without external CDNs.
   - **🖼️ Generate Share PNG Image**: Exports a **ComfyUI-style summary image card** with observation metadata embedded into PNG chunks. Simply drag-and-drop the image back into the application window to instantly import and inspect the system.
   - **📋 System Summary Post Text**: Generates and copies a concise textual summary highlighting orbital wonders, geology, biology, and rings to your clipboard—perfect for Twitch chat, Discord, or X (Twitter).
6. **Astrophysical Rarity Score & 2014 Astronomical Peer-Review**:
   - Automatic calculation of an astrophysical rarity score (0-100) and summary report based on orbital dynamics (Hill spheres, Roche limits, Kozai resonances), habitable zone models (Kopparapu 2013), and mass classification (Weiss & Marcy 2014).
7. **Surface Landing, Gravity & Rhino Mining Support** (Disabled by default):
   - Extreme gravity danger warnings exclusively on landable worlds (3G+ hazard); surface volcanism and geological signals.
   - High-value mining reconnaissance rating (**⛏️ Scout: High / Med**) powered by EDSM telemetry.
   - Automatic query of ring hotspots and planetary mining locations (PML) via Spansh integration.
   - Filtering for systems hosting stations with Large Landing Pads within configurable arrival distance thresholds.
   - Automated DSS ring hotspot markdown logging and one-click CMDR surface coordinate insertion.
   - *Disabled by default to focus on pure exploration. Can be enabled anytime in Settings (Extension Modules).*
8. **Customizable Module Toggles**:
   - Individually toggle **Exobiology**, **Rhino Mining**, and **Faction & Population (BGS)** modules in the settings modal (focused on pure exploration by default with mining and faction modules turned off).
9. **Text-to-Speech Audio Alerts (TTS)**:
   - Voice announcements for First Discoveries upon system arrival and high-value exobiology bodies (40M+ Cr) using Web Speech API or local VOICEVOX. Visual alerts and audio announcements can be toggled independently.
10. **UI Customization & Instant Bilingual Support**:
    - Switchable themes: **Modern Deep Space**, **Elite Classic Amber HUD**, and **Cyan Explorer HUD**.
    - Flexible layout switching between 1-column (standard) and 2-column (parallel Orrery + hierarchy tree).
    - Adjustable font size (numeric px input) with instant reset (<kbd>Ctrl + 0</kbd>).
    - Instant language switching via the **`[JP] / [EN]`** button.

---

### 📖 Usage & Workflow

#### 1. Installation & Launch
- **Pre-built Executable (Recommended)**:
  Download the latest `ED_Journal_Analyzer_v0.8.1.zip` (or `ED_Journal_Analyzer.exe`) from [GitHub Releases](https://github.com/SuzuneYonaki/ED_Journal_Analyzer/releases), extract to any folder, and double-click to run.
- **Run from Source**:
  ```powershell
  git clone https://github.com/SuzuneYonaki/ED_Journal_Analyzer.git
  cd ED_Journal_Analyzer
  pip install -r requirements.txt
  python run.py          # Run desktop GUI
  python run.py --browser # Run in default browser
  ```

#### 2. Basic Workflow
1. **Initial Indexing**: Click **Rescan Logs** in the top-right corner to index your flight history.
2. **Live Tracking**: Launch and play *Elite Dangerous*; the app automatically reflects new events in real time.
3. **System Browsing**: Select a star system from the left panel to inspect its tree and Orrery.

#### 3. 🤝 CMDR Data Share (Exporting & Sharing Exploration Data)
From the **🤝 CMDR Data Share** dropdown menu in the system header, export and share data in three convenient formats:

- **🌐 Generate Web Share HTML**:
  - Exports a single, self-contained HTML file (`exports/{System}_share.html`).
  - Opens offline in any web browser without relying on external servers or CDNs. Complete celestial observation JSON is embedded inside.
- **🖼️ Generate Share PNG Image (Sharing System Data via PNG Image Card)**:
  - Generates a summary PNG image card (`exports/{System}_summary.png`) embedding complete observation data inside a metadata chunk (`ed_journal_data`).
  - Simply drag and drop any shared PNG card into the application window to decode and restore the system survey instantly.
  > [!WARNING]
  > **⚠️ Caution: Handling Exploration Data Before UC Turn-in**  
  > Never publish or share PNG summary cards of star systems that have not yet been sold to **Universal Cartographics (UC)**.  
  > If system names or coordinates leak before sale, other CMDRs might reach UC first, causing you to lose your First Discovery rights and payout bonuses. Always sell your exploration data in-game before sharing!
- **📋 System Summary Post Text**:
  - Copies a concise summary of orbital wonders, geology, biology, and ring features to your clipboard with a single click—ideal for Twitch chat, Discord, or X (Twitter).

#### 4. Advanced Features
- **Bookmarks & Notes**: Open body details to bookmark, set custom aliases (e.g. `Mining Base Alpha`), or write Markdown notes.
- **Mining Hotspots & Surface Coordinates (When Rhino module enabled)**:
  - Scanning rings with DSS automatically appends detected hotspots into the body note.
  - While landed, click "📍 現在地座標挿入" (Insert Coordinates) in the note editor to stamp your exact planetary coordinates.
- **AI-Powered System Audit**:
  - Drag and drop your exported Web Share HTML or Share PNG Image (both embed complete astrophysical & orbital JSON) into ChatGPT, Claude, or Gemini alongside the **Astrophysical Reality Check Prompt** below to generate an in-depth scientific peer review.

#### 💾 Portable Architecture & `data` Directory
- **Zero Registry Footprint**: All database indexes, notes, and preferences reside locally inside the `data/` directory next to the executable.
- **Upgrading**: When updating to a newer release, **preserve your existing `data/` folder**. Simply overwrite the executable or update the code; all records migrate seamlessly.
- **Uninstallation**: Delete the application executable and the `data/` folder to completely remove all traces from your system.

---

<details>
<summary><b>🌌 Expand Astrophysical Reality Check Prompt (for LLMs)</b></summary>

<br>

Both the **Web Share HTML (`{System}_share.html`)** and the **Share PNG Image (`{System}_summary.png`)** exported by this application embed complete astrophysical and orbital parameters in JSON format (inside the `<script id="ed-system-astrophysics-data" type="application/json">` block in HTML, or the `ed_journal_data` chunk in PNG).

Pass either the HTML file or the PNG image (or the raw JSON) to **ChatGPT, Claude, or Gemini** using the prompt below:

```text
The attached file contains observational and orbital telemetry from a star system recorded in the space simulator Elite Dangerous.

Please act as a rigorous peer-reviewer and expert in astrophysics and comparative planetary science.
Critically evaluate the physical quantities (stellar/planetary mass, radius, density, effective temperature, luminosity, atmospheric pressure, chemical composition) and orbital elements (semi-major axis, eccentricity, orbital period, inclination) of every celestial body in this system, and provide a structured scientific report addressing the following five sections:

---

### 1. Physical Reality & Dynamical Stability Audit
- **Verdict**: State clearly whether this system configuration is [Physically Plausible] / [Theoretically Possible but Extremely Rare] / [Physical Contradiction (Procedural Generation Artifact)].
- **Dynamical Stability**:
  - Based on Hill spheres and mutual orbital spacing (e.g. Gladman 1993 stability criteria), can this orbital architecture survive for gigayears without orbital resonances or gravitational scattering?
  - Are there any bodies orbiting dangerously close to or within the Roche limit that should have been tidally disrupted?
  - Does high orbital eccentricity cause extreme periastron tidal heating or orbital crossing hazards?

### 2. Stellar Flux, Habitability & Atmospheric Consistency
- **Equilibrium Temperature & Gas Retention**:
  - Compare the calculated equilibrium temperature (Kopparapu et al. 2013 habitable zone models) against observed surface temperatures, greenhouse factors, and pressures.
  - Using planetary escape velocity and thermal velocity (Jeans escape), can these bodies retain their observed atmospheres (H2O, NH3, CH4, noble gases, etc.) over billions of years?
- **Earth-Like / Water World / Ammonia World Plausibility**:
  - If such worlds are present, can liquid water or liquid ammonia exist stably on their surfaces given the stellar spectral type and atmospheric pressure?

### 3. Procedural Artifacts vs. True Astronomical Wonders
- Identify specific aspects that are physically impossible in nature and represent procedural generation glitches or video game simplifications.
- Conversely, highlight features that appear bizarre at first glance but are theoretically explainable through rare astrophysical phenomena (e.g. supernova fallback disks around pulsars, tidal circularization, Kozai-Lidov cycles).

### 4. Stellar History & Evolutionary Narrative
- Assuming this system exists in reality, reconstruct a chronological evolutionary scenario: stellar birth and primary evolution, protoplanetary disk formation, planetary migration, capture, and long-term tidal locking.

### 5. Ground & Orbital Landscape Description
- Provide a vivid, scientifically grounded description of the sky and celestial vistas as seen by a human observer standing on the surface (or in low orbit) of the most remarkable world in this system (e.g. parent stars, companion binaries, immense planetary rings, or nearby moons).

---

Note: Please avoid boilerplate pleasantries and maintain an objective, academic tone consistent with a scientific peer-review critique or planetary exploration field report.
```

</details>

---

## Credits & Acknowledgements

- **AI Assisted Development**: Developed with the assistance of AI (Google DeepMind / Antigravity / Gemini).
- **Game Data & Assets**: *Elite Dangerous* is a registered trademark of Frontier Developments plc.
- **Formulas & Science**: Exploration payouts, planetary physics models, and Exobiology condition matrices are based on Frontier Developments specifications and ED community research (EDSM, Canonn Research, MattG).

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**.

> [!NOTE]
> **License Transition Notice (v0.8.1)**:
> Starting from version **0.8.1**, the project license has transitioned from Apache 2.0 to **GNU General Public License v3.0 (GPLv3)** to protect open-source integrity, prevent proprietary lock-in / closed-source forks, and guarantee that all derived enhancements remain free and open to the Elite Dangerous community.

