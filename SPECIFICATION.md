# Elite Dangerous Journal Analyzer & Exploration Orrery
## システム仕様書 & LLM改修リファレンス (System Specification for LLMs)

> **対象読者**: 本プロジェクトのコードベースを解析・確認・修正・拡張する AI コーディングアシスタント（LLM）および開発者。  
> **目的**: 本アプリケーションの全体アーキテクチャ、データモデル、ビジネスロジック、UI状態管理、開発規約を単一ドキュメントで把握し、ハルシネーションや既存機能の破壊なしに正確なコード修正を行えるようにすること。

---

## 1. システム概要 & 設計思想 (Architecture Principles)

### 1.1 アプリケーション概要
**Elite Dangerous Journal Analyzer** は、宇宙シミュレーションゲーム『Elite Dangerous』のフライトジャーナルログ（`Journal.*.log`）をリアルタイムに自動監視・解析し、星系構造のインタラクティブ可視化（System Map / Orrery）、探査価値の精密算出、生体スキャン（Exobiology）予測、採掘支援、天体ブックマーク・メモ機能を提供する**ローカルファースト型デスクトップGUIアプリケーション**です。

### 1.2 技術スタック
- **バックエンド**: Python 3.10+ / FastAPI / SQLite3 / Uvicorn
- **フロントエンド**: HTML5 / CSS3 / Vanilla JavaScript (ES6+, フレームワーク不使用)
- **GUIデスクトップラッパー**: PySide6 (Qt) または pywebview（`python run.py --browser` でブラウザ起動も可能）
- **外部連携**: EDSM API, Spansh API, VOICEVOX (ローカルTTS), Web Speech API
- **テスト基盤**: pytest

### 1.3 コア設計原則 (Core Principles)
1. **完全ローカルファースト & プライバシー保護**:
   - プレイヤーの航跡、所持金、スキャンデータ、メモはすべてローカルの SQLite データベースに保存。
   - 外部への個人データ送信は一切行わない。
2. **コミュニティ知見のオンデマンド照会 & 安全ロック**:
   - EDSM や Spansh から未スキャン天体の公転軌道や環ホットスポット（Hotspots）をオンデマンドで取得可能。
   - 未訪問星系に対するエクスポート遮断（安全ロック）など、自力探査の完全性を保証する機構を備える。
3. **SSOT (Single Source of Truth) の徹底**:
   - ドメイン辞書やマッピングテーブルは外部設定ファイル（JSON/YAML/CSV）または専用定義モジュールに集約。スクリプト内にハードコードしない。
4. **ゼロ・スペキュレーション & 厳格なNULL安全性**:
   - 値の有無（NULL/None）や型を推測・捏造しない。
   - **Python における厳格な None ガード**:
     `b.get("key", 0)` や `(val or 0)` は、`0` や `0.0`（離心率 0.0、表面重力 0.0G、銀河座標 0.0 等）が正当値の場合に意図しないフォールバックを引き起こすため**厳格に禁止**する。
     必ず `b.get("key") if b.get("key") is not None else default` または `val if val is not None else default` のように、明示的な `is not None` 判定を必須とする。
   - **JavaScript における Nullish Coalescing 標準化**:
     `val || default` を禁止し、`0` や `""`（空文字）、`false` が falsy として扱われて潰れるのを防ぐため、Nullish Coalescing 演算子 (`val ?? default`) または明示的な `val !== null && val !== undefined` 判定を標準とする。

---

## 2. プロジェクト構造 & モジュール責務 (Project Structure)

