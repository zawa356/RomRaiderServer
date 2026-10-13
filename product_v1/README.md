# RomLogger 製品版 Server v1 — Phase 1（実装中）

このディレクトリは**現行PoCを壊さずに新製品の受信基盤を実装する**ための独立したパッケージ。旧`app/api.py`、`/ingest`、`/mcp`、合成Voice Demoには手を入れない。新テーブルは全て`v1_`プレフィックス。

## 現在実装した範囲

| 機能 | 状態 |
| --- | --- |
| PostgreSQL v1分離テーブル・制約 | 実装。CIのDB結合試験で検証 |
| DeviceごとBearer認証（トークンのSHA256のみDB保管） | 実装。OAuth/MCP認証とは別 |
| 不変profile_revision登録 | 実装 |
| `POST /api/agent/v1/telemetry/batches` | 実装：全件1トランザクション、commit後のみACK |
| 原本ID重複排除、同run+sequence衝突検出 | 実装 |
| 原本JSONB＋パラメーター値索引テーブル | 実装 |
| `POST /api/agent/v1/status` | 最小実装 |
| `GET /api/agent/v1/telemetry/recent` | **Phase 1の認証付き診断専用**。公開MCPではない |
| Agent端末・車両登録 | 最小CLI |
| MCP認証／柔軟な生データ検索 | **未実装**。Phase 4で実装 |
| Windows RRBridgeと実ECU結合 | **未実装・未検証**。Phase 2–3 |
| AI計測操作・Supervisor・走行中切替 | **未実装・未検証**。安全確認前に有効化しない |

設計書: [Agent API wire v1](../docs/interfaces/server_agent_wire_v1.md)と[OpenAPI](../docs/interfaces/agent_api_v1.openapi.json)。**Phase 1では7 APIのうち定義登録／バッチ受信／状態報告の3種類から実装している。** 結合テストのない機能を完成扱いしない。

## 1. 合成データのみでローカル起動

本実装は最初のCIとサーバー基盤の受け皿検証用。車載端末や実ECUには接続しない。

```bash
cp .env.example .env
# .env内のPostgreSQLパスワードとDATABASE_URLを一致させ、秘密トークンは推測不能な値に変更
docker compose -f compose.yaml -f compose.product-v1.yaml up -d --build db api-v1
curl -fsS http://127.0.0.1:18083/health
```

PoCの`api`、`mcp`、`proxy`はこのCompose起動で置き換わらない。`api-v1`のホスト公開は`127.0.0.1:18083`に限定。外部公開用のTLS／OAuthなどは今後追加し、**途中段階で車両データをインターネット公開しない**。

### DBの明示的マイグレーション

`compose.product-v1.yaml`には`product-v1-migrate`サービスがあり、DBがhealthyになったらAlembicで`0001_initial`へupgradeします。**この処理が完了するまで`api-v1`は起動しません**。APIや登録CLIがアクセス時にCREATE TABLEすることはありません。

```bash
docker compose -f compose.yaml -f compose.product-v1.yaml run --rm product-v1-migrate
docker compose -f compose.yaml -f compose.product-v1.yaml exec api-v1 python -m product_v1.migrate check
```

- 既存PoCと製品のDB表は名前空間を分離。`v1_alembic_version`のみ製品版のmigration履歴を表現します。
- 旧製品版試験コードが作った**未管理v1テーブルがすでに存在する場合、初期マイグレーションは安全側で失敗**します。現時点では自動stampしません。運用対象がある場合、データの保全と既存スキーマ検証を行う別手順を設計してから移行してください。
- `0001_initial`と`schema.sql`は初期ベースラインとして**編集禁止**。将来の変更は次の新規Alembic revisionで行います。
- 自動downgradeによる原本破棄を防ぐため、ダウングレードコマンドは提供していません。

変更履歴：[Product v1 CHANGELOG](CHANGELOG.md)／[実装進捗管理](../docs/implementation_progress.md)。

## 2. デバイス登録

```bash
docker compose -f compose.yaml -f compose.product-v1.yaml exec api-v1 \
  python -m product_v1.admin --display-name "Synthetic test vehicle"
```

