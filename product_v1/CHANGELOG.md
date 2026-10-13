# Product v1 CHANGELOG

設計と実装の両方を追跡する。GitHub PRとCI結果、未着手の機能の正本は[実装進捗](../docs/implementation_progress.md)。

## [1.1-D] Phase 1.1-D（2026-10-13）

### Added
- `0003_commands`で計測タスク・計画版・承認範囲・操作台帳・レポート履歴・再照合履歴を追加
- Server–Agent v1のclaim／report／reconcile API。操作要求発行APIは**追加しない**
- 操作配送の期限、最新版照合、承認失効、配送lease、ID冪等、未知状態の保全
- SQLite/実車なしのPostgreSQL合成fixture＋GitHub Actions契約試験

### Safety
- `ROMLOGGER_ENABLE_COMMAND_CLAIM=true`を明示しない限り一切配信しない
- enabledでも`suspend_ai_changes`のみ（apply_measurement_plan等は無効）
- lease期限切れは実行済みかもしれないため`unknown`扱い。勝手に新IDへ再配送しない
- 実行成功とされる`verified`はAgentの状態報告だけから取得。サーバー側で推定しない

### Verification
- [PR #15](https://github.com/zawa356/RomRaiderServer/pull/15)／[Product CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38330361959)：**28件PASS**、Docker起動成功。 [PoC CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38330362074)：2ジョブPASS。実車試験・実装済みAgentへの適用は未実施\n- 追加修正：承認取消／計画新版でのlease再取得拒否、不明ローカル台帳時のclaim拒否、過去reported_atの拒否、API本文上限

## [1.1-C] Phase 1.1-C（2026-10-13）\n\n### Added\n- Alembic `0002_capabilities`：不変なLogger/ECU Capability Snapshotとparameter availability索引\n- 端末認証付き`PUT /api/agent/v1/capability-snapshots/{snapshot_id}`の登録・再送冪等・衝突拒否\n- 保存時の能力状態`defined/possibly_supported/verified_readable/unsupported/unknown`の区別\n- Synthetic PostgreSQL結合試験（実ECUからの能力検出は未実施）\n\n### Verification\n- [PR #14](https://github.com/zawa356/RomRaiderServer/pull/14)／[Product CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38329257391)：14件PASS、DB migration・Docker起動成功。[PoC CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38329257275)も成功\n\n## [1.1-B] Phase 1.1-B（2026-10-13）\n\n### Added\n- `python -m product_v1.credentials status/rotate/revoke --device-id ...` ローカル管理CLI\n- トークンの即時差替え、恒久失効と二重失効の冪等処理\n- 実DB＋FastAPIによる資格情報ライフサイクル試験\n\n### Security\n- ローテーション後の旧トークンをAPI認証に使用不可とする。生トークンはDB保存しない\n- 他Deviceのトークンや過去のTelemetry原本に影響しない\n- 本番MCPに資格情報管理操作は公開しない\n\n### Verification\n- [PR #13](https://github.com/zawa356/RomRaiderServer/pull/13)／[Product CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38328824590)：**11件PASS**、Dockerスモーク成功。[PoC CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38328824542)成功\n\n## [1.1-A] Phase 1.1-A（2026-10-13）

### Added
- Alembicの`0001_initial`として製品用PostgreSQL schemaを管理
- `python -m product_v1.migrate upgrade/current/history/check` CLI
- Docker Compose専用のmigrationサービス、migration完了後のAPI起動
- GitHub Actionsのmigration upgrade再実行・版照合テスト

### Changed
- API・端末登録CLI起動時のDB DDLを廃止。migrationを**明示的に実行**
- DB版が未導入／不一致の場合、API起動はfail-closed

### Safety
- 既存PoCのtableを変更しない。未管理のv1 tableが存在する場合は自動採用しない
- 原本削除の危険がある自動downgradeは禁止

### Verification
- [PR #12](https://github.com/zawa356/RomRaiderServer/pull/12)／[Product v1 CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38328488513)：9テスト合格、Migration 2回、Docker起動・CLI動作合格\n- [Legacy PoC CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38328488536)：supervisor／Compose・MCP全ジョブ成功

## [1.0.0-initial] Phase 1.0（2026-10-13）

- [PR #5](https://github.com/zawa356/RomRaiderServer/pull/5)：atomic ingest／replay／device認証／Docker及びPostgreSQL CI
- [PR #11](https://github.com/zawa356/RomRaiderServer/pull/11)：旧PoCのDB起動時競合とCI readiness修正