```text
elite_journal_analysys/
├── run.py                     # アプリケーション起動エントリポイント (GUI / ブラウザ起動制御)
├── main.py                    # PySide6 GUI ウィンドウ制御
├── SPECIFICATION.md           # 本仕様書
├── README.md                  # ユーザー向け機能説明・インストールガイド
├── agent.md                   # LLM改修規約・Anti-Hallucination ガイドライン
├── app/
│   ├── db/
│   │   └── database.py        # SQLite 接続管理、DDL、マイグレーション、データ操作関数
│   ├── parser/
│   │   ├── journal_parser.py  # ED ジャーナルログ (JSONL) イベント解析 & DB 反映
│   │   ├── value_calculator.py# FSS/DSS 探査クレジット価値・ボーナス計算エンジン
│   │   ├── exobiology.py      # 植物・菌類生息予測 & 報酬・コロニー離隔距離計算
│   │   └── rarity_scorer.py   # 天体物理レア度スコア・星系年齢矛盾のルールベース判定
│   ├── server/
│   │   └── api.py             # FastAPI REST API ルーティング & サーバーサイドロジック
│   ├── services/
│   │   ├── journal_watcher.py # ジャーナルフォルダのリアルタイム差分監視
│   │   ├── export_service.py  # Standalone HTML、ComfyUI方式メタデータ埋め込みPNG、SNS短評出力
│   │   ├── tts_service.py     # 音声読み上げ (VOICEVOX / Web Speech API) 設定連携
│   │   ├── spansh_service.py  # Spansh API 連携 (環ホットスポット、惑星採掘地点 PML)
│   │   └── edsm/              # EDSM 連携モジュール群 (キューイング、天体物理インポート、統計)
│   ├── data/                  # ドメイン辞書、静的定義データ (JSON等)
│   └── ui/                    # フロントエンドリソース
│       ├── index.html         # メインHTMLシェル
│       ├── components/        # 分割HTMLコンポーネント (left_pane, center_pane, right_pane, モーダル)
│       ├── css/
│       │   └── style.css      # スタイルシート (Elite HUD テーマ、バッジ、レスポンシブ)
│       └── js/
│           ├── app.js         # UI初期化、イベントリスナー、グローバル状態、ホットキー、検索ボックス制御
│           ├── system_list.js # 星系一覧、フィルターアコーディオン、一括クリア、ソート
│           ├── system_map.js  # System Map (Orrery、天体階層ツリー、バッジ、FSS/DSS価格バッジ)
│           ├── inspector.js   # 右ペイン天体詳細、物理情報、Exobiology、ブックマーク・メモ編集
│           ├── mining_view.js # 採掘支援ビュー (ホットスポット、PMLリスト、Mining Scout判定)
│           ├── utils.js       # フォーマット関数 (formatCredits, formatKiloCredits, formatDistance 等)
│           └── i18n.js        # 日英バイリンガル辞書 & 翻訳エンジン (t 関数)
└── tests/                     # pytest 単体・統合テストスイート
```

---

## 3. データベーススキーマ (SQLite Schema)

データベースファイル: `journal_analysis.db`（`app/db/database.py` で定義・初期化）

### 3.1 `systems` テーブル (星系メタデータ)
| カラム名 | 型 | 説明 |
|---|---|---|
| `system_address` | INTEGER (PK) | 星系固有アドレス (ED 内部ユニークID) |
| `star_system` | TEXT NOT NULL | 星系名称 |
| `star_pos_x`, `star_pos_y`, `star_pos_z` | REAL | 銀河3次元座標 (Sol 基準 Ly, 0.0 は有効値) |
| `population` | INTEGER | 星系人口 |
| `first_visited`, `last_visited` | TEXT | 初回 / 最終訪問日時 (ISO8601 UTC) |
| `visit_count` | INTEGER | 訪問回数 |
| `total_bodies`, `scanned_bodies` | INTEGER | 星系内総天体数 / スキャン済み天体数 |
| `main_star_type` | TEXT | 主星スペクトル型 (例: `F`, `M`, `Neutron`) |
| `total_fss_value`, `total_dss_value` | INTEGER | 星系全体の FSS 価値合計 / DSS 価値合計 |
| `total_bio_value`, `total_bio_signals`| INTEGER | Exobiology 基礎報酬合計 / 生体シグナル総数 |
| `has_elw`, `has_water_world`, `has_ammonia` | INTEGER (0/1) | 地球型 (ELW) / 海洋 (WW) / アンモニア惑星フラグ |
| `has_terraformable`, `has_bio` | INTEGER (0/1) | TF可能天体 / 生体シグナル保有フラグ |
| `has_landable`, `has_high_g` | INTEGER (0/1) | 着陸可能天体 / 高重力 (3G+) フラグ |
| `has_anomalies` | INTEGER (0/1) | 特殊・軌道異常天体保有フラグ |
| `is_shared` | INTEGER (0/1) | 外部共有パッケージからインポートされた星系か否か |
| `is_external` | INTEGER (0/1) | EDSM等から先行照会された未訪問星系フラグ |
| `mining_scout_grade` | TEXT | 採掘有望度 (`high`, `medium`, `''`) |

