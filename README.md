# Elite Dangerous Journal Analyzer & Exploration Orrery

Elite Dangerousのフライトジャーナルログ（`Journal.*.log`）を解析・常時監視し、過去に訪れた星系・天体の状態、位置関係・軌道情報、レア天体・特殊周回、着陸可否・重力・火山活動、Exobiology（植物・菌類）の予測と報酬額、FSS/DSS探査価値の精密計算を提供するローカルデスクトップGUIアプリケーションです。

> **「あの時訪れたあの星は、どんな宙域だっただろう？」**  
> 銀河の長旅の記録や、過去の探索・初発見の思い出をいつでも鮮やかに振り返ることができます。

---

## 主な機能 (Features)

- **星系 & 天体の過去ログ遡り・タイムライン**:
  - 過去に訪れた際のスキャン状況、訪問回数、ジャンプ距離・消費燃料・搭乗船ログの復元。
- **位置関係 & 軌道階層ツリー**:
  - 恒星・惑星・衛星の階層親子ツリー構造、軌道長半径（AU / ls）、離心率、公転・自転周期、傾斜角、潮汐固定の可視化。
- **レア天体 & 特殊周回の自動検出 (Anomaly Detector)**:
  - ELW (地球型), WW (海洋惑星), Ammonia World, Terraformable, 高離心率 (e >= 0.8), 超短公転周期, 高速自転, 巨大リング等の自動タグ付け。
- **地表・着陸・重力 & 火山活動**:
  - 着陸可否 (Landable)、表面重力 (G値 & 着陸可能天体限定の高重力危険警告)、火山活動の種類・地質シグナル数。
- **Exobiology（植物・菌類）解析 & 報酬予測**:
  - 大気組成・表面温度・重力・天体種別から生息可能性のある植物/菌類候補（Stratum, Bacterium, Clypeus等）と通常報酬 + 初回採取5倍ボーナス額の算出。
  - サンプル採取に必要なコロニー間隔の表示。
- **探査価値精密計算**:
  - FSSスキャン価値、DSSマッピング価値（効率ボーナス含む）、初回発見ボーナス (x2.6)、初回マッピングボーナスの算出。
  - 星系ごとの「FSSスキャン合計」と「最大見込み（FD+FM）」の並列表示。
- **多言語対応 (Bilingual)**:
  - 日本語 / 英語のワンクリックリアルタイム切替。
- **リアルタイム監視**:
  - ゲームプレイ中のジャーナル差分を自動検知して即座に画面へ反映。

---

## 必要要件 & インストール (Requirements & Installation)

- **Python**: 3.10 以上

```powershell
# クローン
git clone https://github.com/SuzuneYonaki/ED_Journal_Analyzer.git
cd ED_Journal_Analyzer

# 依存パッケージのインストール
pip install -r requirements.txt
```

---

## 起動方法 (Usage)

```powershell
# デスクトップGUIウィンドウとして起動
python run.py

# ブラウザで起動する場合
python run.py --browser
```

起動後、右上の「**ログ再スキャン (Rescan Logs)**」をクリックすると、`Saved Games\Frontier Developments\Elite Dangerous\` フォルダ内の全ジャーナルファイルが一括インデックス化されます。

---

## Credits & Acknowledgements

- **AI Assisted Development**: Developed with the assistance of AI (Google Antigravity / Gemini).
- **Game Data & Assets**: *Elite Dangerous* is a registered trademark of Frontier Developments plc.
- **Formulas & Science**: Payout calculations and Exobiology condition matrices are based on Frontier Developments specifications and ED community research (EDSM, Canonn Research, MattG).

---

## License

This project is licensed under the Apache License 2.0.
