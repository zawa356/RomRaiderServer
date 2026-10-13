# Product v1 CHANGELOG

設計と実装の両方を追跡する。GitHub PRとCI結果、未着手の機能の正本は[実装進捗](../docs/implementation_progress.md)。

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