### 3.2 `bodies` テーブル (天体データ)
| カラム名 | 型 | 説明 |
|---|---|---|
| `id` | INTEGER (PK AUTO) | 内部サロゲートキー |
| `system_address` | INTEGER NOT NULL | 所属星系アドレス |
| `body_id` | INTEGER | 星系内天体ID (0: 主星, 1〜: 惑星・衛星) |
| `body_name` | TEXT NOT NULL | 天体正式名称 |
| `distance_from_arrival_ls` | REAL | 到着点（主星）からの距離 (Ls, 0.0 は主星の有効値) |
| `star_type` | TEXT | 恒星スペクトル型 (恒星の場合のみ。惑星は NULL) |
| `planet_class` | TEXT | 惑星分類 (例: `High metal content body`, `Earthlike body`) |
| `mass_em`, `radius` | REAL | 地球質量比 / 半径 (m) |
| `surface_gravity_g` | REAL | 表面重力 (G単位: 1G = 9.81 m/s², 0.0 は有効値) |
| `surface_temperature` | REAL | 表面温度 (K) |
| `landable` | INTEGER (0/1) | 着陸可能フラグ |
| `volcanism` | TEXT | 火山活動種別 (例: `Major Water Geysers`) |
| `semi_major_axis`, `eccentricity`, `orbital_inclination` | REAL | 軌道長半径 (m), 離心率 (0.0〜1.0), 軌道傾斜角 (deg) |
| `orbital_period`, `rotation_period` | REAL | 公転周期 (s), 自転周期 (s) |
| `rings` | TEXT (JSON) | **ED公式環リスト形式**: `[{"Name": str, "RingClass": str, "MassMT": float, "InnerRad": float, "OuterRad": float}]` |
| `materials` | TEXT (JSON) | 地表資源比率辞書 |
| `parents` | TEXT (JSON) | **ED公式階層リスト形式**: `[{"Null": 1}, {"Star": 0}]` 等の親天体・連星重心インデックス配列 |
| `was_discovered`, `was_mapped` | INTEGER (0/1) | 到達時点で既に他者によって発見 / マップ済みだったか |
| `is_mapped_by_user` | INTEGER (0/1) | **プレイヤー自身が DSS マッピングを完了したか (1: 完了, 0: 未完了)** |
| `bio_signals`, `geo_signals`, `mining_signals` | INTEGER | 生体 / 地質 / 採掘シグナル数 |
| `fss_value` | INTEGER | FSS スキャン完了時推定クレジット価値 |
| `dss_value` | INTEGER | DSS マッピング完了時推定クレジット価値 (効率ボーナス込) |
| `confirmed_genuses` | TEXT (JSON) | 採取完了した生体属リスト |
| `exobiology_predictions` | TEXT (JSON) | 生体生息予測結果 |
| `anomalies_json` | TEXT (JSON) | 軌道力学・物理特性のレア度判定結果 (`{"score": int, "tags": list[str], "details": dict}`) |

---

## 4. コアロジック & 計算パイプライン (Business Logic)

