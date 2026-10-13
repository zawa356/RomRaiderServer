# RomLogger 開発チャット引継ぎ（2026-10-13）

> **目的:** 長大なChatGPTチャットの上限に達したため、次のチャットでコード実装・CI/CDを安全に再開できるよう、確認時点の全体状況、技術判断、未解決事項、再開手順を残す。
>
> **確認時点:** 2026-10-13 16時台 JST。本文のGit SHA・CIは作成時点のスナップショット。**次のチャットでは作業前に必ず最新の両repo main・PR・CIを再取得すること**。この文書が後続コミットを上書きする権限を持つわけではない。
>
> **設計・要求の正本:** [RLG-SRS v1.0](../system_requirements.md)、[設計索引](../README.md)、[Server–Agent v1通信契約](../interfaces/server_agent_wire_v1.md)。**実装進捗の正本:** [Server進捗](../implementation_progress.md)と[Agent進捗](https://github.com/zawa356/RomRaider_agent/blob/main/docs/product_v1_implementation_progress.md)。

## 0. 次のチャットが最初に読むべきこと

1. Server `zawa356/RomRaiderServer` の `docs/handoff/2026-10-13_chat_handoff.md`（この文書）、`docs/implementation_progress.md`、`docs/README.md`。
2. Agent `zawa356/RomRaider_agent` の `docs/handoff/2026-10-13_chat_handoff.md`（Agent側対応文書）、`docs/product_v1_implementation_progress.md`、`AGENTS.md`、`docs/08_decisions.md`、`docs/10_interfaces.md`。
3. GitHub APIで両repo `main` SHA、未マージPR、最新CIを確認。エージェントの自動E2Eワークフローは**緑色=実E2E成功ではない**（§5）。
4. **次の小Phase候補**は `2.1-D2b-2c`（旧PoCのbounded memory queue overflow根本対策と欠損低減）。並行して最新版Agentに対する実Server E2Eの本当の実行可否を確認・修正する。既存の優先順位がGitHubで更新されていたらそちらを優先する。
5. ユーザーは**コードの細部・各コミットの個別認可を求めない**。ChatGPTが安全側で実装方針を判断し、小Phaseに分けてコミット／CI／PR／mainマージを進める。ただし、ECU実操作・公開デプロイ・安全ガード緩和はCI成功だけで勝手に解禁しない。

## 1. ゴール・システム・境界

**目的:** スバルLegacy BP5（EJ20X、SSM/K-Line）からRomRaider LoggerとOpenPort 2.0互換機を通じて時系列計測し、Windows X270上のRRBridge Java Agent、Linux VPS Server/PostgreSQL、認証MCP経由で音声・チャットから検索・解析する。将来は運転中に無人で次の計測計画を評価・変更することも想定するが、独立したSupervisor・承認・安全ゲートを満たすまで操作系は無効。

**3層:** `RomRaider Logger + RRBridge (X270/Windows)` → `Agent製品版SQLite spool/送信Worker` → `HTTPS Server製品v1/FastAPI + PostgreSQL16` → `将来の認証MCP/AIクライアント`。

**リポジトリ:**
- [RomRaiderServer](https://github.com/zawa356/RomRaiderServer) — SRS/基本/詳細設計の**正本**、通信OpenAPI、製品版API/DB/CI、旧PoC Server。
- [RomRaider_agent](https://github.com/zawa356/RomRaider_agent) — 既存RRBridge Java PoC、SQLite spool、製品HTTP送信、TSV変換・増分取込、再送Worker、Windows/Linux CI。

**基本原則:** v1通信形式はJSON／UUID／ProfileRevision／Run／Segment／Observation+Event+Gap／原子的DB commit後のみACK。原本record IDは変更せず、ACK不明ならSQLiteに保持し冪等再送。PoCの旧TSV/Receiver形式と製品v1は**別契約**。走行中の画面操作はしない。ECUへの書込み、DTC消去、ROM読み書き、OpenPort FW更新、無承認の計測切替は実装・解禁しない。

## 2. GitHubの確認済み基準点（2026-10-13 16時台 JST）

| 項目 | 実際に確認した値 |
| --- | --- |
| Server `main` | `673e3f931b856943d3aaa8f4185a58663e01db68`（Agent公平配送CIの進捗同期） |
| Agent `main` | `f2fc8dc60d7af0d21e62deec72abb9e0cef9e477`（Agent PR #13：公平配送） |
| 未マージのPR | **両リポジトリとも0件**（確認時点） |
| Server最新履歴同期 | [Server PR #27](https://github.com/zawa356/RomRaiderServer/pull/27) マージ |
| Agent最新機能 | [Agent PR #13](https://github.com/zawa356/RomRaider_agent/pull/13) マージ |
| Agent Windows/Linux spool CI | [run #38361610506](https://github.com/zawa356/RomRaider_agent/actions/runs/38361610506) 両OS success。新FairDeliveryTestは両OS **19チェックPASS** |
| Agent旧TSV保全CI | [run #38355478212](https://github.com/zawa356/RomRaider_agent/actions/runs/38355478212) success |
| Server実Agent→実DB E2E（**固定版**） | [run #38350205850](https://github.com/zawa356/RomRaiderServer/actions/runs/38350205850) success。**Agent最新mainではなく**旧pin |
| Server製品版契約／PG CI | [run #38350205802](https://github.com/zawa356/RomRaiderServer/actions/runs/38350205802) success |
| Server最新docs-only main PoC CI | [run #38361737387](https://github.com/zawa356/RomRaiderServer/actions/runs/38361737387) success（文書コミットなので他のコードCIを当該SHAで走らせたという意味ではない） |

注意: この表は本引継ぎ作成前の基準点。**引継ぎ文書の追記コミット後はmain SHAが当然変わる**。また、2026-10-13の別チャット／別作業からAgentの実装が先へ進んだため、このチャットで当初予定していた`Phase 2.1-B`は**すでに実装済み**。昔のチャット文脈に従って重複実装してはいけない。

## 3. Phase完了状況（仕様/合成試験のゲートとして）

### Server（詳細はServer docs/implementation_progress.md）

- Phase 1.0: 製品版Server受信・原子的ACK・profile定義・認証・PostgreSQL合成試験 [PR #5](https://github.com/zawa356/RomRaiderServer/pull/5)。
- Phase 1.0-R: 旧PoCの同時起動DDL競合修正 [PR #11](https://github.com/zawa356/RomRaiderServer/pull/11)。
- Phase 1.1-A: Alembic versioned schema・明示migration [PR #12](https://github.com/zawa356/RomRaiderServer/pull/12)。
- Phase 1.1-B: デバイストークンrotate/revoke/status（DB管理者CLIのみ） [PR #13](https://github.com/zawa356/RomRaiderServer/pull/13)。
- Phase 1.1-C: ECU/Logger capability snapshots（定義済みと実測確認済みの区別） [PR #14](https://github.com/zawa356/RomRaiderServer/pull/14)。
- Phase 1.1-D: Agent pull claim/report/reconcile、操作記録・保守的lease管理。**配送はデフォルト無効**、有効化しても暫定allowlistは非作動系`suspend_ai_changes`のみ [PR #15](https://github.com/zawa356/RomRaiderServer/pull/15)。
- Phase 1.2-A/B: 障害注入・lost ACK・並列冪等再送、7 Agent APIのOpenAPI契約差分検出。製品版合成CI **48件PASS** [PR #16](https://github.com/zawa356/RomRaiderServer/pull/16)／[PR #17](https://github.com/zawa356/RomRaiderServer/pull/17)。
- Phase 2のServerテスト側: Agent JavaソースをGit blob SHA検証付きでテスト専用固定し、実FastAPI/PostgreSQL 16への合成E2E [PR #22](https://github.com/zawa356/RomRaiderServer/pull/22)、増分取込版の固定E2E更新 [PR #24](https://github.com/zawa356/RomRaiderServer/pull/24)。

### Agent（詳細はAgent docs/product_v1_implementation_progress.md）

- 2.1-A: Java8互換、SQLite WAL/FULL、原本ID・定義・ACK台帳 [Agent PR #3](https://github.com/zawa356/RomRaider_agent/pull/3)。
- 2.1-B: v1 HTTPS/JSON定義・バッチ送信、厳密ACK・再送判断、ローカル合成HTTP契約試験 [PR #4](https://github.com/zawa356/RomRaider_agent/pull/4)。
- 2.1-C1: 旧PoC M/S/E TSV → 新SQLite製品v1（非破壊） [PR #5](https://github.com/zawa356/RomRaider_agent/pull/5)。Windows Maven403のビルド環境障害を[PR #6](https://github.com/zawa356/RomRaider_agent/pull/6)で修復。
- 2.1-D1: TSV増分取込、SQLite永続offset、定義スナップショットとファイル改変/カーソル競合の安全側停止 [PR #8](https://github.com/zawa356/RomRaider_agent/pull/8)。
- 2.1-D2a: Agent増分取込版をServerの固定E2Eへ再pin [Agent PR #9](https://github.com/zawa356/RomRaider_agent/pull/9)、[Server PR #24](https://github.com/zawa356/RomRaiderServer/pull/24)。
- 2.1-D2b-1: SQLite永続retry/backoff、要調査停止、明示起動の独立`ProductBridgeWorker`、既読TSV消失検出 [Agent PR #11](https://github.com/zawa356/RomRaider_agent/pull/11)。
- 2.1-D2b-2a: 旧PoC`Stream.writerLoop()`書込エラー後のretry+fsync、`queue_overflow`欠損イベント、旧Receiver`.sent`だけを根拠にした元TSV自動削除を停止 [Agent PR #12](https://github.com/zawa356/RomRaider_agent/pull/12)。
- 2.1-D2b-2b: SQLite成功ACKベース**古いrun 3：最新run 1** の公平配送（失敗時はスロットを進めない、再起動後も保存） [Agent PR #13](https://github.com/zawa356/RomRaider_agent/pull/13)。
- **未完了**: 2.1-D2b-2c（旧PoC queue飽和の根本対策）、2.1-D3（X270/32bit/容量・物理電源断/実車耐久）、実車E2E、常駐Windows自動運用の安全な導入。

## 4. 現行技術・ファイル入口

**Server**
- `product_v1/api.py` FastAPI Agent v1（ProfileRevision、CapabilitySnapshot、TelemetryBatch、Status、Claim/Report/Reconcile）。
- `product_v1/store.py` PostgreSQL永続処理／UUID冪等／原子ACK。
- `product_v1/migrations/versions/0001_initial.py`～`0003_commands.py`。API起動中にDDLしない。
- `product_v1/credentials.py` DB管理者のみの端末Token rotate/revoke（秘密の生値をGitへ書かない）。
- `docs/interfaces/agent_api_v1.openapi.json` / `docs/interfaces/server_agent_wire_v1.md` 正式通信契約。
- `compose.product-v1.yaml` は製品APIを127.0.0.1:18083へloopback bindingした**opt-in**構成。本番CDなし。
- `.github/workflows/product-v1-ci.yml` 製品契約/PostgreSQL/Docker。
- `tests/e2e/agent_v1_snapshot/` 固定ソースの実Server E2Eとその更新手順。

**Agent**
- `src/main/java/net/neristal/rrbridge/product/v1/DurableSpool.java` SQLite出入庫、原本・ACK/カーソル/送信状態。
- `AgentWire.java`／`ProductSender.java` v1 JSON/HTTP/ACK; `IncrementalTsvBridge.java`／`LegacyTsvBridge.java` TSV変換。
- `ProductDeliveryCoordinator.java` backoff・レビュー停止; `ProductBridgeWorker.java`／`ProductLegacyScanner.java` 手動起動WorkerとTSV監視; `ProductBridgeOnce.java` 手動1サイクル。
- 旧`src/main/java/net/neristal/rrbridge/Stream.java` は**現行PoCのTSV queue・writer**。製品コードへ暗黙に置換しない。
- `scripts/test-product-v1-spool.sh`、`.github/workflows/product-v1-spool-ci.yml` Windows/Linux SQLite合成CI。
- `docs/product_v1_delivery_worker.md`／`docs/product_v1_incremental_import.md` 読むべきWorker・旧TSV故障リスク記録。
- `docs/10_interfaces.md` は**旧PoCのIF正本のみ**。新製品IFはServer側文書。

## 5. CIの非常に重要な「実行した／していない」の区別

1. **実行成功:** Agent最新`main`のWindows/Linux SQLite/JDK `--release 8`合成試験（run [38361610506](https://github.com/zawa356/RomRaider_agent/actions/runs/38361610506)）。`FairDeliveryTest` 19件も両OS成功。**Zulu 8 32bit/X270で実行したわけではない**。
2. **実行成功:** Serverリポジトリの**固定版Agent**（`668ad5230e7e3db4fc592311c857906f43802ad3`）を使い、実FastAPI→Postgres16への合成E2E（[PR #24](https://github.com/zawa356/RomRaiderServer/pull/24)、[main run #38350205850](https://github.com/zawa356/RomRaiderServer/actions/runs/38350205850)）。**現在のAgent main f2fc8dcではない**。
3. **緑でも本当のE2Eはスキップ:** Agent最新`main`の[run #38361610750](https://github.com/zawa356/RomRaider_agent/actions/runs/38361610750)はWorkflow「success」だが、`ROMLOGGER_SERVER_READ_TOKEN`がなく`Declare gated state`はsuccess、他方**別Private repo checkout／Java実行／Postgres E2Eの各stepはskipped**。この緑を「最新mainの実Server E2E合格」と言ってはいけない。
4. 旧PoCのJava writer安全回帰：Agent [CI #38355478212](https://github.com/zawa356/RomRaider_agent/actions/runs/38355478212)成功。旧writer以外や走行時の完全無欠損を意味しない。
5. GitHub Actionsは厳格な状態表示が必要：`success` + `実E2E step=success` と `success` + `実E2E step=skipped` を別ラベルにする。次Phaseでゲート可視化を改善する余地あり。
6. Private間の読み取り資格情報設定は、ユーザー承認／GitHub Secrets設定が必要。勝手に秘密を生成して公開したり、tokenをコミットしない。代替としてServer側pinしたテスト用Agentソースを最新SHAに更新する場合も、固定・ハッシュ照合・実E2Eを再実行する。

## 6. 未解決・禁止・危険箇所（優先順）

**P0：上流生データ喪失防止** — 旧PoC `Stream.java`の**200,000行bounded memory queue**が満杯になれば、依然原本行はその場で失われ得る。現在は`queue_overflow lost_lines=N`で可視化するが復元は不可。増分SQLite取込や3:1公平配送はこの上流欠損を回復しない。次のD2b-2cで安全側の負荷・容量・backpressure設計と故障注入試験を追加する。Logger callbackをブロックしない制約と、K-Lineの帯域を考慮。単に最大queueを増やすだけで無欠損と宣言しない。

**P0：最新Agentの実Server E2E** — 固定版実E2E成功は後続Worker、fairness、旧writer修正までの再保証ではない。Private E2Eはtoken欠如でskipped。現行`main`の実Java/HTTP/SQLite→実FastAPI/PostgreSQLの合成E2Eを実行できる手順を安全に確立する。

**P1：実車接続と電源断** — X270 Windows 10、RomRaider同梱Zulu8 **32bit**、SQLite native library、K-Line実ECU、OpenPort互換、通電・ディスク容量・物理電源断を停車状態で検証する。GitHub Windowsランナー(JDK17 --release 8)は代替にならない。車両状態に影響する操作なしから始める。

**P1：Worker運用・監視** — 現行Workerは明示`--once`／`--foreground`起動で、自動配備・サービス化は未採用。元TSV移動／短縮／改変／64ファイル上限で停止する。413分割、409/422不良原本隔離、Retry-After/jitter、容量逼迫時通知、元TSVの長期保持・手動整理を設計して試験する。未ACK原本自動削除は禁止。

**P2：MCPと安全Supervisor** — [Issue #9](https://github.com/zawa356/RomRaiderServer/issues/9) 本番OAuth認証MCPと生データ時系列・行/列・`anchor.record_id`前後一括取得、カーソル整合。[Issue #10](https://github.com/zawa356/RomRaiderServer/issues/10) 計画審査・期限付き承認・端末側安全判定・LLM非依存の数値監視。**実装済みServer claim APIが存在することは自律車載操作が許可済みの意味ではない**。

**禁止:** ECUのROM読み書き、DTC消去、学習値リセット、走行中の危険な無人操作、未承認profile切替、安全ガード緩和、秘密情報のGit公開、本番VPSへの自動deploy、Serverで成功ACKしていない原本の削除。

## 7. 次のチャットの作業方法（ユーザーとの合意）

- ユーザーは「コードに詳しくないのでChatGPTの判断で実装してよい」「細かな承認は不要」と指示済み。**GitHub Actions中心で、小さなPhaseを区切り、こまめにコミットし、履歴ファイルとコミットメッセージで処理内容を追跡**する。
- 速度より正確性、要件と設計は分ける。SRS v1.0は承認済みとして**無断で書換えない**。仕様の新規判断はADRと詳細設計に記録。
- 各PR: branch作成 → 差分調査 → 限定実装 → 合成故障試験 → Windows/Linux/Server適切なCI → 実行されたstepの確認 → 履歴・残課題・失敗修正の記録 → mainへマージ → main CI再検査。
- 複数チャットや別エージェントが同時にコミットする可能性がある。**作業直前とマージ直前にbase SHA、PR／main差分とCI対象SHAを再取得**。古い期待から変更を上書きしない。
- Project Library／チャット引継ぎもGitを優先して同期する。**GitHub上の変更履歴を唯一の実装結果の根拠**にし、「予定」と「CI成功」と「現車検証済み」を厳密に分ける。

## 8. 新しいチャットへ貼る一文

> RomLogger開発の続きです。まずServerの `docs/handoff/2026-10-13_chat_handoff.md` と両repoの実装進捗台帳を読んで、最新main SHA・PR・CIを再確認してください。既存設計/SRSは正本を優先します。Phase 2.1-D2b-2c（旧PoCのmemory queue overflow対策）と最新版Agent実Server E2EのNOT RUN解消から、安全側の小Phase・こまめなコミット・GitHub Actions・履歴記録を続けてください。実車操作／本番配備は勝手に解禁しないでください。
