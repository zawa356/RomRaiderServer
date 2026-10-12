# DD-OPS-001 配備・設定・運用・保守詳細設計

| 項目 | 内容 |
| --- | --- |
| 文書ID | RLG-DD-OPS |
| 版 | 1.0.0 / 2026-10-12 |
| 状態 | **設計書。現時点で構築・運用検証した手順ではない** |
| 上位 | [基本設計](basic_design.md)、[Server詳細](server_detailed_design.md)、[Agent詳細](agent_detailed_design.md)、[安全検証](safety_validation.md) |

## 1. 配備単位

| 単位 | 実行環境 | 必要な永続領域 | 変更頻度 |
| --- | --- | --- | --- |
| Agent RRBridge / Spool / Uploader | Windows＋RomRaider | spool、profile定義、認証資格情報、実行台帳 | RomRaiderやAgentの互換性に合わせて個別更新 |
| Client Supervisor | 同Windows | 起動モード・最終正常プロファイル・安全状態・操作台帳 | 安全検証を伴う個別更新 |
| Server API / MCP | Linux Docker | DB接続の設定・秘密情報は外部注入 | Server独立更新 |
| Server Monitor Worker | Linux Docker | MonitorRule評価結果／checkpointはPostgreSQLへ | Serverと同バージョンで更新 |
| PostgreSQL | Linux Dockerまたは独立DB | **原本・全イベント・状態・履歴** | インフラ運用側で保全・更新 |
| TLSリバースプロキシ | Linux環境 | TLS設定／証明書 | インフラ責務 |

**初版ではRedis／Kafka／専用時系列DBは必須にしない。** Serverの運用はDocker Composeを基準とするが、特定VPSや固定ホストへの依存を設けない。

## 2. コンテナ・ネットワーク設計

- Server APIとWorker、PostgreSQLは私設ネットワークで連携。PostgreSQLはインターネットへ直接公開しない。
- 外部へは必要なTLS終端のみ公開し、`/api/agent/v1/`と`/mcp`をルーティング。端末APIとMCPは独立認証。
- コンテナは非root、読取専用ファイルシステム等を可能な範囲で適用。DB資格情報はシークレット注入。
- Health endpointは生データや認証情報を返さない。未認証の外部公開は最低限のaliveのみ。readinessは内部または管理限定とし、DBの接続・マイグレーション済み状態を検証。
- 最低限のサービス状態: `api_alive`、`db_ready`、`schema_version`、`worker_heartbeat_age`、`mcp_auth_ready`。
- TLS証明書更新・DB物理バックアップはインフラ側で実施。本アプリは切断時もAgent spoolの保全が成立するよう設計。

## 3. 初回セットアップ手順の設計

1. `docker compose config`等で設定を静的検証し、必要なDB接続・公開URL・MCP認証Issuer等を確認。
2. DBを起動し、**マイグレーションを一回だけ**実施。失敗したらServer APIをreadyにしない。
3. Server API／Workerを起動。内部readinessでDBに実際に保存可能な状態を確認（既存原本の上書きはしない）。
4. 管理CLIからVehicle登録、Device登録、車両割当、個別の端末トークンを発行・安全に端末へ配布。
5. Windows側で起動方式（manual/ai）、Server URL、資格情報保存場所、spool保存先、容量警告を設定。公開READMEに秘密のサンプル値を載せない。
6. 合成データ転送テストでProfileRevision登録、Observation受信、ACK、再送時duplicateを確認。
7. 実ECU計測は**車載実機検証の別工程**で初めて実施。現在のPoC安全制限は適用要件が確かめられるまで維持。

管理者向けには`register-vehicle`、`register-device`、`rotate-token`、`revoke-device`、`approve-task`、`list-failed-batches`、`get-ingest-health`相当の操作をCLIで提供。コマンド名称は詳細実装で固定してよい。リモートMCPから資格情報発行・不特定コマンドを許可しない。

## 4. 設定のカテゴリ

| 区分 | 例 | 標準方針 |
| --- | --- | --- |
| Server API | listen、DB接続、外部URL、JSON上限、CORS／origin | 最小設定＋安全な既定値 |
| 認証 | device token発行、MCP issuer/audience/scope | 設定シークレット管理・失効可能 |
| 取り込み | Batch 128件／256KiB送信、Server最大本文512KiB初期目安、DB timeout | 構成間の上限不整合をチェック |
| 検索 | 初期1000行／最大5000行、タイムアウト・AST複雑度・cursor TTL | 巨大応答を回避しページング |
| Agent | Server URL、spool folder、通信 timeout、retry、disk警告 | 端末固有パスをハードコードしない |
| RRBridge | RomRaiderパス発見、定義fingerprint、フック状態 | BP5固定IDに依存しない |
| 安全・フォールバック | 実装確認済み条件、閾値、設定版、手動停止フラグ | 未検証なら保守的に拒否 |
| 監視 | スキャン間隔、ルール評価、stale閾値、重要度 | LLM依存なし、現車故障断定なし |

