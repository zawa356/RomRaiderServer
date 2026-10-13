# RomLogger 実装進捗・変更履歴（正本）

このファイルは**GitのコミットとPRに結び付ける作業台帳**。要件や設計の正本は[設計文書一覧](README.md)とし、ここでは「どこまで実装したか、何を試験し、何が未実装か」を管理する。

## 運用規則

- 1 Phase = 独立したPRを基本とし、仕様・実装・テスト・ドキュメントを適切な粒度でコミット
- PRではGitHub Actionsの**PostgreSQL実DB試験、Docker起動試験、既存PoCの回帰試験**を確認してからmainへ統合
- 新しい機能を「完成」と記載するのは、該当するCIが成功した後。未実車・未導入は別区分
- コミットメッセージのprefixは `feat(db)` / `fix(db)` / `test(db)` / `ci(db)` / `docs(phase)` 等を使用
- 失敗した試験・修正内容・未対応の課題も記録。過去エントリを書き換えて隠さない
- 本番CD、実車接続・安全操作をCI成功だけで自動有効化しない

## 開発ロードマップとゲート

| Phase | 概要 | 状態 | GitHub |
| --- | --- | --- | --- |
| 1.0 | 製品版Server初期受信、原子的ACK、認証、合成データ試験 | **完了（CI確認済み／実車未確認）** | [PR #5](https://github.com/zawa356/RomRaiderServer/pull/5) |
| 1.0-R | PoC同時起動のDB初期化競合修正 | **完了（CI確認済み）** | [PR #11](https://github.com/zawa356/RomRaiderServer/pull/11) |
| 1.1-A | Alembic導入・DB版管理・移行を独立工程化 | **完了（CI合格、PR #12）** | [Issue #6](https://github.com/zawa356/RomRaiderServer/issues/6) |
| 1.1-B | デバイス資格情報の失効・更新と認証試験 | **完了（CI合格、PR #13）** | [PR #13](https://github.com/zawa356/RomRaiderServer/pull/13) |
| 1.1-C | Agent能力スナップショット登録と整合性試験 | **完了（CI合格、PR #14）** | [PR #14](https://github.com/zawa356/RomRaiderServer/pull/14) |
| 1.1-D | Agent操作のclaim／report／reconcileと保守的な期限管理 | **完了（PR #15・合成CI合格）** | [PR #15](https://github.com/zawa356/RomRaiderServer/pull/15) |
| 1.2-A | DB障害・ACK喪失・並列再送の耐障害契約試験 | **合成CI合格・PR #16** | [PR #16](https://github.com/zawa356/RomRaiderServer/pull/16) |\n| 1.2-B | Agent v1 OpenAPI契約の機械検証と受信境界テスト | **合成CI合格・PR #17** | [PR #17](https://github.com/zawa356/RomRaiderServer/pull/17) |\n| 2.1-A | Windows Agent製品版SQLite spool・ACK管理（Linux/Windows合成CI） | **完了（実ECU・HTTP未接続）** | [Agent PR #3](https://github.com/zawa356/RomRaider_agent/pull/3)／[Issue #7](https://github.com/zawa356/RomRaiderServer/issues/7) |\n| 2.1-B〜D | Server v1 HTTP送受信・RRBridge統合・実機耐久検証 | 未着手 | [Agent進捗](https://github.com/zawa356/RomRaider_agent/blob/main/docs/product_v1_implementation_progress.md) |
| 3 | 実ECU全経路の停車試験 | 未着手 | [Issue #8](https://github.com/zawa356/RomRaiderServer/issues/8) |
| 4 | 本番MCP認証、生データ検索・anchor | 未着手 | [Issue #9](https://github.com/zawa356/RomRaiderServer/issues/9) |
| 5–6 | 安全Supervisor・数値監視・解析履歴 | 未着手 | [Issue #10](https://github.com/zawa356/RomRaiderServer/issues/10) |

## 変更履歴

### 2026-10-13 — Phase 2.1-A：車載AgentのローカルSQLite spool（合成CI合格）

- Agent側[PR #3](https://github.com/zawa356/RomRaider_agent/pull/3)で、PoCのJava Agentから独立した製品SQLite outbox／WAL FULL同期／原本UUID・run+sequenceの衝突検知／ProfileRevision ACK待ち／バッチACK台帳を実装
- [Linux/Windows CI](https://github.com/zawa356/RomRaider_agent/actions/runs/38336548609)：**Ubuntu/Windowsそれぞれ42件PASS**、Java8対応コンパイルと実SQLite DBを確認
- Agent版の実装・修正正本：[Agent進捗台帳](https://github.com/zawa356/RomRaider_agent/blob/main/docs/product_v1_implementation_progress.md)
- **範囲外**：Server v1 HTTP転送、旧RRBridgeとの接続、X270 Zulu8 32-bit、ECU観測、物理電源断・disk-full、実車へのプロファイル操作。未ACK自動削除は実装していない
- ServerリポジトリのProduct API／DB／MCPコードは本記録では変更しない

### 2026-10-13 — Phase 1.2-B：Server–Agent v1通信契約の自動照合（合成CI合格）

- バージョン管理済みOpenAPIを正本に、FastAPIの実際のOpenAPIから**7 APIパス・HTTPメソッド・各リクエストの必須フィールドと項目名**を比較するCIを導入
- ネストされた観測／イベント／Gap／能力／状態品質の項目および操作状態の列挙値を照合。将来の意図しない契約破壊を検出
- 状態報告APIへ仕様上存在した`ecu_state`,`link_error_count`を追加。品質Hzの非負・非有限値排除、観測時刻TZ必須、Agent version空文字拒否
- プロトコルバージョン不一致はHTTP **426**とし、通常の形式不正422とは区別。エラー応答はコミット済みJSON Schemaで実レスポンスを検証
- [PR #17](https://github.com/zawa356/RomRaiderServer/pull/17)／[製品CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38334888281)：**48件PASS**（うちOpenAPI契約テスト14件）、Docker起動成功。[従来PoC CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38334888242)：Supervisor合格・Compose回帰確認。Agent、ECU、本番MCPへの接続試験は未実施

### 2026-10-13 — Phase 1.2-A：受信耐障害とACK不確定への対処（合成CI合格）

- PostgreSQLの実トリガーによるバッチ途中失敗を注入し、先に保存した観測／値／区間／取込通番も**同じトランザクションで巻き戻る**ことを確認するテストを追加
- commit完了後のHTTP応答喪失を模擬し、同一record ID再送がduplicateのみになり取込watermarkを二重更新しないことを検証
- 同一runへの4並列バッチ再送、同一record ID別内容の並列競合、古い端末状態報告が新状態を上書きしないことを検証
- PostgreSQL切断／commit成否不確定時に機密接続先を露出しない`503 STORAGE_UNAVAILABLE`（`retryable=true`）を返し、成功ACKを返さない
- 既存PoC・DB表／マイグレーション・車載機能は変更しない。テストfixtureは**synthetic限定**
- [PR #16](https://github.com/zawa356/RomRaiderServer/pull/16)／[製品CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38334387914)：**34件PASS**（うち耐障害試験6件）、Docker build/起動/CLI合格。[従来PoC CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38334387951)：2ジョブ合格。**本番障害注入や実ECU試験は未実施**

### 2026-10-13 — Phase 1.1-D：Agent操作配送・結果報告・状態照合（合成CI合格）

- Alembic `0003_commands`：タスク、計画版、承認範囲、操作要求、追記型report、再照合台帳を追加。既存生テレメトリーは変更しない
- 3 APIを実装：`POST /commands/claim`、`POST /commands/{command_id}/report`、`POST /reconcile`
- 配送は**初期無効**。有効化しても`suspend_ai_changes`のみの保守的な許可リストを採用。計画適用／ECU操作は引き続き実装・許可しない
- 承認済み有効期間・activeタスク・最新plan revision・端末割当・最新reconcile版が一致する場合だけlease候補。期限切れleaseは`unknown`に移し**自動再配達しない**
- report IDの同一内容再送は冪等、別内容衝突は409。報告状態を逆行させず、`verified`をServer受付のみで生成しない
- Reconcileはローカル状態を監査記録として保管し、不一致・不明な実行を自動解決しない
- 安全側の修正履歴：承認取消・計画更新後のlease再使用を禁止、不明ローカル実行履歴があるとclaimを拒否、古いreconcile時刻を409で拒否、通信本文サイズ制限を追加\n- [PR #15](https://github.com/zawa356/RomRaiderServer/pull/15)／[製品CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38330361959)：PostgreSQLの合成結合試験**28件PASS**、Docker起動／端末登録も成功。[旧PoC CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38330362074)：supervisor／composeの2ジョブ成功

### 2026-10-13 — Phase 1.1-C：ECU／Logger能力情報の同期（作業中）\n\n- Alembic `0002_capabilities`で不変Snapshotとパラメーター適合度の索引表を追加（過去原本を更新しない）\n- `PUT /api/agent/v1/capability-snapshots/{snapshot_id}`を端末認証付きで追加\n- 定義上の存在／ECU適合推定／実取得確認／非対応／不明を区別したまま保存（定義に存在するだけで実取得済みとは扱わない）\n- Idempotentな再送、同一ID別内容の409、重複パラメーター422、認証拒否を実DBで検証\n- [PR #14](https://github.com/zawa356/RomRaiderServer/pull/14)／[Product CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38329257391)で**14件PASS**、migration `0002_capabilities`、Dockerスモーク成功。[PoC CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38329257275)も成功。実ECU上での能力発見は**未検証**\n\n### 2026-10-13 — Phase 1.1-B：端末資格情報の管理（作業中）\n\n- 製品版Server専用のローカル管理CLIでトークン再発行・端末失効・状態照会を実装\n- 端末IDは不変、資格情報のフィンガープリントだけDB保存。再発行時に旧トークンは即時失効\n- 失効は冪等で再有効化は認めない。既存観測・定義・計測実行を削除しない\n- PostgreSQL結合試験で旧tokenの401、再発行tokenの200、失効後401、他端末への影響なしを検証\n- [PR #13](https://github.com/zawa356/RomRaiderServer/pull/13)／[Product CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38328824590)で**11件PASS**、Docker起動確認。[PoC CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38328824542)も成功\n\n### 2026-10-13 — Phase 1.1-A：Alembicとスキーマ管理

- `product_v1/migrations/`に製品版独立の**初期版0001_initial**を追加。既存PoC表を対象にしない
- 製品APIと管理CLIは起動時DDLを行わず、現在のスキーマ版を**読み取りのみで検証**
- Compose overlayに1回限りのmigrationサービスを追加し、成功してからAPI起動
- GitHub Actionsで実DBへのupgrade（2回実行による冪等確認）、version check、既存契約試験を実施
- 未管理の製品版テーブルがすでに存在するDBへは**安全のため自動stampしない**。運用移行には別の検証付き移行手順を要する
- 今回の初期MigrationはデータをDELETE/DROPしない。**downward migrationは自動実行不可**
- [PR #12](https://github.com/zawa356/RomRaiderServer/pull/12)。[Product CI実行結果](https://github.com/zawa356/RomRaiderServer/actions/runs/38328488513)：PostgreSQL試験**9件PASS**、migration 2回・version照合、Dockerビルド・起動・登録成功。[PoC CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38328488536)も成功

### 2026-10-13 — Phase 1.0：Server受信基盤

- [PR #5](https://github.com/zawa356/RomRaiderServer/pull/5)／`7a5b71f030c7fe021285a4836f5ff55dfa112ab8`
- 合成fixtureに対してPostgreSQL 16、原子的バッチACK、冪等なrecord ID、profile定義、端末認証と車両スコープの自動テスト8件が成功
- Composeで製品APIの起動・端末登録CLIを確認。実ECU、Agent spool、MCP、Supervisorは**未実装**

### 2026-10-13 — Phase 1.0-R：PoCのCI回帰

- [PR #11](https://github.com/zawa356/RomRaiderServer/pull/11)／`91bd4752297bb4a28a045b99c15984ef5101cc31`
- PoCコンテナ同時DDLの競合をadvisory lockで解消、read-only MCP tools/listの起動待ちを修正
- 既存PoCの試験を成功させたが、**実ECUに対する試験ではない**
