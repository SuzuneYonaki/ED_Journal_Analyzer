# Elite Dangerous Journal Analyzer & Exploration Orrery

[日本語](#日本語) | [English](#english)

---

<a name="日本語"></a>
## 概要 (日本語)

**Elite Dangerous Journal Analyzer** は、宇宙シミュレーションゲーム『Elite Dangerous』のフライトジャーナルログ（`Journal.*.log`）をリアルタイムに自動解析・監視し、星系構造の可視化、探査価値の精密算出、Exobiology（生体スキャン）予測、採掘支援、天体ブックマーク・メモ機能を提供する**完全ローカル完結型デスクトップGUIアプリケーション**です。

---

### 🚀 主な機能 (Core Features)

1. **リアルタイム・フライトログ解析 & 探査価値計算**:
   - ジャンプイン、Honk（FSS）、DSS、着陸、生体スキャンを完全自動トラッキング。
   - FSSスキャン価値、DSSマッピング価値（効率ボーナス含む）、初回発見ボーナス（×2.6）、初回マッピングボーナスを精密算出。
2. **多重連星系対応 Orrery & 軌道階層ツリー**:
   - 恒星・惑星・衛星の階層親子ツリー構造、多重連星系共通重心（Barycentre）、周連星惑星（`AB 1` 等）、周回恒星（`A 1`, `B 1` 等）、特殊命名天体（`Sagittarius A*`, `Founders World`, `Earth` 等）を正確な軌道順で描画。
   - 自由な拡大縮小（0.12x〜40x）・ドラッグ操作に対応したインタラクティブ星系儀（Orrery）。
3. **Exobiology（植物・菌類）解析 & 報酬予測**:
   - 大気組成・表面温度・重力・天体種別から生息可能性のある植物/菌類候補と通常報酬＋初回採取5倍ボーナス額を自動算出。コロニー間隔も常時表示。
4. **地表・着陸・重力 & 採掘支援 (Rhino Mining Support)**:
   - 着陸可能天体（Landable）限定の高重力警告、地質・火山活動シグナル。
   - EDSM天体データに基づく採掘有望度スコア判定（**⛏️ Scout: High / Med**）。
   - 大型着艦パッド（Large Pad）装備ステーション保有星系・到達距離フィルター。
   - リング天体のDSSスキャン結果（ホットスポット）のMarkdownメモ自動記録、CMDR現在地座標のワンクリック挿入。
5. **天体ブックマーク・エイリアス（別名）・Markdownメモ帳**:
   - 天体単位でのブックマーク登録、ユーザー定義通称（エイリアス）、リアルタイムプレビュー対応のMarkdownメモ。
   - 星系名・天体名・エイリアス名・メモ本文を対象とした高速グローバル検索。
6. **スタンドアロン Web共有HTML生成**:
   - ワンクリックで単一の美しい星系図HTML（`exports/{星系名}_share.html`）を出力。外部通信なしでブラウザ閲覧可能。
   - **完全な天体物理観測JSONデータを内包**しており、LLMへの直接投入データコンテナとしても機能。
7. **EDSM連携 & 未訪問星系オンデマンド参照（安全ロック付き）**:
   - 既知星系へのジャンプインやHonk時に未スキャン天体の公転軌道・物理データ・探査価値を優先キューで自動補完。
   - 未訪問星系でも外部参照として星系マップをオンデマンド閲覧可能（エクスポート遮断・統計除外の安全ロック機構を完備）。
8. **UIカスタマイズ & 日英バイリンガル対応**:
   - コックピット計器盤を再現した **Elite Classic Amber HUD**、**Modern Deep Space**、**Cyan Explorer HUD** のテーマ切り替え。
   - UIフォントサイズの自由変更および緊急リセット（<kbd>Ctrl + 0</kbd>）。
   - 画面右上の **`[JP] / [EN]`** ボタンからいつでもワンクリックで言語切替。

---

### 📖 使用方法 (Usage & Workflow)

#### 1. インストールと起動
- **配布パッケージ（推奨）**:
  [GitHub Releases](https://github.com/SuzuneYonaki/ED_Journal_Analyzer/releases) より `ED_Journal_Analyzer.exe` をダウンロードし、任意のフォルダに配置して実行します。
- **Pythonソースから実行**:
  ```powershell
  git clone https://github.com/SuzuneYonaki/ED_Journal_Analyzer.git
  cd ED_Journal_Analyzer
  pip install -r requirements.txt
  python run.py          # GUIアプリとして起動
  python run.py --browser # 既定のブラウザで起動
  ```

#### 2. 基本ワークフロー
1. **初回ログスキャン**: 起動後、画面右上の「**Rescan Logs**」をクリックして過去のフライトログをインデックスします。
2. **ゲームプレイ中の自動追跡**: *Elite Dangerous* を起動してプレイするだけで、ジャンプ・スキャン・着陸などの最新イベントがリアルタイムに画面へ反映されます。
3. **星系の閲覧 & Web共有HTML出力**:
   - 画面左側の星系リストから星系を選択してツリーやOrreryを表示します。
   - 星系ヘッダーの「**Web共有HTML出力**」をクリックすると、`exports/` フォルダに自己完結型のHTML星系図が出力され、エクスプローラーでハイライトされます。

#### 3. 応用的な使い方
- **ブックマーク & メモ**: 天体詳細パネルから「★ ブックマーク」やエイリアス名（例: `採掘拠点 Alpha`）、Markdown形式のメモを保存できます。
- **採掘スポット・地表座標の記録**:
  - リング天体をDSSスキャンすると、ホットスポット一覧が自動で天体メモに追記されます。
  - 着陸中にメモ欄右下の「📍 現在地座標挿入」を押すと、現在CMDRがいる緯度・経度が瞬時に挿入されます。
- **AI による星系の深層査読**:
  - 出力した Web 共有 HTML（内部に天体・軌道JSONを完全保持）を ChatGPT、Claude、Gemini 等にドラッグ＆ドロップし、下記の**天体物理リアリティチェック・プロンプト**を併用することで、星系の物理的実在性やハビタビリティの学術的検証レポートを生成できます。

#### 💾 ポータブル設計 & `data` フォルダの管理
- **レジストリ完全非依存**: すべての設定・インデックスデータ・メモ・ブックマークは、実行ファイルと同じ階層の `data/` フォルダ内に保存されます。
- **アップデート時**: 新バージョンへ移行する際は、**既存の `data/` フォルダをそのまま残し**、実行ファイル（またはソースコード）のみを上書きしてください。すべてのフライト履歴やメモが自動で引き継がれます。
- **アンインストール**: アプリ本体と `data/` フォルダを削除するだけで、PC環境を一切汚さず完全に消去できます。

---

### 🌌 天体物理学的実在妥当性チェック・プロンプト (for LLMs)

本アプリケーションが出力する **Web共有HTML（`{星系名}_share.html`）** には、`<script id="ed-system-astrophysics-data" type="application/json">` として、星系内の全天体の完全な天体物理・軌道パラメータがJSON形式で埋め込まれています。

このHTMLファイル（またはJSON）を **ChatGPT、Claude、Gemini 等の生成AIにドラッグ＆ドロップで添付** し、以下のプロンプトを入力することで、現代の天体物理学・惑星科学の観点から厳密な実在妥当性チェックを行うことができます。

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

---

<a name="english"></a>
## Overview (English)

**Elite Dangerous Journal Analyzer** is a standalone, local-first desktop GUI application designed to parse and monitor *Elite Dangerous* flight journal logs (`Journal.*.log`) in real time. It offers orbital hierarchy visualization, precise exploration payout calculations, Exobiology predictions, mining reconnaissance, and celestial bookmarking/notes.

---

### 🚀 Core Features

1. **Real-Time Journal Tracking & Exploration Payouts**:
   - Automated live tracking of system jumps, Honk (FSS), DSS mapping, surface landings, and bio-scans.
   - Exact payout calculation for FSS scans, DSS mapping (including efficiency bonus), First Discovery bonus (×2.6), and First Mapped bonus.
2. **Multi-Star Orrery & Orbital Hierarchy Tree**:
   - True parent-child hierarchy representing stellar barycentres, circumbinary planets (`AB 1`), circumstellar companion stars (`A 1`, `B 1`), and custom-named bodies (`Sagittarius A*`, `Founders World`, `Earth`, `Moon`).
   - Interactive system orrery with smooth continuous zoom (0.12x - 40x), drag pan, and stellar jump navigation.
3. **Exobiology Predictions & Reward Modeling**:
   - Predicts bio-genus candidates (Stratum, Bacterium, etc.) and calculates standard payouts plus 5x First Sampler bonuses based on atmosphere, surface temperature, gravity, and planet type. Displays required colony distance.
4. **Surface Landing, Gravity & Rhino Mining Support**:
   - Extreme gravity danger warnings exclusively on landable worlds; surface volcanism and geological signals.
   - High-value mining reconnaissance rating (**⛏️ Scout: High / Med**) powered by EDSM telemetry.
   - Filtering for systems hosting stations with Large Landing Pads within configurable arrival distance thresholds (< 2,000 Ls, < 10,000 Ls, < 50,000 Ls).
   - Automated DSS ring hotspot markdown logging and one-click CMDR surface coordinate insertion.
5. **Celestial Bookmarks, Aliases & Markdown Notes**:
   - Bookmark celestial bodies, assign user aliases (e.g. `Mining Base Alpha`), and edit rich Markdown notes with live preview.
   - Lightning-fast global search across star systems, body names, custom aliases, and note contents.
6. **Standalone Web Share HTML Export**:
   - Exports a single, self-contained HTML file (`exports/{System}_share.html`) that opens offline in any browser without external CDNs.
   - **Embeds complete astrophysical observation JSON data**, serving as a ready-to-use container for Generative AI analysis.
7. **EDSM Integration & Unvisited Reference Systems**:
   - Auto-backfills orbital mechanics and exploration values for known systems via background priority queue upon jump-in or Honk.
   - On-demand inspection of unvisited systems with strict export lockout and expedition stat exclusion.
8. **UI Customization & Instant Bilingual Support**:
   - Switchable themes: **Elite Classic Amber HUD**, **Modern Deep Space**, and **Cyan Explorer HUD**.
   - Adjustable font size (numeric px input) with instant reset (<kbd>Ctrl + 0</kbd>).
   - Instant language switching via the **`[JP] / [EN]`** button.

---

### 📖 Usage & Workflow

#### 1. Installation & Launch
- **Pre-built Executable (Recommended)**:
  Download `ED_Journal_Analyzer.exe` from [GitHub Releases](https://github.com/SuzuneYonaki/ED_Journal_Analyzer/releases), place it in any folder, and double-click to run.
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
3. **System Browsing & Web Share Export**:
   - Select a star system from the left panel to inspect its tree and Orrery.
   - Click "**Web共有HTML出力**" on any system header to export a standalone orrery HTML file into `exports/`.

#### 3. Advanced Features
- **Bookmarks & Notes**: Open body details to bookmark, set custom aliases, or write Markdown notes.
- **Mining & Surface Navigation**:
  - Scanning rings with DSS automatically documents detected hotspots into the body note.
  - While landed, click "📍 現在地座標挿入" in the note editor to insert your exact planetary coordinates.
- **AI-Powered System Audit**:
  - Drag and drop your exported Web Share HTML into ChatGPT, Claude, or Gemini alongside the **Astrophysical Reality Check Prompt** below to generate an in-depth astrophysical plausibility review.

#### 💾 Portable Architecture & `data` Directory
- **Zero Registry Footprint**: All database indexes, notes, and preferences reside locally inside the `data/` directory next to the executable.
- **Upgrading**: When updating to a newer release, **preserve your existing `data/` folder**. Simply overwrite the executable or update the code; all records migrate seamlessly.
- **Uninstallation**: Delete the application executable and the `data/` folder to completely remove all traces from your system.

---

### 🌌 Astrophysical Reality Check Prompt (for LLMs)

Each exported **Web Share HTML (`{System}_share.html`)** embeds complete astrophysical and orbital telemetry inside a `<script id="ed-system-astrophysics-data" type="application/json">` block.

Pass this HTML file (or the raw JSON) to **ChatGPT, Claude, or Gemini** using the prompt below:

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

---

## Credits & Acknowledgements

- **AI Assisted Development**: Developed with the assistance of AI (Google DeepMind / Antigravity / Gemini).
- **Game Data & Assets**: *Elite Dangerous* is a registered trademark of Frontier Developments plc.
- **Formulas & Science**: Exploration payouts, planetary physics models, and Exobiology condition matrices are based on Frontier Developments specifications and ED community research (EDSM, Canonn Research, MattG).

---

## License

This project is licensed under the Apache License 2.0.