**値の位置付け:** Batch件数、検索行数、状態報告10秒、サーバー保存遅延P95 2秒などは、現在の要件が保証した数値ではなく実測で調整する初期設計値。

## 5. コンポーネント間バージョンの取り扱い

- Server API契約は`/api/agent/v1/`。Agentは送信する`protocol_version=1`と自身の版を状態報告。
- v1の互換なoptional追加はv1のまま。既存フィールドの意味変更、必須追加、列挙値の危険な読み替えなどの破壊的変更は**v2**へ。
- Server更新の際、**旧Agentが未ACKデータを持っている可能性を想定**。新Serverは旧版v1受信を一定期間維持するか、アップグレード手順で未ACK保全の安全な移行を先に確保。
- Agent更新ではspoolのスキーマを保全し、過去の未ACKと未完了コマンド台帳を改変・削除しない。ダウングレード時の読み取れない形式も事前警告。
- RomRaider内部の変更（Java privateメンバ等）がある場合はRRBridgeフック失敗を検知して計測機能を停止／抑止し、無理に自動操作しない。
- DB schema変更はexpand → 両版展開 → contractを基準とする。データの移行は検証済みの段階で実施し、原本を黙って書換えない。

## 6. 運用監視・障害対応

| 事象 | ユーザーへ見せる診断 | 初期対応 |
| --- | --- | --- |
| Agentが長時間未接続 | 最終報告時刻、最後の実サンプル時刻、未着の可能性 | 接続・端末稼働・資格情報を調査。ECU故障断定不可 |
| ECU接続はあるが観測が来ない | logger_stateとacquisition Hz、リンクエラー | ロガー／定義／OpenPortを調査 |
| Server DBが利用できない | API readiness false、取り込み失敗、Agent backlog | 未ACK保持、DB修復後に自動再送 |
| 409 ID衝突 | record ID、run、原因、隔離状況 | 原本を上書きしない。生成IDと重複実行原因を調査 |
| 422 不正レコード | 問題の項目、定義版、隔離件数 | 問題レコードを永続隔離、他の正常分を再送 |
| デバイストークン失効 | 認証エラー、device_id | 管理CLIで再発行。古いトークンをログに残さない |
| spool容量警告 | 未ACK件数・残容量・想定継続可能時間（不確かさ付き） | Server/回線を調査し、未ACK削除は禁止 |
| 安全条件不明 | 必要な情報・古さ・拒否理由 | プロファイル変更を止める。データ保全は継続 |
| 認証付きMCPが接続不能 | metadata、Issuer、TLS、トークンaudience | OAuth検証。匿名公開へ切り替えない |
| 監視イベントの滞留 | cursor age、最後の評価時刻 | worker再起動と冪等再計算 |

ログは構造化JSONを基準とし、`request_id,device_id,vehicle_id,run_id,batch_id,command_id,component,error_code,duration_ms`等を状況に応じて記録。**生トークン、HTTP Authorization、DBパスワード、不要な全サンプル原文は記録禁止。** 監査情報は原本と区別して保存。

## 7. デプロイ／更新時の確認

| ステップ | 必要な確認 |
| --- | --- |
| DB migration | バックアップ主体が復旧を準備したことを運用上確認（基盤側）、migration成否とschema_version |
| Server deploy | API alive、readiness、バッチ受信の契約テスト、MCP認証とreader検索 |
| Worker deploy | 二重worker時のイベント冪等性、checkpoint維持 |
| Agent deploy | spoolの未ACK数・再起動復元・Loggerフック・実行台帳 |
| IFの更新 | OpenAPI、Markdown、テストfixtureのバージョン整合 |
| 運用の試験 | 1回の通信断・再送・認証失効・DB停止復旧・失効コマンド拒否 |
| 公開 | ライセンス、依存ライブラリ、実バイナリ・資格情報・車両識別情報の不適切な同梱がないこと |

## 8. インフラ側との責務分界

DB物理バックアップ・レプリカ・ディスク冗長化・復元訓練は本プロジェクトの**対象外**。RomLogger側の責務は、原本を不用意に自動削除しないこと、マイグレーションの破壊的実行を防止すること、DB喪失時の状態を正確にAgentへ伝えて未ACKを保持させること、障害調査に必要な証跡を維持すること。インフラ側がDB永続性・バックアップを保証していることをアプリケーションが勝手に断定しない。

## 9. 公開・配布条件

- RomRaider本体とJava Agentの結合方式についてGPL等のライセンス上の扱いを公開前に確認し、第三者ライブラリ・実行バイナリの再配布権限を確認する。
- 特定のX270・BP5の設定サンプルは**検証専用**に置き、一般配布時の必須値にしない。
- 公開READMEには、サポート対象・未検証機能・利用者による安全上の判断・データ欠落限界・外部MCP本番認証の前提を明確にする。
- 初版リリースに向けてテレメトリー原本の保全とECU読取り限定を優先し、走行中切替は実証条件を満たすまで無効とする。
