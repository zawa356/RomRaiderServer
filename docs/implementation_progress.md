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
| 2 | 車載RRBridge spool・送受信 | 未着手 | [Issue #7](https://github.com/zawa356/RomRaiderServer/issues/7) |
| 3 | 実ECU全経路の停車試験 | 未着手 | [Issue #8](https://github.com/zawa356/RomRaiderServer/issues/8) |
| 4 | 本番MCP認証、生データ検索・anchor | 未着手 | [Issue #9](https://github.com/zawa356/RomRaiderServer/issues/9) |
| 5–6 | 安全Supervisor・数値監視・解析履歴 | 未着手 | [Issue #10](https://github.com/zawa356/RomRaiderServer/issues/10) |

## 変更履歴

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
