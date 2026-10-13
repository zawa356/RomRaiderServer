# Phase 2.1-C2: Private Agent→actual Server E2E (pinned source)

このディレクトリは **Agentの実際のJavaソースを1コミットだけ固定したCI専用スナップショット**。製品の稼働コード、別実装、ライブラリ配布物ではない。

- Source repository: `zawa356/RomRaider_agent` (Private)
- Pinned **commit**: `6dd46835a200d961d517f5bb54f11eb2d7bdd2af` (Agent Phase 2.1-C1修正後)
- [固定した各ファイルのGit Blob SHA](SOURCE_BLOBS.sha1)。`scripts/prepare-agent-e2e.sh`が **git hash-object** で全ファイルを検査し、相違はビルド前に失敗する
- Java: `javac --release 8` でコンパイル（実X270／32-bit Java8実行の確認ではない）
- Database: GitHub Actionsの **disposable PostgreSQL 16 service**。本番DB・実車のtoken・ECUには接続しない
- Runner: Ubuntu GitHub Actions。車載Windows動作はAgent側CIの独立検証

## Why snapshot rather than read Private Agent repo at CI runtime?

現状両リポジトリがPrivateで、`GITHUB_TOKEN`は通常別Privateリポジトリを読めない。Agent側から実Serverをcheckoutするテストは、別途`ROMLOGGER_SERVER_READ_TOKEN`が設定されるまで **NOT RUN** になる。

本スナップショットをServer repoに保管することで、Server側のプルリクエストが Agent Java→実HTTP→FastAPI→PostgreSQLの結合契約を**シークレットなし**で検証できる。ただし、**Agentの最新版を自動取得するわけではない**。Phase 2.1-C2の成功はあくまで上記 pinned Agent commit の成功。

## Test scope

[Workflow](../../../.github/workflows/product-v1-java-agent-e2e.yml) は次を行う。

1. manifest上のAgent blob SHA一致を確認
2. Java8互換バイトコードにコンパイル
3. Server APIへ合成デバイスを登録し、使い捨てToken生成
4. 旧RRBridge形の合成TSV→Java `LegacyTsvBridge`→SQLite `DurableSpool`
5. Java `ProductSender` によるProfileRevision PUT／観測2件のPOST
6. **別SQLiteで同じTSVを再読込、同一record IDを再送**
7. 返却された完全ACKで両方のローカル送信台帳が確定し、DB直接参照で観測2件・Profile1件・synthetic出所を照合

### Updating the snapshot safely

Agent側で通信関連ファイルが更新されたら、Server CIが比較するJavaソースのスナップショットを**別PRで更新**する必要がある。

- Agent `main`の対象commitを確定し、`SOURCE_BLOBS.sha1`にcommitと各Git blob SHAを記載
- 対象ソースを原文のままコピーし、CIの`git hash-object`とAgent側リポジトリのblob hashが一致することを確認する
- 旧pinと新pinの差分レビュー、Java E2Eおよび既存Server/Postgres契約CIをPASSしてからmainへ統合
- **検証用のソースコピーを修正してAgent本体との違いを隠さない**。不一致修正はAgentを先に修正し、それから再pinする
- Agentの独立CIは引き続き必要。ソースが更新されたのにsnapshotが古いままなら「最新版とのE2E合格」と表記しない

## Excluded

- 実ECU・K-Line・X270／Zulu8 32bit、本番/インターネットHTTPS経路、リアル電源断／disk-full
- Logger callbackからの製品経路の自動常駐、legacy TSV削除条件、旧Queue dropを回避するための取り込み変更
- MCP/LLM、Profile自動切替、走行中判断、ECU書込み等

これらはE2E成功から推測しない。
