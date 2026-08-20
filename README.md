# Elite Dangerous Journal Analyzer & Exploration Orrery

Elite Dangerousのフライトジャーナルを解析・可視化するデスクトップGUIアプリケーションです。

## 主な機能
- **星系 & 天体の過去ログ遡り**: 過去に訪れた星系の状態、スキャン状況、訪問履歴（ジャンプ距離・燃料・搭乗船）の復元。
- **位置関係 & 軌道階層ツリー**: 恒星・惑星・衛星の親子ツリー、軌道長半径、離心率、公転・自転周期、傾斜角、潮汐固定の可視化。
- **レア天体 & 特殊周回の自動検出**: ELW, Ammonia World, Terraformable, 高離心率 (e > 0.8), 超短公転周期, 高速自転, 巨大リング, 逆行軌道等。
- **地表・着陸・重力 & 火山活動**: 着陸可否 (Landable)、表面重力 (G値・高重力危険警告)、火山活動の種類・有無。
- **Exobiology（植物・菌類）解析 & 報酬予測**: 大気・天体条件から生息可能な属・種（Stratum, Bacterium, Clypeus等）と基本報酬・初回サンプリング5倍ボーナス額を算出。
- **探査価値精密計算**: FSS / DSS / 初回発見・マッピングボーナス計算。

## 起動方法
```powershell
python run.py
```
（ブラウザで起動したい場合は `python run.py --browser`）