### 4.1 探査クレジット価値計算 (`value_calculator.py`)
Elite Dangerous 3.3 以降の探査価値公式を完全再現：
- **基礎FSS価値 (`fss_value`)**: 質量と天体種別（ELW, WW, Ammonia, TF可能HMC等）に基づく基礎額。未発見の場合は初回発見ボーナス（×2.6）が加算。
- **DSSマッピング価値 (`dss_value`)**: FSSスキャンに加えてDSSを行った場合の総額。効率目標弾数以内で完了したボーナスを含む。
- **初回マッピングボーナス (`first_mapped_dss`)**: 未マップ天体を初マッピングした場合の追加額。

### 4.2 天体物理・星系年齢のルールベース判定 (`app/parser/rarity_scorer.py`)
LLMを用いず、EDジャーナルの確定値（`Scan` イベント）から数理モデルと閾値判定でスコアおよび異常タグ（`anomalies_json`）を算出する。

1. **星系年齢（`Age_MY`）と恒星進化矛盾**:
   - 超若年星系: `Age_MY < 10` (+20pt, タグ: `"Ultra-Young System"`)
   - 超古代星系: `Age_MY > 12500` (+20pt, タグ: `"Ancient Population II"`)
   - 恒星進化矛盾: O/B型星なのに `Age_MY > 300` (+30pt, タグ: `"Stellar Evolution Anomaly (O/B Over-aged)"`)
2. **軌道力学的極限（Orbital Mechanics）**:
   - 極端離心率: `Eccentricity >= 0.9` (+30pt, タグ: `"Hyper-Eccentric"`) / `0.8 <= Eccentricity < 0.9` (+15pt, タグ: `"High Eccentricity"`)
   - 逆行軌道: `abs(OrbitalInclination) > 90` (+25pt, タグ: `"Retrograde Orbit"`)
   - 極軌道: `85 <= abs(OrbitalInclination) <= 95` (+15pt, タグ: `"Polar Orbit"`)
   - 極短周期公転（ホット・オービット）: 惑星かつ `OrbitalPeriod < 86400`（1日未満） (+20pt, タグ: `"Ultra-Short Period"`)
   - 異常な自転軸傾斜: `80 <= abs(AxialTilt * 180 / PI) <= 100` (+15pt, タグ: `"Extreme Axial Tilt (Sideways)"`)
3. **密度・構造極限（Density & Radius）**:
   - 平均密度 $\rho = \text{Mass} / (\frac{4}{3}\pi \text{Radius}^3)$ を算出（地球質量 $5.9722 \times 10^{24}\text{ kg}$、半径 $m$ から $\text{g/cm}^3$ へ換算）。
   - クトニア惑星候補（異常高密度）: 岩石/金属天体で $\rho > 15.0 \text{ g/cm}^3$ (+30pt, タグ: `"Super-Dense Core"`)
   - パフ・プラネット（超低密度ガス天体）: ガス巨人/巨大ガス天体で $\rho < 0.1 \text{ g/cm}^3$ (+25pt, タグ: `"Super-Puff Planet"`)
4. **特殊環（Ring Systems）**:
   - 巨大リング: 環の幅 $(OuterRad - InnerRad) > 10 \times Radius$ (+20pt, タグ: `"Massive Ring System"`)
   - 恒星・希少惑星の環: 恒星、または地球型(ELW)/アンモニア(AW)に環が存在 (+35pt, タグ: `"Exotic Ring Host"`)
5. **総合スコア化 & JSON出力**:
   - 各加点の合算値を `rarity_score` とする。
   - レスポンス形式: `{ "score": int, "tags": list[str], "details": dict }`

### 4.3 Exobiology（生体採取）予測 (`exobiology.py`)
- 天体の大気種別、表面温度、重力、恒星スペクトル型、惑星分類を条件マトリクスと照合。
- 生息可能な植物・菌類候補（Genus / Species）を抽出し、基本採取額および初回ボーナス（×5倍）を算出。
- 生体採取に必要な最低コロニー離隔距離（Colony Distance, 例: 100m, 500m, 800m）を提示。

---

## 5. フロントエンド設計 & UI状態管理 (Frontend Architecture)

