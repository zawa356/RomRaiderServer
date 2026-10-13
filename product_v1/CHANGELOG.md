# Product v1 CHANGELOG

設計と実装の両方を追跡する。GitHub PRとCI結果、未着手の機能の正本は[実装進捗](../docs/implementation_progress.md)。

## [Unreleased] Phase 1.1-A（2026-10-13）

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
- この変更履歴の作成時点はCI未完了。合格後にCI実行URLを追記

## [1.0.0-initial] Phase 1.0（2026-10-13）

- [PR #5](https://github.com/zawa356/RomRaiderServer/pull/5)：atomic ingest／replay／device認証／Docker及びPostgreSQL CI
- [PR #11](https://github.com/zawa356/RomRaiderServer/pull/11)：旧PoCのDB起動時競合とCI readiness修正
