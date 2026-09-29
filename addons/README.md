# アドオン機構 (Addon System)

`ED_Journal_Analyzer` のコアモジュール（`app/parser`, `app/server`, `app/db`, `app/ui` 等）を直接改変せずに、機能を後付けで追加するための仕組みです。

## 設計方針

- **無効なアドオンはコストゼロ**: 起動時に読み込まれるのは各アドオンの `addon.json`（軽量なJSON）のみ。Pythonモジュール本体は、そのアドオンが**有効化されている場合に限り**インポートされます。未使用のアドオンがいくつ `addons/` に置かれていても起動速度・メモリに影響しません。
- **ファイル分離**: 1アドオン = 1フォルダ。コアの `app/` 配下のファイルは一切編集不要です。
- **落ちても本体は落ちない**: アドオンの読み込み・フック処理・マイグレーションはすべて例外を捕捉した上でログ出力されるだけで、アプリ全体をクラッシュさせません。

## ディレクトリ構成

```
addons/
  <addon_id>/
    addon.json        # マニフェスト(必須)
    addon.py          # register(ctx) を持つエントリポイント(必須)
    ui/
      panel.js         # 任意: フロントエンドに注入するESモジュール
```

## `addon.json` マニフェスト

```json
{
  "id": "sample_hello",
  "name": "Sample Hello Addon",
  "version": "0.1.0",
  "description": "説明文",
  "entry": "addon.py",
  "enabled_by_default": false,
  "ui_entry": "ui/panel.js"
}
```

| フィールド | 説明 |
|---|---|
| `id` | 一意なアドオンID。フォルダ名と揃えること推奨。 |
| `entry` | `register(ctx)` を定義したPythonファイル(フォルダ相対パス)。 |
| `enabled_by_default` | 初回起動時のデフォルト有効/無効。ユーザーの選択は `data/addons_settings.json` に保存され、以後はそちらが優先される。 |
| `ui_entry` | (任意) フロントエンドに動的挿入するESモジュールのパス(フォルダ相対)。`/addons/<id>/<ui_entry>` で配信される。 |

有効/無効はアプリ内の `GET /api/addons` / `POST /api/addons/{id}/toggle` から切り替え可能(切り替えは次回起動時に反映)。

## `addon.py` エントリポイント

```python
def register(ctx: AddonContext) -> None:
    ...
```

`ctx` は以下を提供します:

- `ctx.addon_id: str`
- `ctx.data_dir: Path` — このアドオン専用の永続化ディレクトリ(`data/addons/<id>/`)。設定ファイルやキャッシュはここに置く。
- `ctx.on(hook_name: str, callback)` — ホストイベントを購読する。現在発火するフックは `"journal_event"` のみで、`callback(event_name: str, event_data: dict)` が呼ばれる。ライブ監視中のイベントと、起動時の過去ログ一括再解析の両方で発火する(ライブ用WebSocket通知とは独立)。
- `ctx.add_api_router(router: fastapi.APIRouter, prefix: str | None = None)` — 既定では `router` は `/api/addons/<addon_id>/...` にマウントされる。コアから移設したアドオンが既存のURL(フロントエンドの`fetch`呼び出し先)を維持する必要がある場合は、`prefix="/api"` のように明示指定して元のパスを再現できる(`addons/edsm_sync/`, `addons/spansh_sync/` が実例)。
- `ctx.on_migrate(fn)` — `fn(conn: sqlite3.Connection)` を起動時に一度だけ実行。**追加専用**(`CREATE TABLE IF NOT EXISTS <addon固有のテーブル名>`)とし、コアの `systems` / `bodies` テーブルは改変しないこと。`system_address` / `body_id` で `LEFT JOIN` して参照する([`INTEROPERABILITY_DESIGN.md`](../INTEROPERABILITY_DESIGN.md) と同じパターン)。
- `ctx.on_startup(fn)` / `ctx.on_shutdown(fn)` — `fn()`(同期/非同期どちらも可)をホストのASGI起動・終了イベントで一度ずつ実行。バックグラウンドワーカーや常駐接続を持つサービス(例: TTS再生ワーカー)向け。起動側は `init_db()` とすべてのアドオンの `on_migrate` が完了した後に呼ばれる。
- `ctx.provide(name: str, fn)` — コア側が同期的に呼び出して戻り値を使う「計算スロット」を提供する(例: `"rarity_score"`, `"exobiology_predict_body"`)。`on()` が複数購読者への一方通行のfire-and-forgetなのに対し、`provide()` は**1つの名前につき1アドオンが値を返す**枠。コア側は `AddonManager.get_provider(name)` で参照し、`None`(未提供 = 無効化中)の場合は安全な空相当のデフォルトにフォールバックする — これにより該当アドオンを無効化すると、その計算だけがきれいに止まり、他のコア機能やUIはクラッシュしない。

