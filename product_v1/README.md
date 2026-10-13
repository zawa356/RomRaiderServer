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

## 2. デバイス登録

```bash
docker compose -f compose.yaml -f compose.product-v1.yaml exec api-v1 \
  python -m product_v1.admin --display-name "Synthetic test vehicle"
```

結果に`vehicle_id`、`device_id`、`device_token`を**1回だけ**表示。tokenは平文でDBに保存しない。ログやIssue、チャット、公開GitHubに貼らず、外部の秘密管理に保管すること。

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
- 現時点では`init_schema()`の冪等DDLを使用。**本番アップグレード手順の代替とはしない**。本番配備前にDBマイグレーション管理を追加する。