結果に`vehicle_id`、`device_id`、`device_token`を**1回だけ**表示。tokenは平文でDBに保存しない。ログやIssue、チャット、公開GitHubに貼らず、外部の秘密管理に保管すること。

### 端末トークンの再発行・失効（Phase 1.1-B）

DB管理者だけがアクセスできるローカルCLIを使用します。**HTTP／MCPに資格情報操作は公開していません。**

```bash
# 端末の有効／失効状態を確認する
docker compose -f compose.yaml -f compose.product-v1.yaml exec api-v1 \
  python -m product_v1.credentials status --device-id DEVICE_UUID

# トークンを再発行（古いトークンはこの時点で無効）
docker compose -f compose.yaml -f compose.product-v1.yaml exec api-v1 \
  python -m product_v1.credentials rotate --device-id DEVICE_UUID

# 端末を恒久失効（2回目以降の実行も冪等）
docker compose -f compose.yaml -f compose.product-v1.yaml exec api-v1 \
  python -m product_v1.credentials revoke --device-id DEVICE_UUID
```

- `rotate`は新しいランダムトークンを**一度だけ標準出力に表示**。パイプ／端末ログ／CI／GitHub Issue等へ漏洩させない。DBにはSHA-256フィンガープリントだけ保存する
- `rotate`は**即時切替**。通信中のWindows Agentは旧トークンで401になるため、安全な端末再設定とスプール保持が必要。サーバー未ACKの観測は削除しない
- `revoke`では以降の全端末認証が401となる。同じIDの再有効化は初版では禁止。誤操作防止のため対象端末IDを確認する
- 削除／更新により過去の観測原本・ProfileRevision・Runの記録は消去されない
- このCLIはデバイス管理の最小機能。ユーザーによる包括承認・MCP認証などは別の機能

## 3. API呼出し順序

1. `PUT /api/agent/v1/profile-revisions/{profile_revision_id}` に、車両・端末ID、Logger fingerprint、項目定義を登録。
2. `POST /api/agent/v1/telemetry/batches` に、1 run単位の観測・イベント・gapレコードを送信。原本の`record_id`は再送でも変更しない。
3. Serverが全件commitした場合だけHTTP 200 `status=committed`、送信`batch_id`、`record_count`、`inserted_count`、`duplicate_count`を応答。
4. エラー・タイムアウト・commit成否不明ならAgentは未ACKをローカルに保持し、再送する設計。**旧PoCの2xxだけで送信済みにする処理を流用してはいけない**。
5. 診断用`GET /api/agent/v1/telemetry/recent?limit=100`は、その認証Deviceの割当Vehicleの最新観測を最大100件返す。

`Authorization: Bearer <device_token>`が必須。認証済みDeviceとリクエスト本文のvehicle/deviceが一致しない場合は拒否。合成値は`source_kind=synthetic`とし、実ECU由来として扱わない。

## 4. CI/CD

[GitHub Actions Product v1 contract CI](../.github/workflows/product-v1-ci.yml)は、PR・main／開発ブランチへのpushで以下を実行する。

- Python 3.12でproduct v1の構文確認
- Disposable PostgreSQL 16を立ち上げ、実DBへの原子的保存、再送、衝突、認証、synthetic識別のpytest
- Dockerイメージbuild、Compose overlayの設定妥当性検証

**CDは初期段階では本番自動デプロイをしない。** CIで失敗するコードを本番や車載へ自動配備しないため。実装成熟後に必要な承認・環境分離・資格情報の管理とともに追加する。

## 5. 未完了と次の実装

- Phase 1のさらに必要な範囲: 7 APIの残り（capability、commands、reconcile）はAgent工程で接続。HTTPエラー契約の詳細統一、MCP向けの行・列・anchor検索は別工程。マイグレーションを明示的なAlembic管理に変更。
- Agentの独立スプールと再送、実車・K-Line計測は今後の工程。実走行中のプロファイル変更は安全検証まで無効。
- Alembicによる初期版管理は実装済み。ただし**既に無管理で作られたv1テーブルの移行と、本番環境での可逆移行運用は未整備**。未管理のDBへ無条件stampしない。