## UIパネル (`ui_entry`)

指定した場合、フロントエンドの `addons.js` ローダーが有効なアドオンごとに `<div class="addon-panel">` を生成し、指定したESモジュールを動的 `import()` して `default(container, addonMeta)` を呼び出します。

```js
export default function init(container, addon) {
  container.innerHTML = `<strong>${addon.name}</strong> is running.`;
}
```

## サンプル / 実例

- `addons/sample_hello/` — フック購読・DBマイグレーション・APIルーター・UIパネルをすべて使う最小のサンプル(既定では無効)。機構の動作確認用。
- `addons/edsm_sync/`, `addons/spansh_sync/` — 旧 `app/server/api.py` に直書きされていた EDSM/Spansh の手動同期エンドポイントを実際に移設した例。`prefix="/api"` で元のURL(`/api/systems/{id}/edsm_sync` 等)をそのまま維持しているため、フロントエンド側の変更は不要。
- `addons/tts/` — TTS(VOICEVOX/Web Speech)の設定永続化・`/api/tts_settings`・`/api/tts/*` エンドポイント・再生ワーカーの起動終了ライフサイクルを移設した例。`ctx.on_startup`/`ctx.on_shutdown` の実例。`app/services/tts_service.py` のシングルトン本体と、`app/parser/journal_parser.py` からの直接呼び出し(GGG・高額生物アラート)はコア側に残置 — このアドオンを無効化すると設定API・再生ワーカーは止まるが、検出ロジック自体は変わらない。
- `addons/export_share/` — Standalone Web共有HTML・SNSサマリー画像・`.edsys` パッケージのエクスポート/インポート機能一式(`/api/export/*`, `/api/system/reveal-file`, `/api/import/*`)を移設した例。`app/services/export_service.py` 本体は引き続きコア側に残置(`GET /api/system/{id}/orrery` が同モジュールの `build_interactive_orrery` を使う核心UIビューのため)。このアドオンを無効化するとエクスポート/インポート機能のみ止まり、Orreryタブや星系一覧など閲覧系の機能には影響しない。
- `addons/rarity_scorer/`, `addons/exobiology_prediction/` — `provide()` の実例。コア計算ロジック(`app/parser/rarity_scorer.py` の天体物理レア度・GGG候補スコア、`app/parser/exobiology.py` の生体属/種予測)をファイル移動せずに `"rarity_score"` / `"exobiology_predict_body"` / `"exobiology_predict_system"` スロットへ登録するだけの薄いラッパー。`journal_parser.py`(ライブ監視・過去ログ一括再解析の両方)と `app/server/api.py` の星系詳細エンドポイント、`app/services/edsm/body_importer.py` の3箇所すべてが `AddonManager.get_provider(...)` 経由に統一されているため、無効化すると全箇所で一貫して機能が止まる。生体信号数(`bio_signals`)・確定GGG(Codexベース)判定・`anomaly_finder.py` の基本アノマリー・`scanned_organics` による確定生体表示は、どちらのアドオンとも独立したコア機能として無効化の影響を受けない。

## 既定は全アドオン無効 & 設定画面からのトグル

6つの移設済みアドオン(`edsm_sync`, `spansh_sync`, `tts`, `export_share`, `rarity_scorer`, `exobiology_prediction`)はすべて `enabled_by_default: false`。新規インストール直後はコア機能のみが動作し、ユーザーは アプリ内の **設定 > 🧩 アドオン** タブで個別にON/OFFを切り替える(`GET /api/addons` で一覧・`POST /api/addons/{id}/toggle` で切り替え)。切り替えは**次回起動時にのみ反映**されるため、タブ内に再起動を促すバナーが表示され、`POST /api/app/restart` でアプリ自身を再起動できる(WALをチェックポイントしてから同じ実行ファイル/スクリプトを再度起動し、自プロセスを終了する)。

開発時にすべてのアドオンを有効にしてテストしたい場合は、`data/addons_settings.json` に `{"<id>": true, ...}` を書くか、`pytest` 実行時は `tests/conftest.py` が自動的に(実プロジェクトの `data/` は汚さず)全アドオンを有効にした状態でテストする。

## リリースパッケージング

`addons/` はコンパイル済みexeに焼き込まず、**exeと同じフォルダに置く生ファイル**として配布する(addon.py をリビルドなしで編集できるという設計上の利点を保つため)。`tools/package_release.py` が `dist/ED_Journal_Analyzer.exe` + `addons/` を1つのリリースZIPにまとめる(PyInstallerでのexeビルド後に実行する):

```bash
pyinstaller ED_Journal_Analyzer.spec
python tools/package_release.py
```
