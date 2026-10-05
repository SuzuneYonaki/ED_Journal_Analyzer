# Elite Dangerous Journal Analyzer & Exploration Orrery

[![Version](https://img.shields.io/badge/version-v0.8.23-orange.svg)](https://github.com/SuzuneYonaki/ED_Journal_Analyzer/releases)
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

v0.8.15 より、EDSM/Spansh連携・TTS音声読み上げ・探査データ共有・天体物理レア度スコア・生体種予測といった主要機能は、それぞれ独立した**アドオン**として実装されました。初期状態ではすべて無効化されており、必要な機能だけを設定画面から選んで有効化する、軽量かつプライバシー重視の運用が可能です。

---

### 🛡️ 設計思想：ローカルファースト & コミュニティ連携

- **完全ローカル完結・プライバシー保護**:
  フライトジャーナルログ、CMDRの航跡、所持金・搭乗船データ、天体メモ、ブックマーク等は、すべて**あなたのPC上のローカルSQLiteデータベースのみ**に保存されます。常時通信や強制アップロード、アカウント登録等は一切不要です。
- **コミュニティ知見のオンデマンド照会**:
  必要に応じて、EDSMやSpanshから天体物理データや環ホットスポット（Hotspots）、惑星採掘地点（PML）をオンデマンド照会・補完できます。未スキャン天体の公転軌道や価値を事前に把握可能です（未訪問星系にはエクスポート遮断等の安全ロック機構を完備）。
- **多彩な探査データ共有 (CMDR Data Share)**:
  自力で探査・観測した成果は、スタンドアロンHTML、観測データを内包したComfyUI方式PNGカード、Twitch/SNS向けテキスト短評として自由に外部へ共有・復元できます。
- **アドオンによる機能の取捨選択 (New in v0.8.15)**:
  EDSM/Spansh連携、TTS、探査データ共有、天体物理レア度スコア、生体種予測は、それぞれ独立したアドオンとして提供され、既定ではすべて無効です。設定画面の「🧩 アドオン」タブから必要な機能だけを個別に有効化できます。EDSM/Spanshのように外部サーバーとの通信を伴う機能は「外部オンラインアクセス」として一括のオン/オフスイッチにまとめられており、有効化時には確認ポップアップで通知されます。

---

### 🚀 主な機能 (Core Features)

1. **リアルタイム・フライトログ解析 & 航行距離トラッキング**:
   - ジャンプイン、Honk（FSS）、DSS、着陸、生体スキャンを完全自動トラッキング。
   - 記録開始（最古のジャーナル）から現在地までの**累計ジャンプ距離（ly）**およびジャンプ回数をヘッダーに常時表示（ツールチップで初期星系からの直線距離も算出）。
   - FSSスキャン価値、DSSマッピング価値（効率ボーナス含む）、初回発見ボーナス（×2.6）、初回マッピングボーナスを精密算出。
2. **多重連星系対応 Orrery & 軌道階層ツリー**:
   - 恒星・惑星・衛星の階層親子ツリー構造、多重連星系共通重心（Barycentre）、周連星惑星（`AB 1` 等）、周回恒星（`A 1`, `B 1` 等）、特殊命名天体（`Sagittarius A*`, `Founders World`, `Earth` 等）を正確な軌道順で描画。
   - 自由な拡大縮小（0.12x〜40x）・ドラッグ操作に対応したインタラクティブ星系儀（Orrery）。
3. **Exobiology（植物・菌類）解析 & 報酬予測**:
   - 大気組成・表面温度・重力・天体種別から生息可能性のある植物/菌類候補と通常報酬＋初回採取5倍ボーナス額（例: Stratum 90M+ Cr等）を自動算出。規定の必要コロニー離隔距離（m）やサンプリング進行状況（1/3, 2/3, 採取完了）も常時表示。
4. **多段階カウント対応の高度な星系フィルター**:
   - 各種天体（ELW, WW, AW, HMC, 金属豊富, 各種ガスジャイアント等）、物理特性（テラフォーミング候補, 着陸可能, 高重力, 環付き, 特異天体アノマリー）、恒星スペクトル型（O, B, A, F, G, K, M, L, T, Y, 白色矮星, 中性子星, ブラックホール等）、恒星光度階級（Ia0〜VII）を網羅。
   - 単なる有無判定だけでなく、**「特定天体が2個以上」「特定の恒星が3個以上」**といった**天体数・恒星数による多段階下限指定フィルター**を完備。
5. **天体ブックマーク・エイリアス（別名）・Markdownメモ帳**:
   - 天体単位でのブックマーク登録、ユーザー定義通称（エイリアス）、リアルタイムプレビュー対応のMarkdownメモ。
   - 星系名・天体名・エイリアス名・メモ本文を対象とした高速グローバル検索。
6. **🤝 CMDR Data Share（3系統の探査データ共有・出力 & LLM推論連携）**:
   - **🌐 Web共有HTML生成**: ワンクリックで単一の星系図HTML（`exports/{星系名}_share.html`）を出力。本アプリ内では外部通信なし・オフラインで閲覧可能なインタラクティブ天球儀（Orrery）の描画に用いられ、アプリ外では、星系の完全な天体観測JSONを内包した**LLM（ChatGPT, Claude, Gemini等）向けの推論補佐用共有データ**としても利用できます。Elite Dangerousの1星系分のFSS完了ジャーナルをもとに、「独立した(孤立した)星系として、この天体配置は物理的に成立しうるか」といった天体物理シナリオをLLMに推論させる用途を想定しています。
   - **🖼️ 共有用画像生成**: 観測メタデータ（簡易星系データJSON）をPNGチャンクに埋め込んだ **ComfyUI方式サマリー画像カード** を出力。SNS等での共有に対応するほか、本アプリにドラッグ＆ドロップするだけで星系データを瞬時にインポート・復元可能（同様にLLMへの直接入力にも対応）。
   - **📋 星系短評投稿文**: 特殊軌道、地質、生体、環情報などの見どころをまとめたテキストをワンクリックでクリップボードへコピー。Twitch配信コメントやDiscord、X（旧Twitter）への投稿に最適。
   - ＊単一星系分のFSS完了ジャーナルデータさえあれば、本アプリを使わずとも同様のLLM推論は可能です。本機能はそのためのデータ整形・共有を簡便にするものです。
7. **天体物理妥当性チェック・レア度スコア & 天文学モデル査読**:
   - 軌道力学（ヒル球・ロッシュ限界・古在共鳴）やハビタブルゾーン（Kopparapu 2013）、質量分類（Weiss & Marcy 2014）に基づく天体物理レア度スコア（100点満点）の自動算出とサマリーレポート生成。
   - 各天体の質量、密度、温度、重力、軌道離心率などの物理的整合性を機械的ロジックにより多角的に妥当性チェック。
8. **希少天体・特異アノマリーの検知 & アラート**:
   - 物理パラメータや大気・質量・温度条件から極めて希少な特異天体を検知し、FSSスキャン時や星系到達時に視覚バッジおよびTTS通知で案内。
9. **音声合成 (TTS) & VOICEVOX ローカル連携**:
   - 新星系到着時の初回発見（1st Discover）、高額生物天体（初回5倍ボーナス込40M+ Cr / 基礎8M+ Cr相当、閾値設定可能）、および希少特異天体の発見を、音声合成（Web Speech API または 完全ローカルなVOICEVOX）で自動アナウンス。
   - 各イベント通知は個別のON/OFFスイッチおよび通知音タイプ（音声＋チャイム / 音声のみ / チャイムのみ）で柔軟に制御可能。
10. **完全多言語対応 (日本語 / 英語)**:
    - UI画面、星系図、天体インスペクター、Orrery、フィルター、設定、エクスポートHTMLまで、ボタン1つで日本語と英語をシームレスに切り替え可能。
11. **🧩 アドオンシステム (機能の個別ON/OFF)**:
    - EDSM/Spansh連携、TTS、探査データ共有（CMDR Data Share）、天体物理レア度スコア、生体種予測は、それぞれ独立したアドオンとして提供され、設定画面の「🧩 アドオン」タブから個別に有効/無効を切り替え可能。
    - 既定ではすべて無効化されており、必要な機能だけを選んで軽量に使えます。外部通信を伴うEDSM/Spanshは「外部オンラインアクセス」として一括のオン/オフスイッチにまとめられ、有効化時には確認ポップアップが表示されます。
    - 切り替えはアプリの再起動後に反映され、設定画面から再起動を実行できます。

---

### 💻 動作環境

- **OS**: Windows 10 / 11 (64-bit)
- **Python**: 3.10 以上 (ソースコードから起動する場合)
- **ブラウザ**: Microsoft Edge, Google Chrome, Mozilla Firefox (モダンブラウザ推奨)

---

### 📖 使用方法 (Usage & Workflow)

#### 1. インストールと起動

**スタンドアロンEXE版の場合**:
1. [Releases](https://github.com/SuzuneYonaki/ED_Journal_Analyzer/releases) から最新の `ED_Journal_Analyzer.zip` をダウンロードして展開します。
2. フォルダ内の `ED_Journal_Analyzer.exe` を実行します。

**ソースコードから実行する場合**:
```bash
git clone https://github.com/SuzuneYonaki/ED_Journal_Analyzer.git
cd ED_Journal_Analyzer
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

#### 2. 基本ワークフロー

1. アプリを起動すると、自動的に標準のジャーナル保存先（`%USERPROFILE%\Saved Games\Frontier Developments\Elite Dangerous`）を検出し、過去ログの解析を開始します。
2. 画面上部の **「LIVE」** ボタンをONにすると、ゲームプレイ中のFSSスキャンやジャンプインをリアルタイムで検知・更新します。
3. 左ペインの星系リストから任意の星系を選択すると、中央ペインに星系図（Orrery / 階層リスト）、右ペインに天体詳細インスペクターが表示されます。
4. 画面右上の **「⚙️ 設定」** から、文字サイズ調整、ジャーナル保存先の変更、TTS音声エンジン（Web Speech API / VOICEVOX）や通知条件の設定が可能です。

---

<a name="english"></a>
## Overview (English)

> "What kind of star system was that one I passed through after only a quick FSS honk? When did I visit?"
> 
> Bringing the forgotten stars beyond your FSS scanner right back into the palm of your hand.
> 
> A dedicated flight log companion that reawakens the exploration records sleeping in your journals, visualizing your discovery history and astrophysics data with vivid clarity.

**Elite Dangerous Journal Analyzer** is a **local-first desktop GUI application** designed to automatically analyze and monitor flight journal logs (`Journal.*.log`) in real time for *Elite Dangerous*. It provides interactive star system visualizations (Orrery), precise exploration payout estimation, Exobiology biological prediction, mining survey tools, and celestial bookmarking/note-taking.

Starting with v0.8.15, major features — EDSM/Spansh sync, TTS voice alerts, exploration data sharing, astrophysical rarity scoring, and exobiology species prediction — are now implemented as independent **addons**. All of them ship disabled by default, so you can run a lightweight, privacy-focused core install and enable only the features you actually want from the Settings screen.

---

### 🛡️ Core Philosophy: Local-First & Community Connectivity

- **100% Local-First & Privacy Conscious**:
  Flight journals, flight tracks, credits/ship telemetry, celestial notes, and bookmarks are stored **exclusively in your local SQLite database**. No forced cloud sync, mandatory telemetry, or account registration.
- **On-Demand Community Intelligence**:
  Query celestial telemetry, planetary ring hotspots, and planetary mining locations (PML) from EDSM and Spansh on demand. Safely inspect unmapped orbital architectures while keeping unvisited systems strictly isolated from exports.
- **Rich Exploration Sharing (CMDR Data Share)**:
  Export your discovery findings as standalone interactive HTML system maps, ComfyUI-style PNG metadata summary cards, or clipboard summaries for Twitch/Discord/social media.
- **Pick-and-Choose Addons (New in v0.8.15)**:
  EDSM/Spansh sync, TTS, exploration data sharing, astrophysical rarity scoring, and exobiology species prediction are each an independent addon, shipped disabled by default. Enable only what you need from the Settings > Addons tab. Features that reach external servers (EDSM/Spansh) are consolidated into a single "External Online Access" switch with a confirmation prompt before it's turned on.

---

### 🚀 Core Features

1. **Real-Time Journal Parsing & Flight Distance Tracking**:
   - Fully tracks system arrivals, Honk (FSS), DSS mappings, planetary touchdowns, and biological sampling.
   - Live tracking of **total cumulative jump distance (ly)** and jump count from your earliest recorded journal to current location (with straight-line displacement in tooltip).
   - Accurate calculation of FSS values, DSS mapping values (with efficiency bonus), first discovery bonus (2.6x), and first mapped bonus.
2. **Multi-Stellar System Orrery & Orbital Hierarchy Tree**:
   - Accurately renders parent-child hierarchy, barycentres, circumbinary planets (`AB 1`), orbiting stars (`A 1`), and uniquely named bodies (`Sagittarius A*`, `Founders World`, `Earth`).
   - Interactive zoomable (0.12x–40x) and draggable Orrery view with full bilingual labels.
3. **Exobiology Biological Analysis & Payout Forecast**:
   - Predicts potential flora and fungal genera based on atmosphere composition, surface temperature, gravity, and planet class. Calculates payout with the 5x first-sampler bonus (e.g., Stratum 90M+ Cr) and tracks sampling progress (1/3, 2/3, completed).
4. **Advanced Multi-Count Star & Celestial Filters**:
   - Filter by planet classes (ELW, WW, AW, HMC, Metal-Rich, Gas Giants), orbital traits (terraformable, landable, high-G, ringed, anomalies), stellar spectral types (O, B, A, F, G, K, M, L, T, Y, White Dwarfs, Neutron Stars, Black Holes), and luminosity classes (Ia0–VII).
   - Supports **minimum count threshold filters** (e.g., "systems with at least 2 ELWs" or "systems with at least 3 M-class stars") with configurable ALL/ANY logic matching.
5. **Celestial Bookmarks, Aliases & Markdown Notebook**:
   - Bookmark specific bodies with custom alias names and live Markdown notes.
   - Comprehensive global search across star systems, body names, aliases, and notebook contents.
6. **🤝 CMDR Data Share (3-Way Exploration Data Export & LLM Inference Integration)**:
   - **🌐 Standalone Web HTML**: One-click generation of a self-contained interactive HTML system map (`exports/{System}_share.html`). Within the app, it drives the offline, no-network Orrery view; outside the app, the same file — with its embedded full celestial observation JSON — also works as **shareable data to assist LLM inference** (ChatGPT, Claude, Gemini, etc.). It's built for scenarios like asking an LLM whether a body arrangement, based on a single Elite Dangerous system's FSS-complete journal data, could be physically plausible as an isolated system.
   - **🖼️ Summary Image Card**: Exports a ComfyUI-style PNG image card with embedded observation metadata (a simplified system data JSON), suitable for sharing on social media. Drag-and-drop it back into the app to restore the system data instantly (also usable as direct LLM input).
   - **📋 System Review Text**: One-click clipboard copy of a concise highlight summary (special orbits, geology, biology, rings, etc.) for Twitch chat, Discord, or social media posts.
   - *Note: this LLM-inference workflow only needs a single system's FSS-complete journal data — it's possible without this application entirely. This feature simply makes formatting and sharing that data easier.*
7. **Astrophysical Reality Audit & Rarity Scoring**:
   - Automatic 100-point rarity scoring and report generation based on orbital dynamics (Hill sphere, Roche limit, Kozai mechanism), habitable zones (Kopparapu 2013), and mass classifications (Weiss & Marcy 2014).
8. **Rare & Anomalous Body Detection**:
   - Detects extraordinary celestial objects and anomalies based on physical parameters, triggering distinct UI badges and customizable audio notifications.
9. **Text-to-Speech (TTS) & Local VOICEVOX Integration**:
   - Voice alerts for First Discoveries, high-value exobiology bodies (40M+ Cr w/ bonus threshold configurable), and rare celestial anomalies via Web Speech API or local VOICEVOX (`http://127.0.0.1:50021`).
   - Independent event toggles and alert mode selector (Voice + Chime / Voice only / Chime only).
10. **Full Bilingual Support (Japanese / English)**:
    - Complete one-click localization across UI controls, Orrery views, inspector panels, settings modal, and exported HTML files.
11. **🧩 Addon System (Per-Feature Enable/Disable)**:
    - EDSM/Spansh sync, TTS, exploration data sharing (CMDR Data Share), astrophysical rarity scoring, and exobiology species prediction are each an independent addon, individually toggleable from the Settings > Addons tab.
    - All ship disabled by default, so you only run what you need. EDSM/Spansh (which reach external servers) are consolidated into a single "External Online Access" switch with a confirmation prompt on enable.
    - Toggling takes effect on the next restart; the Settings tab can trigger that restart for you.

---

### 📖 Installation & Usage

#### Standalone EXE (Windows):
1. Download `ED_Journal_Analyzer.zip` from [Releases](https://github.com/SuzuneYonaki/ED_Journal_Analyzer/releases).
2. Extract the archive and launch `ED_Journal_Analyzer.exe`.

#### Running from Source:
```bash
git clone https://github.com/SuzuneYonaki/ED_Journal_Analyzer.git
cd ED_Journal_Analyzer
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

---

## Credits & Acknowledgements / 謝辞 & クレジット

### 🌐 オンラインサービス & コミュニティデータベースへの謝辞 (Online Community Services & APIs)
- **[EDSM (Elite Dangerous Star Map)](https://www.edsm.net/)**:
  Public REST APIs for star system coordinates, celestial astrophysics telemetry, and faction BGS states. Immense gratitude to AnthorNet and the EDSM community.
- **[Spansh (Elite Dangerous Galaxy Search Engine)](https://spansh.co.uk/)**:
  High-performance deep search APIs for planetary bodies, planetary ring hotspots, and planetary mining locations (PML). Sincere thanks to Spansh and community contributors.
- **Frontier Developments plc**:
  For the boundless 1:1 scale Milky Way galaxy of *Elite Dangerous* and the official Player Journal API.
  > "Elite Dangerous Journal Analyzer & Exploration Orrery was created using assets and imagery from Elite Dangerous, with the permission of Frontier Developments plc, for non-commercial purposes. It is not endorsed by nor reflects the views or opinions of Frontier Developments and no employee of Frontier Developments was involved in the making of it."
- **[Canonn Research Group](https://canonn.science/)**:
  Scientific research on Exobiology environmental matrices and biological colony distance rules.
- **MattG & Exploration Pioneers**:
  For exploration payout formula reverse-engineering and community documentation.
- **[VOICEVOX](https://voicevox.hiroshiba.jp/)**:
  Hiroshiba and character voice library creators for the outstanding local Japanese speech synthesis engine.
- **AI Assisted Development**:
  Google DeepMind / Antigravity / Gemini for real-time architecture design, pipeline automation, and pair programming.

---

## License

This project is licensed under the **GNU General Public License v3.0 (GPLv3)**. See [LICENSE](LICENSE) for details.
