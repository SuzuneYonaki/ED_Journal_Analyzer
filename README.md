# Elite Dangerous Journal Analyzer & Exploration Orrery (v0.1.7)

[日本語](#日本語) | [English](#english)

---

<a name="日本語"></a>
## 概要 (日本語)

**Elite Dangerous Journal Analyzer** は、宇宙シミュレーションゲーム『Elite Dangerous』のフライトジャーナルログ（`Journal.*.log`）を自動解析・リアルタイム監視し、過去に訪れた星系・天体の状態、位置関係・軌道情報、レア天体・特殊周回、着陸可否・重力・火山活動、Exobiology（植物・菌類）の生息予測と報酬額、FSS/DSS探査価値の精密計算、Rhino採掘支援、天体ブックマーク・Markdownメモ機能を提供する**完全ローカル完結型デスクトップGUIアプリケーション**です。

> **「あの時訪れたあの星は、どんな宙域だっただろう？」**  
> 銀河の遥かなる長旅の記録や、過去の深宇宙探索・初発見の思い出をいつでも完全なプライバシーと美しいビジュアルで振り返ることができます。

> **⚠️ 使用上の注意・免責事項**: 本ツールはファンメイドの非公式オープンソースツールです。フロンティア・デベロップメンツ社とは一切関係ありません。ジャーナルログの解釈や探査・採掘データの完全性についてはいかなる保証も致しかねます。本ツールの使用によって生じたゲーム内での損失（機体喪失、採掘リグ耐久値損失、探査データ喪失など）を含むいかなる結果についても開発者は一切の責任を負いません。自己責任においてご利用ください。

---

### 主な機能 (Key Features)

1. **軌道階層ツリー & インタラクティブ System Map**:
   - 恒星・惑星・衛星の階層親子ツリー構造、多重連星系共通重心（Barycentre）、周回恒星、軌道長半径（AU / Ls）、離心率、公転・自転周期、傾斜角、潮汐固定の忠実な可視化。
   - 周回恒星（`A 1`, `B 1` 等）や連星周回天体（`AB 1`, `Ab 2` 等）、特殊命名天体（`Founders World`, `Earth`, `Moon`, `Sagittarius A*`, `Source 2` 等）を正確な軌道順で描画。
2. **探査価値の精密計算 (Exploration Payouts)**:
   - FSSスキャン価値、DSSマッピング価値（効率ボーナス含む）、初回発見ボーナス（$\times 2.6$）、初回マッピングボーナスを精密算出。
   - 星系ごとの「FSSスキャン合計」と「最大見込み（FD+FM）」を並列表示。
3. **Exobiology（植物・菌類）解析 & 報酬予測**:
   - 大気組成・表面温度・重力・天体種別から生息可能性のある植物/菌類候補（Stratum, Bacterium, Clypeus等）と通常報酬 + 初回採取5倍ボーナス額を自動算出。
   - サンプル採取に必要なコロニー間隔を天体カードに常時表示。
4. **地表・着陸・重力 & 採掘支援 (Rhino Mining Support)**:
   - 着陸可否（Landable）、精密表面重力（$G$値）と着陸可能天体限定の高重力危険警告、火山活動・地質シグナル。
   - 採掘Rig耐久値管理に直結する重力（$G$）・表面温度（$K$）の表示トグル。
   - EDSM天体データに基づく採掘有望度スコア（**⛏️ Scout: High** / **⛏️ Scout: Med**）判定。
   - 大型着艦パッド（Large Pad）装備ステーション保有星系・到達距離（< 2,000 Ls、< 10,000 Ls、< 50,000 Ls）フィルター。
   - リング天体DSSスキャン（ホットスポット）のMarkdownメモ自動記録機能。
   - CMDRの現在地座標（緯度・経度）を天体メモへワンクリック挿入。
5. **天体ブックマーク・エイリアス（別名）・Markdownメモ帳**:
   - 天体単位でのブックマーク登録、ユーザー定義通称（例: `採掘拠点 Alpha`, `TF候補1`）、Markdown形式メモ（リアルタイムプレビュー対応）。
   - 星系名だけでなく「天体名」「エイリアス名」「メモ本文」を横断したグローバル検索が可能。
6. **完全スタンドアロン Web共有HTML生成**:
   - ワンクリックで単一の美しい星系図HTML（`{星系名}_share.html`）を `exports/` フォルダへ書き出し、エクスプローラーで自動ハイライト。
   - 外部CDNや外部ネットワーク接続を一切必要としない完全オフライン完結設計。
   - 多重連星系対応のオーラリー（無段階ズーム 0.12x〜40x、ドラッグパン、恒星クイックジャンプバー）を搭載。
   - **完全な天体物理観測JSONデータを内包**しており、LLMへの直接投入データコンテナとしても機能。
7. **EDSM連携 & 未訪問星系オンデマンド参照（安全ロック付き）**:
   - EDSM（Elite Dangerous Star Map）連携により、既知星系へのジャンプインや Honk（`FSSDiscoveryScan`）時に未スキャン天体の公転軌道・物理データ・探査価値を優先キューで自動補完。
   - 未訪問星系でも外部参照として星系マップをオンデマンド閲覧可能（プレイヤー自身の探査記録と混同されないようエクスポート遮断・統計除外の安全ロック機構を完備）。
8. **UIカスタマイズ & 日英バイリンガル対応**:
   - コックピット計器盤を再現した **Elite Classic Amber HUD**、**Modern Deep Space**、**Cyan Explorer HUD** のカラーテーマ切り替え。
   - UIフォントサイズの実数値（px）自由変更および緊急リセット（<kbd>Ctrl + 0</kbd>）。
   - 画面右上の **`[JP] / [EN]`** ボタンからいつでもワンクリックで言語を切り替え可能。

---

### 使用方法 (Usage)

#### 起動方法

##### 配布パッケージ（推奨）:
GitHub Releases よりダウンロードした `ED_Journal_Analyzer.exe` を任意のフォルダに配置して実行します。

##### ソースコードから実行する場合:
```powershell
# リポジトリのクローン
git clone https://github.com/SuzuneYonaki/ED_Journal_Analyzer.git
cd ED_Journal_Analyzer

# 依存パッケージのインストール
pip install -r requirements.txt

# デスクトップGUIウィンドウとして起動
python run.py

# または標準ブラウザで起動
python run.py --browser
```

#### 基本的な操作フロー
1. **ログの読み込み**:
   - 起動後、右上の「**ログ再スキャン (Rescan Logs)**」をクリックすると、Saved Games フォルダ内のジャーナルログが一括インデックス化されます。
2. **リアルタイム追従 (LIVE)**:
   - ゲームプレイ中は自動的にジャーナルの更新を検知し、現在いる星系・スキャンした天体情報が画面に即時反映されます。
3. **星系・天体の探索とメモ**:
   - 左ペインの星系リストや検索バーから星系を選択。天体インスペクターからブックマーク登録やMarkdownメモの記述が可能です。
4. **Web共有HTMLの出力**:
   - 星系詳細ヘッダーの「Web共有HTML出力」をクリックすると、`exports/{星系名}_share.html` が書き出され、保存先がエクスプローラーで自動表示されます。

#### 💾 ポータブル設計・`data` フォルダの扱い
- **レジストリやシステム領域への書き込みは一切行いません**: すべてのデータはアプリケーション実行フォルダ内で完結します。
- **`data` フォルダ**: 初回起動時に自動作成され、SQLiteデータベース（`elite_exploration.db`）が格納されます。
- **バージョンアップ時**:
  - 新バージョンへアップデートする際は、**既存の `data` フォルダを残したまま**、新しい `ED_Journal_Analyzer.exe`（またはソースファイル）で上書き起動してください。
  - 過去の探査ログ、ブックマーク、メモ等の全データがそのまま安全に引き継がれます。
- **完全削除（アンインストール）**:
  - アプリケーション本体と `data` フォルダを手動で削除するだけで、PC内に一切の痕跡を残さずアンインストールされます。

---

### 🌌 生成AIを活用した天体物理学的実在妥当性の検証 (Astrophysical Reality Check Prompt)

本アプリケーションが出力する **Web共有HTML（`{星系名}_share.html`）** には、`<script id="ed-system-astrophysics-data" type="application/json">` として、星系内の全天体の完全な天体物理・軌道パラメータ（質量、半径、温度、軌道長半径、離心率、公転周期、大気圧、大気組成比率など）がJSON形式で埋め込まれています。

このHTMLファイル（またはエクスポートされたJSON）を **ChatGPT、Claude、Gemini 等の生成AIにドラッグ＆ドロップで添付** し、以下のプロンプトを入力することで、**「この星系が現代の天体物理学・惑星科学の観点から見て、現実の宇宙に本当に存在し得るかどうか」** の厳密な実在妥当性チェックを行うことができます。

> 💡 **AstroRarity との連携**:
> 天体物理特異性判定エンジン（AstroRarity）等と連携して評価する際のリファレンスプロンプトとしても活用いただけます。

#### 📋 天体物理学的実在妥当性チェック・プロンプト

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

**Elite Dangerous Journal Analyzer** is a local desktop GUI application designed to automatically parse, monitor, and visualize flight journal logs (`Journal.*.log`) from the space simulator *Elite Dangerous*. It delivers comprehensive expedition archives, orbital hierarchy trees, rare celestial anomaly detection, surface gravity & volcanism checks, Exobiology habitat predictions & payouts, exact FSS/DSS exploration value calculations, Rhino SRV mining intelligence, and celestial body bookmarks with rich Markdown notes—**completely offline with absolute privacy**.

> **"What kind of world was that memorable planet I visited long ago?"**  
> Relive your interstellar voyages, deep-space expeditions, and first discoveries through beautiful visuals and comprehensive telemetry.

> **⚠️ Disclaimer**: This tool is an unofficial, fan-made open-source companion and is not affiliated with or endorsed by Frontier Developments plc. No warranties are provided regarding data accuracy or game log interpretation. The developer assumes no responsibility or liability for any in-game losses or damages. Use at your own discretion.

---

### Key Features

1. **Orbital Hierarchy & Interactive System Map**:
   - Faithful hierarchical visualization of stars, planets, and moons, including circumbinary barycentres, companion stars, semi-major axes (AU / Ls), eccentricity, orbital/rotational periods, inclination, and tidal locking.
   - Accurately positions circumstellar stars (`A 1`, `B 1`), circumbinary bodies (`AB 1`, `Ab 2`), and custom-named bodies (`Founders World`, `Earth`, `Moon`, `Sagittarius A*`, `Source 2`) in exact orbital order.
2. **Exact Exploration Payout Engine**:
   - Precision calculation of FSS scan values, DSS mapped values (including efficiency bonus), First Discovered ($2.6\times$), and First Mapped bonuses.
   - Parallel display of current FSS Scan Total alongside Max Potential (FD+FM).
3. **Exobiology Predictor & Vista Genomics Rewards**:
   - Predicts organic candidates (Stratum, Bacterium, Clypeus, Tubus, etc.) based on atmospheric composition, temperature, surface gravity, and planetary classification.
   - Computes standard payouts and $5\times$ First Discovery bonuses, with sample colony distance requirements displayed on each body card.
4. **Surface Telemetry & Rhino Mining Support**:
   - Landable status, surface gravity ($G$) with High-G landing safety warnings, volcanism classification, and geological signals.
   - Dedicated toggles for surface gravity ($G$) and surface temperature ($K$) directly tied to mining rig durability management.
   - EDSM-based mining scout scores (**⛏️ Scout: High** / **⛏️ Scout: Med**).
   - Filter systems by Large Landing Pad availability and arrival distance thresholds (< 2,000 Ls, < 10,000 Ls, < 50,000 Ls).
   - Automated ring DSS scan (hotspots) logging into body Markdown notes.
   - One-click insertion of live CMDR planetary surface coordinates into body notes.
5. **Body Bookmarks, Custom Aliases & Markdown Notes**:
   - Bookmark celestial bodies, set user-defined aliases (e.g. `Mining Base Alpha`), and maintain rich Markdown notes with instant live preview.
   - Full global search across star systems, body names, aliases, and Markdown note contents simultaneously.
6. **Standalone Web Share HTML Generation**:
   - One-click export of a beautiful, self-contained single HTML file (`exports/{System}_share.html`) that automatically opens and highlights in Windows Explorer.
   - Zero external CDN links or network requests; runs 100% offline in any modern browser.
   - Interactive multi-star system orrery with continuous zoom (0.12x - 40x), drag pan, hover tooltips, and stellar quick jump navigation.
   - **Embeds complete astrophysical observation JSON data**, serving as a ready-to-use container for Generative AI analysis.
7. **EDSM Integration & Unvisited Reference Systems (with Safety Locks)**:
   - Synchronizes with EDSM via priority queue to auto-backfill physical parameters and exploration values for known star systems upon jump-in or Honk.
   - On-demand inspection of unvisited reference systems with strict export lockout and expedition stat exclusion.
8. **UI Customization & Instant Bilingual Support**:
   - Switchable color presets: **Elite Classic Amber HUD** (authentic cockpit recreation), **Modern Deep Space**, and **Cyan Explorer HUD**.
   - Adjustable font size (direct numeric px input) with instant reset (<kbd>Ctrl + 0</kbd>).
   - Instant language switching via the **`[JP] / [EN]`** toggle in the top-right corner.

---

### Installation & Run

#### Pre-built Executable (Recommended):
Download `ED_Journal_Analyzer.exe` from [GitHub Releases](https://github.com/SuzuneYonaki/ED_Journal_Analyzer/releases), place it in any folder, and double-click to run.

#### Running from Source:
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

#### Basic Workflow:
1. **Initial Indexing**: Launch the app and click **Rescan Logs** in the top-right corner to index your flight history.
2. **Live Tracking**: During gameplay, the app automatically tracks new journal events in real time.
3. **Export Web Share HTML**: Click "Web共有HTML出力" on any system header to export a standalone orrery HTML file into `exports/`.

#### 💾 Portable Design & `data` Directory Handling
- **Zero registry footprint**: Everything is stored locally next to the application executable.
- **Upgrading**: When upgrading to a newer version, **keep your existing `data` folder**. Simply replace the executable or pull the latest code. All flight histories, bookmarks, and notes will migrate automatically and remain intact.
- **Uninstallation**: Delete the application executable and the `data` folder to remove all traces from your computer.

---

### 🌌 Deep Astrophysical Reality Check via Generative AI (LLM Prompting)

Each exported **Web Share HTML (`{System}_share.html`)** contains the complete observational and orbital dataset (stellar & planetary masses, precise radii, temperatures, semi-major axes, eccentricities, orbital periods, surface pressures, and chemical compositions) embedded inside a `<script id="ed-system-astrophysics-data" type="application/json">` element.

By dragging and dropping this HTML file (or the raw JSON) into **ChatGPT, Claude, or Gemini** alongside the prompt below, you can perform a rigorous scientific audit to evaluate whether the system could genuinely exist in physical reality, separate procedural artifacts from true astronomical anomalies, and reconstruct its stellar formation narrative.

#### 📋 Astrophysical Reality Check Prompt Template

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