### 5.1 グローバル状態管理 (`state` in `app.js`)
すべての UI 状態は `app.js` 内のグローバル `state` オブジェクトに保持される。

### 5.2 星系検索ボックス (`#system-search`)
- **リアルタイム検索**: 入力後 300ms デバウンスで星系絞り込み API を呼出。
- **右クリック即時ペースト機能**:
  - 検索ボックスが**空のときのみ**、右クリック（`contextmenu`）でクリップボードの文字列を自動取得・空白トリムして即座に挿入し、検索を実行。
  - すでに文字が入力されているときは挿入を行わず、通常のコンテキストメニューを表示。

### 5.3 フィルターアコーディオン & 一括クリアボタン
画面左ペインの各アコーディオンヘッダー右端に一括クリアボタン（`btn-page`, `data-i18n="filter_clear"`）が設置されている：
1. **一般天体・属性フィルター**: `#btn-clear-general-filters`
2. **天体特性・軌道フィルター**: `#btn-clear-celestial-filters`
3. **星系内恒星フィルター (複数検索)**: `#btn-clear-stars-filters`
   - クリック時 `e.stopPropagation()` でアコーディオンの開閉を抑止。
   - プルダウン内の恒星種別（`.star-filter-cb`）・光度階級（`.lum-filter-cb`）のチェックを全解除し、条件モードラジオボタンをデフォルトの `any`（OR）に戻し、バッジと一覧を即時更新。
4. **採掘・Landableフィルター**: `#btn-clear-mining-filters`

### 5.4 System Map (Orrery & 階層ツリー) の描画仕様 (`system_map.js`)
- **階層構造**: 主星（Root Star）から周回惑星、衛星、小惑星帯（Asteroid Belt）、連星共通重心（Barycentre）を親子ツリーとして配置。
- **天体価格バッジ (FSS / DSS Bonus)**:
  - **配置**: 他のバッジの横に並べるのではなく、**必ず一番下に改行された独立コンテナ `<div class="sysmap-price-row">` として中央配置**。
  - **DSS Bonus 判定ロジック (厳格化)**:
    `was_mapped` による他者の事前マップ履歴と混同しないため、**「プレイヤー自身がマッピング完了した天体」のみを DSS Bonus の対象とする**。
    ```javascript
    const isUserMapped = Boolean(body.is_mapped_by_user) && ((body.dss_value ?? 0) > 0);
    const targetPrice = isUserMapped ? body.dss_value : body.fss_value;
    const priceLabel = isUserMapped ? 'DSS Bonus' : 'FSS';
    const badgeClass = isUserMapped ? 'dss' : 'fss';
    ```
    価格が 0 または存在しない天体（小惑星帯、連星共通軌道等）は非表示。
  - **数値フォーマット (`formatKiloCredits` in `utils.js`)**:
    - 最低価格桁は **Kilo (`k`)**。M（メガ）単位は使用しない。
    - 100k 未満（例: 7,592 Cr）: 小数第1位に四捨五入（`7.6k`）。
    - 100k 以上（例: 4,700,000 Cr）: 四捨五入して整数（`4700k`）。
    - 末尾の `Cr` は表記せず、先頭の `FSS` または `DSS Bonus` で価格であることを識別。
    - ホバー時の `title` 属性にはフルクレジット額（例: `DSS Bonus: 4,700,000 Cr`）を表示。

---

## 6. REST API 仕様 & レスポンス統一規格 (`app/server/api.py`)

### 6.1 API レスポンス統一規格
バックエンド API は、クライアント側でのエラーハンドリングおよび型安全性を担保するため、以下の統一フォーマットに準拠する。

#### 成功時レスポンス (HTTP 200 / 201)
```json
{
  "status": "success",
  "data": { ... } // 配列またはオブジェクト
}
```
※ 既存の互換性維持エンドポイントにおいてオブジェクトが直下に返される場合でも、新規・改修エンドポイントは上記ラッパー構造を原則とする。

