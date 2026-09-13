# Elite Dangerous Journal Analyzer & Exploration Orrery (v0.1.7)

[日本語](#日本語) | [English](#english)

---

<a name="日本語"></a>
## 概要 (日本語)

Elite Dangerousのフライトジャーナルログ（`Journal.*.log`）を自動解析・リアルタイム監視し、過去に訪れた星系・天体の状態、位置関係・軌道情報、レア天体・特殊周回、着陸可否・重力・火山活動、Exobiology（植物・菌類）の生息予測と報酬額、FSS/DSS探査価値の精密計算、Rhino採掘支援（重力・温度表示）、天体ブックマーク・エイリアス・Markdownメモ、UIフォントサイズ実数値拡縮機能を提供するローカルデスクトップGUIアプリケーションです。

> **「あの時訪れたあの星は、どんな宙域だっただろう？」**  
> 銀河の遥かなる長旅の記録や、過去の深宇宙探索・初発見の思い出をいつでも鮮明に振り返ることができます。

> **⚠️ 使用上の注意・免責事項**: 本ツールはファンメイドの非公式オープンソースツールです。フロンティア・デベロップメンツ社とは一切関係ありません。ジャーナルログの解釈や探査・採掘データの完全性についてはいかなる保証も致しかねます。本ツールの使用によって生じたゲーム内での損失（機体喪失、採掘リグ耐久値損失、探査データ喪失など）を含むいかなる結果についても開発者は一切の責任を負いません。自己責任においてご利用ください。

### 🚀 v0.1.7 アップデート・サマリー
- **EDSM天体データに基づく採掘有望度スコア & 検索フィルター新設**:
  - EDSM天体データおよびジャーナル走査により、埋蔵量（Reserve Level）が **Pristine（最高）** かつ高価値リングを持つ星系を自動判定。
  - **⛏️ Scout: High**: Pristine + Metallic（金属質）リング（プラチナ・ペイン石など高価値レーザー採掘向け最有望星系）。
  - **⛏️ Scout: Med**: Pristine + Icy（氷）リング（トリチウム・低温ダイヤモンド等向け有望星系）。
  - 星系カードおよび詳細ヘッダーにバッジ表示されるほか、左側パネルの採掘フィルターに「すべて / High / Med」チップフィルターを新設。
- **無駄足を防ぐ大型着艦パッド（Has Large Pad）＆ 到着距離（Arrival Distance）フィルター**:
  - **🚀 大型パッド（Large Pad）**: 大型宇宙船（Anaconda、Cutter、Type-9等）が着艦可能な Starport、Planetary Port、Megaship、Carrier を持つ星系のみを瞬時に抽出。
  - **到達距離フィルター**: 星系内のステーションや天体までの到達距離（< 2,000 Ls、< 10,000 Ls、< 50,000 Ls、指定なし）で絞り込み可能。何十万Lsもの長距離スーパークルーズ移動を未然に防止します。
- **リングDSSスキャン（ホットスポット）の天体Markdownメモ自動記録**:
  - リング天体へのDSS（詳細サーフェススキャナー）実施時に発生する `SAASignalsFound` イベントを自動検知。
  - プラチナ、ペイン石、トリチウム等のホットスポット名と重複数を集計し、天体のMarkdownメモへ `### 🪐 Ring DSS Scan (Hotspots)` として自動追記・更新。
- **天体メモへのリアルタイム現在地座標ワンクリック挿入**:
  - 天体詳細インスペクターのブックマーク・Markdownメモ編集欄に「📍 座標挿入（Insert Coords）」ボタンを新設。
  - `Status.json` または最新の地表探査ログから現在の緯度・経度を即座に取得し、エディタのカーソル位置へ自動挿入。地表採掘地点やレア拠点の記録が格段にスムーズになりました。

### 🚀 v0.1.6 アップデート・サマリー
- **Web共有HTMLの「対話的マルチ恒星オーラリー（連星系・伴星・周回軌道図）」新設**:
  - 従来のWeb共有HTMLで主星以外の伴星（Companion Stars: B, C, D...）が表示されなかった不具合を根本解決。
  - 主星（A星）だけでなく、連星系における伴星（B星など）、伴星を周回する惑星（B 1, B 2...）、および惑星を周回する衛星（B 1 a...）を包括した完全な階層構造（Orbital Hierarchy）を描画。
  - 到着距離（Ls）に応じた対数スケール軌道円および距離ラベルを表示し、星系全体の空間配置を一目で直感的に把握可能。
- **無段階パン＆ズーム（0.12x〜40x）＆ 恒星クイックジャンプバー**:
  - マウスホイールによる滑らかな無段階ズーム、ドラッグによるパン移動、モバイル/タブレットのピンチズーム・ドラッグに対応。
  - 最大40倍までズームイン可能なため、伴星周りの惑星系や微小な衛星軌道まで明瞭にクローズアップ観察可能。
  - 上部に新設された「恒星クイックジャンプバー」（`[☀️ 主星 A]`、`[⭐ 伴星 B (12,450 Ls)]`等）をワンクリックするだけで、対象天体へカメラが瞬時にフォーカス移動＆ズームイン。
- **天体ホバー情報ツールチップ ＆ 完全スタンドアロン維持**:
  - オーラリー上の天体にマウスホバー（タッチ）することで、天体名、分類、到着距離、表面重力、表面温度がポップアップ表示。
  - 外部CDNや外部JS/CSSライブラリへの依存を一切持たず、単一HTMLファイル内でSVG対話制御・全天体物理JSON内包・AI推論対応が完全自己完結。

### 🚀 v0.1.5 アップデート・サマリー
- **Web共有HTMLの「完全天体物理観測JSON内包」＆ AI推論対応化**:
  - 生成されるスタンドアロンWeb共有HTML（`{星系名}_share.html`）内に、星系および全天体の完全な天体物理・軌道観測データ（恒星・惑星質量、精密半径、軌道長半径、離心率、公転・自転周期、軸傾斜、詳細大気組成比率など）を `<script type="application/json">` としてまるごと内包。
  - **人間向けの美しい星系図ビューアー**でありながら、**各種生成AI（ChatGPT、Claude、Gemini等）に本HTMLファイルをそのまま渡すだけで、100%の精度で星系形成史シナリオや天体物理学的考察を推論させることができる「完全データコンテナ」**へ進化しました。
  - 天体一覧テーブルの各行に「🔬 詳細天体物理パラメータ (AI推論用)」アコーディオンを新設。ブラウザ上で質量、半径、AU軌道長半径、離心率、大気組成比率を人間も即座に確認できます。
- **Web共有HTMLの保存先自動特定＆エクスプローラー直接オープン機能**:
  - デスクトップGUI（pywebview）環境でHTMLを出力した際、保存先が分からなくなる問題を解消。
  - アプリ実行場所直下の **`exports/`** フォルダへ確実に自動保存し、生成完了と同時に**Windowsエクスプローラーが自動起動して該当ファイルをハイライト表示**します。
  - 画面上にも保存先フルパスと「📂 保存フォルダーを開く」ボタン付きトースト通知を表示し、迷子を100%防止。

### 🚀 v0.1.4 アップデート・サマリー
- **未訪問星系（EDSM/Spansh/Inara既知）ロード時の404エラー解消**:
  - 自身が訪問していない未訪問星系（Sol、Beagle Point等）を外部DB足跡チェックから「🚀 EDSMから星系データをロード（未訪問参照）」した際に、EDSM APIリクエストに `&showId=1` が欠落していたことでシステムアドレス（`id64`）が取得できず404エラーになっていた不具合を根本解決。
  - EDSM上のあらゆる未訪問星系・天体データを100%確実にインポートし、System Mapで軌道構造や天体スペックを即座に閲覧できるようになりました。
- **Elite Dangerous 固有のHUDカラーテーマを含む「UIカラーテーマ切り替え」新設**:
  - 設定モーダル（UI表示設定タブ）に「🎨 UIカラーテーマ / 配色プリセット」を追加。
  - **🌌 Modern Deep Space**: 視認性に優れた標準ハイコントラスト配色（ダークブルー＋アンバー）。
  - **🚀 Elite Classic Amber HUD**: 原作Elite Dangerousのコックピット計器盤・ホログラフィックHUDのアンバーオレンジ配色（`#ff7100` / `#ffaa33`）を忠実に再現。
  - **🌐 Cyan Explorer HUD**: サイバー調の深宇宙探査機向けシアン・ブルー配色。
  - 選択したテーマは画面リロードなしで即座にUI全体へ反映され、次回起動時も永続化されます。

### 🚀 v0.1.3 アップデート・サマリー
- **中央ペイン天体ソートに「Rhino適格 (PML順)」を追加**:
  - 天体ソート（Body Sort）の選択肢に「⛏️ PML数 / Rhino適格 (多い順)」および「⛏️ PML数 / Rhino適格 (少ない順)」を新設。
  - Planetary Mining Locations (PML) のシグナル数が多い惑星・天体を即座にリスト最上部にソート可能。同数の場合は到着距離順に自動タイブレークされます。
- **拡張機能モジュール表示設定（チェックボックスで明示的に消す・戻す）**:
  - 設定モーダルの「UI表示設定タブ」に「🧩 拡張機能モジュール表示設定」を新設。
  - **🌿 Exobiology モジュール**: 星系一覧や天体ツリーのBIOバッジ、生物候補予測セクション、生物探査ビューをチェックボックス1つで明示的に消す（非表示にする）／戻す（表示する）ことが可能。
  - **🦏 Rhino 採掘モジュール**: 星系一覧の採掘拠点バッジ、惑星表面のRhino採掘座標マップや履歴カード、採掘適格ビューをチェックボックス1つで明示的に消す／戻すことが可能。
  - 過去の探査ログを純粋な天体物理データとしてシンプルに眺めたい時はチェックを外して消し、旅のしるし（思い出）として振り返りたい時はチェックを入れて戻すという自由な運用が可能です。
- **旅のしるし（画面表示）とTTS（音声通知）の完全分離 & 個別制御**:
  - 画面上の表示（生物予測・バッジ・採掘拠点）は大切な探査の思い出として維持したまま、ゲームプレイ中に気になるTTS（音声読み上げ）のみを個別スイッチで安全に外す（OFFにする）ことができます。
  - 「未発見（1st Discover）読み上げ通知」と「高額生物天体 (40M+ Cr) 通知」を独立化し、高額生物通知の初期設定を静音（OFF）に配慮。
- **設定の安全永続化**:
  - モジュール表示設定はブラウザのローカルストレージに加え、バックエンド（`Data/module_settings.json`）にも自動同期保存。

### 🚀 v0.1.2 アップデート・サマリー
- **Rhino 採掘記録（緯度経度 ＆ 掘れた鉱物）の惑星メモ簡潔追記機能**:
  - メモ欄の美しさと容量効率を最優先し、冗長なタイムスタンプや全生ログの羅列を排除。
  - **「緯度経度」とともに「何を掘ったか（掘れた鉱物・素材）」だけ**をシンプルかつコンパクトに惑星のメモ（Markdownノート）へ追加記述（追記）する仕組みを新設。
  - 同一地点でさらに新しい鉱物を掘った場合、行数を増やさず既存行の鉱物リストへスマートにマージ統合（例: `- [Lat: +12.3456°, Lon: -45.6789°]: ゲルマニウム, 鉄, テクネチウム`）。既存のユーザー独自メモも100%保持。
  - 天体インスペクターの採掘地点カードに「📝 メモに追記」ボタン、ヘッダーに「📝 全地点をメモに追記」ボタンを新設。ワンクリックで惑星メモ欄（`#bm-note-input`）へ即座に反映可能。
  - ゲームプレイ中の SRV 採掘（マテリアル採取／鉱物精製）時にも、`Status.json` からのリアルタイム精密座標を補完して自動的に惑星メモへスマート記録。
- **アーキテクチャのモジュール分割（「過去のアーカイブ」と「現在のLiveコパイロット」の分離）**:
  - `app/live/` パッケージを新設し、リアルタイム監視・Status.jsonテレメトリ（`telemetry.py`）、ランドマークPOI距離計算（`landmarks.py`）、Rhino採掘追跡＆メモ統合（`live/rhino/`）の責務を綺麗に分離。
  - 将来の天体物理ローカルLLM組み込み（Bonsai Ternary 7B 等による学術ナラティブ生成）に向けた基盤モジュール（`app/analyzer/llm/`）を整備。

### 🚀 v0.1.1 アップデート・サマリー
- **未訪問星系の EDSM オンデマンド参照ロード機能（安全ロック保護付き）**:
  - 検索バー下の「外部DB足跡チェック」で EDSM 足跡（登録）が確認された未訪問星系について、「🚀 EDSMから星系データをロード（未訪問参照）」ボタンを新設。
  - フライト履歴のない星系でもオンデマンドで EDSM より座標・星系情報・全天体データを取得・インポートし、System Map や天体インスペクターで自由に軌道構造・天体スペックを閲覧可能に。
  - **厳格なエクスポート保護（安全ロック）**: 未訪問の外部参照星系（`is_external = 1` または `visit_count = 0`）は、プレイヤー自身の探査記録と混同されないよう、**Web共有HTML生成（`btn-export-html`）およびパッケージ書き出し（`btn-export-pkg`）はUI上で完全非表示化＆バックエンド 403 Forbidden による二重保護ブロック**を徹底。また星系統計（訪問星系数・総探査額）にも加算されません。
  - 星系一覧カードおよび詳細ヘッダーに `🌐 外部参照 (未訪問)` バッジを明示。
- **ヘッダーUIの整理・一本化**:
  - ヘッダー部の「ジャーナル探査」「天体物理」ボタンを左ペイン側のコンセプトタブに一本化し、ヘッダーの横幅を確保して統計情報や現在地表示をより見やすく整理。
- **ヘッダーログスキャンボタンのアイコン重複修正**:
  - ログスキャンボタンでリロードマーク `🔄` が2個並んで表示されていた問題を修正し、1個のスッキリした表示に改善。
- **バージョニング運用ルールの適用**:
  - 通常アップデート時は最下位桁（下3桁目 `v0.0.x`）を繰り上げ（`v0.1.0` → `v0.1.1`）。

### 🚀 v0.1.0 アップデート・サマリー (Major Update)
- **ジャーナル読み込みの低レイヤー堅牢化 & 破損完全防止**:
  - ジャーナル読み取りエンジンをバイナリ（`rb`）ストリーム走査へ全面刷新。
  - Elite Dangerous 本体がログ書き込み中に発生する「行途切れ（Truncated line）」の自動検知・ロールバック機構を新設。
  - ファイル縮小時の自動リセットと相まって、ゲーム側とのファイル競合や不完全行の誤パースを100%防止し、動作の劇的な軽量化を実現。
- **UIレイアウトのオーバーホール & LIVE・ソート双方向同期**:
  - 左ペイン最上段の探査・天体物理タブおよび LIVE トグルボタンの配置を最適化し、文字露出や幅オーバーフローを完全解消。
  - 折りたたみアコーディオン（期間・ソート設定）内にも「⚡ リアルタイム追従中」ガイド行 & 「LIVE解除 / LIVE再開」ボタンを新設。
  - アコーディオンを開いた状態からワンクリックで LIVE を解除し、1次・2次・3次ソートを自由に操作可能（ヘッダーとアコーディオンは完全双方向同期）。
- **System Map（軌道階層ツリー）表示時の天体ソート制御**:
  - 階層ツリーを描画する System Map 表示時は、ツリー構造と無関係な「天体ソート」を自動的に非表示化。天体一覧（Flat View）、Bio、採掘ビューの時のみ表示・連動させて混乱を防止。
- **フィルターチップ初期状態のバグ修正**:
  - 「⭐ 1st Disc」「🔖 ブックマーク」「🤝 Shared」が未選択時でも色が付いて見えていた不具合を修正。未選択時は他のチップと同じグレーで統一し、選択（アクティブ）時のみ鮮やかに点灯。
- **任意ランドマーク距離表示のカスタマイズ設定新設**:
  - 設定モーダル（「画面・文字サイズ」タブ）内に「📍 ランドマーク距離バッジ表示設定」を新設。
  - CMDR現在地、Sol、Colonia、Rainbow's End、Explorer's Anchorage を個別にチェックボックスでON/OFF可能（設定は自動保存され即時反映）。
- **EDSM連携の復活 & 既知星系天体自動補完の優先キュー（Priority Queue）最適化**:
  - EDSM（Elite Dangerous Star Map）連携を完全復活。既知星系へのジャンプインや Honk（`FSSDiscoveryScan`）時に、未スキャン天体の公転軌道・物理データ・探査価値を自動補完。
  - **二重優先度キュー機構**を新設。過去ログ解析によるAPIリクエスト渋滞を防止し、現在地・Honk・UI星系選択・手動同期を常に**最優先（待ち時間ゼロ）**で処理。
  - 星系ヘッダーに「🔄 EDSM同期」ボタンを新設し、過去に補完が漏れていた星系でもワンクリックで即座に EDSM データを再取得・天体補完可能。
  - 天体インスペクターに「⭐ EDSM既知（未スキャン）」バッジおよび「EDSM発見者: CMDR xxx」のクレジット表示を新設。

### 🌐 日英バイリンガル対応 (One-Click Language Switch)
- アプリ画面右上の **`[JP] / [EN]`** ボタンから、日本語・英語をいつでも**ワンクリックで即座に切り替え可能**です。

### 💾 ポータブル設計・`data` フォルダの扱い & アップデート手順
- **レジストリやシステム領域への書き込みは一切行いません**: すべてのデータは実行ファイル直下のローカル領域で完結します。
- **`data` フォルダの役割**:
  - `ED_Journal_Analyzer.exe` を初回実行すると、同じフォルダ内に **`data`** フォルダが自動生成され、過去ジャーナルの解析データ、天体ブックマーク、エイリアス、メモ等の SQLite データベース（`elite_exploration.db`）が格納されます。
- **既存ユーザーのアップデート方法（exe の置き換えだけで即時移行可能）**:
  - 新バージョンへアップデートする際は、**既存の `data` フォルダは絶対に削除せずそのまま残してください**。
  - 新しい `ED_Journal_Analyzer.exe` をダウンロードし、古い exe ファイルに上書き（置き換え）して起動するだけで、**これまでの探査履歴・ブックマーク・メモなどのすべてのデータをそのまま引き継いで即座に移行・利用再開できます**。
  - データベースは起動時に後方互換性を保った自動マイグレーションが行われるため、手動でのデータ移行や再読み込み作業は一切不要です。
- **完全初期化・アンインストール**:
  - アプリを完全に削除したい場合は、`ED_Journal_Analyzer.exe` と `data` フォルダを手動で削除するだけで、PC内に一切の痕跡を残さず綺麗にアンインストールされます。

### 主な機能 (Key Features)

- **UIフォントサイズ実数値拡縮機能 & セーフティ機構**:
  - 設定モーダルに「🖥️ 画面・文字サイズ」タブを新設。**18px**（標準中間サイズ）をデフォルトとし、最小目安 **14px** から任意のpx実数値を直接指定可能。
  - バッジやパネルが一列から自然に折り返され、文字数や情報を欠落させずに縦長にフィット。
  - 右上「⚙️ 設定」ボタンは常に最前面に固定表示され、極端な数値入力時でも <kbd>Ctrl + 0</kbd> で即座に標準 (18px) に復旧可能。
- **5大銀河ランドマーク距離表示 & 個別カスタマイズ**:
  - CMDR現在地、Sol、Colonia、Rainbow's End (DW3)、Explorer's Anchorage (Sgr A*) からの直線距離（Ly）を星系カードおよびインスペクターに自動算出・表示。設定画面から表示したいランドマークを自由に選定可能。
- **採掘支援 重力 (G)・温度 (K) 可視化 & 採掘パネル併記**:
  - 採掘ビューの天体カードにおいて、表面温度・大気欄に加えて **重力 (G)** も一行に並べて表示。
  - 採掘Rig耐久値管理に直結する重力 (G)・表面温度 (K) の表示トグルを左パネルに完備。
  - 星系カード最下段のLandableバッジは、左パネルでオンにした採掘フィルターに該当する天体のみがスマートに表示されるよう連動。
- **LIVE（リアルタイム）ボタンの配置最適化 & ソート解除**:
  - 左ペイン最上段とアコーディオン内の両方に配置。ワンクリックで LIVE 解除と手動ソートの切り替えが可能。
  - ジャンプ到着待機（Honk待機）中であっても、LIVEボタンを押すことで即座に最新星系の現状データを閲覧可能。
- **天体ブックマーク・エイリアス（別名・通称）・Markdownメモ帳**:
  - 天体単位でのブックマーク登録、ユーザー定義通称（例: `採掘拠点 Alpha`, `TF候補1`）、Markdown形式メモ（リアルタイムプレビュー対応）。
  - 星系検索欄で、星系名だけでなく **「天体名」「エイリアス名」「メモ本文」を横断した全文検索** が可能。
  - フィルターチップ「🔖 ブックマーク」による登録天体星系の瞬時絞り込み。
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

### 🌌 生成AIを活用した天体物理学的考察・星系形成史シナリオの推論 (LLM Prompting)

本アプリで解析・管理される星系観測データ（またはエクスポートされた星系JSON / edsysデータ）を、各種生成AI（ChatGPT、Claude、Gemini、ローカルLLMなど）に読み込ませて以下のプロンプトを入力することで、現代の天体物理学・惑星科学に基づいた高精度な学術的考察や、星系形成史シナリオ、臨場感あふれる情景描写を推論させることができます。

#### 💡 推論用プロンプト・テンプレート

```text
添付したJSONデータは、宇宙シミュレーションゲーム『Elite Dangerous』の星系観測ログです。

この星系に存在する天体配置、物理パラメータ（質量・半径・表面温度・大気圧・組成）、軌道要素（軌道長半径・離心率・公転周期）を天体物理学・惑星科学の観点から詳細に精査してください。

その上で、以下の内容について考察と解説をお願いします：

1. **物理的なリアリズムと矛盾点**:
   - 現代天文学・惑星形成理論から見て「あり得る点」と「物理的に不自然・矛盾している点（ゲーム的デフォルメやプロシージャル生成の癖）」の切り分け。
2. **星系の形成史シナリオ（成り立ちの仮説）**:
   - もしこの星系が実在すると仮定した場合、主星の進化（前駆星から現在に至るまで）、惑星系の誕生（原始惑星系円盤またはフォールバック・ディスク等）、軌道の進化（真円化や重力散乱）、そして現在の温度・大気が維持されているメカニズムについて、時系列に沿った詳細な科学的仮説シナリオ。
3. **天文学的・観測的な特異性と景観の描写**:
   - この星系特有のレアリティの解説、およびもし人類がこの惑星（特に地球型天体）の地表や軌道上に立った場合に観測されるであろう天球・空・環境の情景描写。

※お世辞や定型句は省き、学術的な査読論文の解説や専門的なフィールドノートのようなトーンで論理的に解説してください。
```

### 起動方法

```powershell
# デスクトップGUIウィンドウとして起動
python run.py

# ブラウザで起動する場合
python run.py --browser
```

起動後、右上の「**ログ再スキャン (Rescan Logs)**」をクリックすると、全ジャーナルファイルが一括インデックス化されます。
アップデート時dataフォルダを残して、他ファイルをアップデートすることでログの再読み込みが発生しなくなります。
---

<a name="english"></a>
## Overview (English)

A local desktop GUI application that automatically parses and monitors Elite Dangerous flight journals (`Journal.*.log`). It provides comprehensive exploration insights including historical system/body records, orbital hierarchy trees, rare celestial anomalies, surface gravity & volcanism, Exobiology habitat predictions & payouts, precise FSS/DSS exploration value calculations, Rhino SRV mining support (gravity & temperature toggles), celestial body bookmarks with custom aliases, and Markdown notes.

> **"What kind of world was that memorable planet I visited long ago?"**  
> Relive and explore your epic expedition memories, first discoveries, and galaxy travels anytime with complete offline privacy.

> **⚠️ Disclaimer**: This tool is an unofficial, fan-made open-source companion and is not affiliated with or endorsed by Frontier Developments plc. No warranties are provided regarding data accuracy or game log interpretation. The developer assumes no responsibility or liability for any in-game losses or damages (including loss of ships, mining rig durability, or exploration data). Use at your own discretion.

### 🚀 v0.1.7 Update Summary
- **EDSM Mining Scout Candidate Score & Filter**:
  - Evaluates system mining potential by checking for **Pristine** resource reserves and high-value ring types.
  - **⛏️ Scout: High**: Pristine + Metallic rings (prime candidate for laser mining platinum, painite, etc.).
  - **⛏️ Scout: Med**: Pristine + Icy rings (candidate for tritium, low-temperature diamonds, etc.).
  - Visual badges displayed on system cards and system headers, with interactive quick filter chips ("All / High / Med") in the mining filter group.
- **Station Pad Size & Arrival Distance Filters (Prevent Fruitless Long Trips)**:
  - **🚀 Large Pad Checkbox**: Filter systems containing starports, planetary ports, megaships, or carriers equipped with Large Landing Pads suitable for large exploration and trade vessels (Anaconda, Cutter, Type-9, etc.).
  - **Max Arrival Distance Select**: Filter stations and bodies by arrival distance thresholds (< 2,000 Ls, < 10,000 Ls, < 50,000 Ls, or Any), saving commanders from unnecessary hundreds of thousands Ls supercruise trips.
- **Automated Ring DSS Scan (Hotspot) Logging into Markdown Notes**:
  - Automatically captures `SAASignalsFound` events on planetary rings.
  - Formats detected hotspots (e.g., Platinum x2, Painite x1, Tritium x3) and appends or updates them cleanly under `### 🪐 Ring DSS Scan (Hotspots)` in the body's Markdown note.
- **One-Click Live CMDR Surface Coordinates Insertion**:
  - Added a "📍 Insert Coords" button directly in the Body Inspector bookmark note editor.
  - Pulls real-time telemetry from `Status.json` (or latest surface activity) and inserts the commander's current planetary coordinates directly at the editor cursor.

### 🚀 v0.1.6 Update Summary
- **Interactive Multi-Star Orrery & Companion Orbit Hierarchy in Web Share HTML**:
  - Fixed an issue where companion stars (B, C, D...) and their orbiting planetary systems were omitted in exported HTML orrery views.
  - Renders complete hierarchical celestial orbital structures, including primary stars, companion binary stars, their orbiting planets (B 1, B 2...), and moons (B 1 a...).
  - Incorporates logarithmic scale orbital guide circles and distance labels based on arrival distance (Ls), giving commanders an intuitive spatial map of massive multi-star systems.
- **Infinite Pan & Smooth Zoom (0.12x - 40x) & Stellar Quick Jump Navigation**:
  - Smooth zooming via mouse wheel, pan by drag, and mobile/tablet touch pinch-zoom gestures.
  - Zoom up to 40x to inspect dense planetary and lunar subsystems orbiting distant companions.
  - Quick jump buttons (`[☀️ Star A]`, `[⭐ Star B (12,450 Ls)]`, etc.) instantly reposition and zoom the camera onto the selected stellar center.
- **Interactive Hover Tooltips & 100% Zero-Dependency Standalone Self-Containment**:
  - Hovering or tapping any celestial body in the Orrery reveals key telemetry: body name, classification, arrival distance, surface gravity, and temperature.
  - Remains completely standalone in a single file without external CDN links or network requirements.

### 🚀 v0.1.5 Update Summary
- **Embedded Complete Astrophysical Observation JSON in Web Share HTML & Full AI Inference Readiness**:
  - Standalone Web Share HTML files (`{system}_share.html`) now embed the complete astrophysical and orbital observation dataset (stellar & planetary masses, precise radii, semi-major axes, eccentricities, orbital/rotational periods, axial tilts, and exact atmospheric composition ratios) directly inside a `<script type="application/json">` block.
  - Acts both as a zero-dependency beautiful orbital system viewer for humans, and an all-in-one data container: simply drag and drop the HTML file into Generative AI models (ChatGPT, Claude, Gemini, etc.) alongside scientific prompts to deduce accurate stellar history and formation scenarios.
  - Added expandable "🔬 Detailed Astrophysical Parameters" rows to each celestial body table for instant human inspection of key physical numbers.
- **Dedicated `exports/` Folder & Automatic File Explorer Reveal**:
  - Solved the issue where desktop pywebview environments saved HTML files invisibly without showing download directories.
  - Automatically writes exported HTML files directly into a dedicated **`exports/`** directory next to the application, and instantly reveals and highlights the exported file in Windows File Explorer.
  - Added an interactive on-screen completion toast displaying the full file path and an instant "📂 Open Folder" action button.

### 🚀 v0.1.4 Update Summary
- **Resolved HTTP 404 Bug When Loading Unvisited Systems (EDSM / Spansh / Inara)**:
  - Fixed a critical issue where attempting to load unvisited systems (e.g. Sol, Beagle Point) via "🚀 Load System Data from EDSM" resulted in a 404 error due to missing `&showId=1` query parameter in the EDSM API request.
  - Now 100% reliably imports system coordinates, addresses (`id64`), and all orbital body data directly into the System Map for reference exploration.
- **Cockpit-Authentic "UI Color Theme Selector"**:
  - Added "🎨 UI Color Theme Presets" in the Settings modal (UI Settings tab).
  - **🌌 Modern Deep Space**: Default high-contrast dark space aesthetic (Deep Blue & Orange Amber).
  - **🚀 Elite Classic Amber HUD**: Faithfully reproduces the authentic Elite Dangerous cockpit instrument panel and holographic amber orange HUD (`#ff7100` / `#ffaa33`).
  - **🌐 Cyan Explorer HUD**: High-tech cyber cyan-blue theme tailored for deep space exploratory probes.
  - Theme changes apply immediately across all interface elements without reload and persist seamlessly across sessions.

### 🚀 v0.1.3 Update Summary
- **PML Sorting for Rhino Eligibility in Central Pane**:
  - Added "⛏️ PMLs / Rhino Eligible (Highest)" and "⛏️ PMLs / Rhino Eligible (Lowest)" to the Body Sort options.
  - Instantly sorts celestial bodies with Planetary Mining Locations (PMLs) to the top of the list, breaking ties by closest arrival distance.
- **Expansion Module Display Settings (Explicit Checkboxes to Hide or Restore)**:
  - Added "🧩 Module Display Settings" inside the UI Settings tab.
  - **🌿 Exobiology Module**: Toggle BIO badges across system cards, orbital trees, biological candidate prediction cards, and the Bio View on/off.
  - **🦏 Rhino Mining Module**: Toggle mining badges, surface coordinates map, mining history cards, and the Mining View on/off.
  - Allows commanders to easily declutter the interface to focus purely on astrophysics or restore memories whenever desired.
- **Clean Separation of Exploration Memories (UI Badges) and TTS (Voice Alerts)**:
  - Exploration milestones (bio predictions, badges, mining sites) remain visible on screen as journey keepsakes.
  - Voice alerts (TTS) and chimes can be independently turned on/off. High-value bio alerts (40M+ Cr) default to silent (disabled) until explicitly enabled.
- **Robust Settings Persistence**:
  - Module configurations are saved in localStorage and automatically synced to `Data/module_settings.json` on the server.

### 🚀 v0.1.2 Update Summary
- **Concise Rhino Mining History in Planet Notes (Coordinates & Mined Materials Only)**:
  - Designed for visual elegance and markdown note efficiency, avoiding verbose raw log dumps or timestamp clutter.
  - Automatically or manually logs **only "what was mined at which coordinates"** directly into celestial body notes (`body_bookmarks.note_markdown`).
  - Intelligently merges newly extracted minerals at the same site into the existing coordinate line (e.g., `- [Lat: +12.3456°, Lon: -45.6789°]: Germanium, Iron, Technetium`) without inflating line count, preserving all user notes.
  - Added "📝 メモに追記" buttons on mining site cards and "📝 全地点をメモに追記" in the mining section header for instant 1-click synchronization to the note editor (`#bm-note-input`).
  - Real-time SRV surface mining seamlessly complements latitude/longitude telemetry from `Status.json`.
- **Architectural Separation: Historical Exploration Archive vs. Live Co-Pilot**:
  - Introduced the `app/live/` package separating real-time telemetry (`telemetry.py`), dynamic landmark POI distances (`landmarks.py`), and Rhino surface tracking/note integration (`live/rhino/`).
  - Added interface foundations (`app/analyzer/llm/`) preparing for upcoming local LLM integrations (such as Bonsai Ternary 7B) for deep astrophysical scientific narratives.

### 🚀 v0.1.1 Update Summary
- **On-Demand EDSM Reference Loading for Unvisited Systems (with Security Lockout)**:
  - Added a "🚀 EDSMから星系データをロード（未訪問参照）" button in the External Footprint Check panel when a system is discovered on EDSM.
  - Allows pilots to retrieve and import stellar coordinates, system allegiance, and complete celestial body hierarchies directly into the local DB without needing flight journal logs, enabling immediate inspection in the System Map and Celestial Inspector.
  - **Strict Security Lockout**: Unvisited reference systems (`is_external = 1` or `visit_count = 0`) are completely barred from Web Share HTML generation (`btn-export-html`) and `.edsys` package export (`btn-export-pkg`) via both UI hiding and dual-layer backend HTTP 403 Forbidden enforcement. They are also excluded from personal expedition statistics (visited count and total payouts).
  - Explicit `🌐 外部参照 (未訪問)` badges are rendered on system cards and the detail header.
- **Header UI Streamlining**:
  - Consolidated redundant Explorer / Astrophysics concept buttons from the top header into the left pane tabs, freeing up horizontal space for system stats and CMDR coordinates.
- **Fixed Duplicate Reload Icon in Header Rescan Button**:
  - Removed duplicate `🔄` emoji rendering from the header Log Rescan button, restoring a clean single icon layout.
- **Semantic Versioning Convention**:
  - Adopted automatic patch level increments (`v0.0.x`) for standard updates (`v0.1.0` → `v0.1.1`).

### 🚀 v0.1.0 Major Update Summary
- **Low-Level Journal Reader Hardening & Zero-Corruption Guarantee**:
  - Rewrote the journal log reader engine to binary stream scanning (`rb` mode).
  - Automatically handles and rolls back truncated lines written by Elite Dangerous in real-time, preventing partial line parsing or file locking.
  - Automatically resets offset when log files are truncated or rotated, delivering ultra-lightweight and crash-resilient parsing.
- **UI Layout Overhaul & Bidirectional LIVE/Sort Controls**:
  - Re-aligned explorer/astrophysics concept tabs and the real-time LIVE button in the left pane header, eliminating text overflow and key label leakages.
  - Added an in-accordion LIVE guide banner and Unlock/Resume buttons in the Visit Period & Sort section.
  - Disabling LIVE instantly unlocks 1st, 2nd, and 3rd custom sorting (by potential value, astrophysics rarity, visit date, distances, etc.).
- **Context-Aware Body Sort Controls in Center Pane**:
  - Body sort dropdown is automatically hidden when viewing the hierarchical System Map tree to prevent confusion, and seamlessly displayed for Flat List, Bio, and Mining views.
- **Filter Chip Initial State Bug Fix**:
  - Fixed an issue where "⭐ 1st Disc", "🔖 Bookmarks", and "🤝 Shared" appeared selected even when inactive. They now default to neutral gray and glow brightly only when active.
- **Customizable Galactic Landmark Distance Badges**:
  - Added a dedicated checklist in Settings ("🖥️ Display & Font Size" tab) to independently toggle distance badges for CMDR current location, Sol, Colonia, Rainbow's End, and Explorer's Anchorage.
- **Restored EDSM Integration & High-Priority Body Completion**:
  - Full restoration of EDSM (Elite Dangerous Star Map) integration to automatically backfill known celestial bodies, orbital parameters, physical properties, and exploration values upon jump-in or Honk (`FSSDiscoveryScan`).
  - Implemented dual-queue architecture with **High-Priority Queue**, eliminating API request backlogs from historical journal scans and guaranteeing immediate, zero-wait queries for current systems, Honks, and UI selections.
  - Added "🔄 EDSM Sync" button in the system header for on-demand manual resynchronization.
  - Added "⭐ EDSM Known (Unscanned)" tag and discoverer CMDR credits in the Celestial Body Inspector.

### 🌐 Instant Bilingual Support (JP / EN Switch)
- Switch seamlessly between **English** and **Japanese** at any time with a single click on the **`[JP] / [EN]`** toggle in the top-right corner.

### 💾 100% Portable Design, `data` Directory Handling & Seamless Updates
- **Zero registry or system modifications**: Everything runs strictly in local user space without touching Windows registry or AppData.
- **Role of the `data` Folder**:
  - Running `ED_Journal_Analyzer.exe` automatically creates a local **`data`** folder in the same directory, containing your SQLite database (`elite_exploration.db`), parsed exploration history, celestial body bookmarks, custom aliases, and Markdown notes.
- **How to Update for Existing Users (Instant Migration by Replacing .exe Only)**:
  - When upgrading to a newer version, **do NOT delete the existing `data` folder**.
  - Simply replace the old `ED_Journal_Analyzer.exe` with the newly downloaded `.exe` and launch it.
  - All your accumulated travel logs, bookmarks, notes, and preferences **will be seamlessly preserved and instantly available**.
  - Automatic non-destructive schema migrations are applied on startup, requiring zero manual database handling.
- **Complete Reset / Uninstall**:
  - To completely remove the application, simply delete `ED_Journal_Analyzer.exe` and the `data` folder. No uninstaller or leftover files.

### Key Features

- **UI Font Size Direct Numeric Scaling & Safety Reset**:
  - New "🖥️ Display & Font Size" tab in Settings. Set standard base font size (**18px** default recommended, **14px** minimum guidance) with direct numeric input for custom values.
  - Fluid responsive wrapping allows badges and cards to fold vertically without truncation or loss of critical information.
  - Always-on-top Settings button and emergency <kbd>Ctrl + 0</kbd> shortcut instantly restores the default standard 18px size.
- **5 Key Galactic Landmark Distances & Custom Display**:
  - Instant distance calculations ($Ly$) to CMDR current location, Sol, Colonia, Rainbow's End (DW3), and Explorer's Anchorage (Sgr A*). Choose which badges to show in settings.
- **Mining Support: Gravity (G) & Temperature (K) Display & Mining View Integration**:
  - Surface gravity ($G$) is displayed directly alongside temperature and atmosphere in the mining body cards.
  - Dedicated checkboxes to toggle surface gravity ($G$) and surface temperature ($K$) across all views.
  - System card bottom landable bar automatically synchronizes to display only bodies matching active mining filter chips.
- **Optimized LIVE (Real-time) Button Relocation & Unlock**:
  - Easily toggle LIVE sync on/off from either the left header or the sort accordion to unlock manual custom sorting.
  - Easily dismisses Honk waiting screens to inspect current known star system data immediately.
- **Body Bookmarks, Custom Aliases & Markdown Notes**:
  - Bookmark individual celestial bodies, assign user-defined aliases (e.g. `Mining Base Alpha`), and keep rich Markdown notes with instant live preview.
  - Search across star systems, body names, custom aliases, and Markdown note contents simultaneously via the global search bar.
  - Filter chip for quick navigation to bookmarked systems (`🔖 Bookmarks`).
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

### 🌌 Deep Astrophysical Analysis & Stellar History Deduction via Generative AI (LLM Prompting)

You can feed the stellar system observation logs (system JSON / edsys data) parsed and managed by this application into modern Generative AI models (e.g. ChatGPT, Claude, Gemini, or local LLMs) using the prompt template below to deduce rigorous astrophysical critiques, stellar formation histories, and vivid atmospheric/orbital landscape descriptions:

#### 💡 Generative AI Prompt Template

```text
添付したJSONデータは、宇宙シミュレーションゲーム『Elite Dangerous』の星系観測ログです。

この星系に存在する天体配置、物理パラメータ（質量・半径・表面温度・大気圧・組成）、軌道要素（軌道長半径・離心率・公転周期）を天体物理学・惑星科学の観点から詳細に精査してください。

その上で、以下の内容について考察と解説をお願いします：

1. **物理的なリアリズムと矛盾点**:
   - 現代天文学・惑星形成理論から見て「あり得る点」と「物理的に不自然・矛盾している点（ゲーム的デフォルメやプロシージャル生成の癖）」の切り分け。
2. **星系の形成史シナリオ（成り立ちの仮説）**:
   - もしこの星系が実在すると仮定した場合、主星の進化（前駆星から現在に至るまで）、惑星系の誕生（原始惑星系円盤またはフォールバック・ディスク等）、軌道の進化（真円化や重力散乱）、そして現在の温度・大気が維持されているメカニズムについて、時系列に沿った詳細な科学的仮説シナリオ。
3. **天文学的・観測的な特異性と景観の描写**:
   - この星系特有のレアリティの解説、およびもし人類がこの惑星（特に地球型天体）の地表や軌道上に立った場合に観測されるであろう天球・空・環境の情景描写。

※お世辞や定型句は省き、学術的な査読論文の解説や専門的なフィールドノートのようなトーンで論理的に解説してください。
```

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
when update, you can remain data folder for stop re-read the journals.
---

## Credits & Acknowledgements

- **AI Assisted Development**: Developed with the assistance of AI (Google Antigravity / Gemini).
- **Game Data & Assets**: *Elite Dangerous* is a registered trademark of Frontier Developments plc.
- **Formulas & Science**: Payout calculations and Exobiology condition matrices are based on Frontier Developments specifications and ED community research (EDSM, Canonn Research, MattG).

---

## License

This project is licensed under the Apache License 2.0.