#### エラー時レスポンス (HTTP 4xx / 5xx)
FastAPI 標準の `HTTPException` に準拠：
```json
{
  "detail": "エラーメッセージの説明"
}
```

### 6.2 主要エンドポイント一覧
| メソッド | パス | 説明 |
|---|---|---|
| `GET` | `/api/systems` | 星系一覧取得（検索文字列、各種フィルターパラメータ、ページネーション対応） |
| `GET` | `/api/system/{system_address}` | 指定星系の詳細メタデータおよび全天体（`bodies`）リスト取得 |
| `POST`| `/api/scan_now` | フライトログフォルダの手動再スキャン開始 |
| `GET` | `/api/scan_status` | ログ解析の進捗状況取得 |
| `GET` | `/api/events/latest` | 直近のジャーナルイベント取得（リアルタイム監視用） |
| `POST`| `/api/bookmark` | 天体ブックマーク・エイリアス・Markdownメモの保存 |
| `DELETE`| `/api/bookmark/{system_address}/{body_id}` | 天体ブックマークの削除 |
| `POST`| `/api/systems/{system_address}/edsm_sync` | 指定星系の EDSM データオンデマンド照会・同期 |
| `POST`| `/api/systems/{system_address}/spansh_sync`| 指定星系の Spansh 採掘データオンデマンド照会・同期 |
| `GET` | `/api/export/html/{system_address}` | Standalone Web共有HTMLファイルの生成・出力 |
| `GET` | `/api/export/image/{system_address}` | ComfyUI 方式メタデータ埋め込みPNGサマリー画像の生成 |
| `GET` | `/api/export/snippet/{system_address}` | SNS / Twitch 配信向け短評テキストの生成 |
| `GET` | `/api/app_settings` / `POST` | アプリケーション各種設定（テーマ、モジュール表示、TTS設定等）の取得・更新 |

---

## 7. LLM 改修ガイドライン & 開発規約 (Safety Rules for LLMs)

外部LLMや開発者が本プロジェクトに変更を加える際は、以下の規約を厳格に遵守してください。

### 7.1 Anti-Hallucination & SSOT 規約
- **推測・捏造の禁止**: 存在しないカラム、パラメータ、未知のEnum値、架空の天体種別を勝手に追加しない。
- **データ分離**: 新しい分類や静的データ（天体種別リスト、鉱石リスト等）を追加する場合は、ロジック内に直接記述せず、設定ファイルまたは専用定数モジュールに切り出す。

### 7.2 NULL安全性 & エラーハンドリング (厳格ルール)
1. **Python**:
   - `0`, `0.0`, `False`, `""` を有効値として扱うため、`or` によるデフォルト値代入（`val or default`）を禁止する。
   - `dict.get(key, default)` は、キーが存在して値が `None` の場合に `None` を返すため、必ず `val if val is not None else default` で明示的に None ガードを行うこと。
2. **JavaScript**:
   - `val || default` を禁止し、Nullish Coalescing (`val ?? default`) を使用すること。
   - 文字列操作（`.trim()`, `.toLowerCase()` 等）の前には必ず未定義・null チェックを行うこと。

### 7.3 Git プロトコル
1. **`main` への直接コミット禁止**: 必ずトピックブランチ（`feat/...`, `fix/...`, `docs/...`）を作成して作業する。
2. **単一責務の原則 (1 Task = 1 Branch)**: 依頼された単一のタスクのみにスコープを限定し、無関係なリファクタリングやフォーマット変更を行わない。
3. **Conventional Commits の遵守**: `feat:`, `fix:`, `refactor:`, `test:`, `docs:`, `chore:` をプレフィックスとする。
4. **自動 push の禁止**: `git push` はユーザーの明示的な許可があるまで絶対に実行しない。

### 7.4 テスト & 整合性検証
- JavaScript 変更時は `node -c <file_path>` で構文エラーがないことを確認する。
- Python 変更時または機能追加後は、必ず `pytest -q`（または該当テストスライス）を実行し、全テストがパスすることを確認する。
