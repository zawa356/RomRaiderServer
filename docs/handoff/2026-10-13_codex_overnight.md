# RomLogger — Codex無人開発・再開指示書（2026-10-13 夜、正本）

> **目的**：ユーザーが就寝中で追加承認を出せない時間帯に、Codexが安全な合成開発を小Phaseごとに自律実施し、利用上限やコンテキスト切断を挟んでもGitの正本から正確に再開できるようにする。
>
> **本書は作業ルールと開始時点のスナップショット**。読み始める前に両リポジトリの現在の `origin/main`、open PR、CI、`docs/implementation_progress.md` / Agent進捗を再確認する。本書のSHAは将来の更新を上書きしない。
>
> **ユーザーの委任**：小規模な設計・実装・故障注入・テスト・Git commit/push/PR/正常CI確認後のmergeは自律的に実施してよい。ユーザーは夜間に返信できない。**新規承認が必要な危険作業を既定で許可されたと解釈しない**。その作業は保留して、安全な合成試験・設計検討に切り替えること。

## A. この文書が最新版かを確認する

- 設計・要件正本：本リポジトリ `docs/README.md`、`docs/system_requirements.md`（承認済みRLG-SRS v1）、`docs/basic_design.md`、`docs/interfaces/server_agent_wire_v1.md`。
- **実装進捗・履歴の正本**：Server [`docs/implementation_progress.md`](../implementation_progress.md)、Agent [`docs/product_v1_implementation_progress.md`](https://github.com/zawa356/RomRaider_agent/blob/main/docs/product_v1_implementation_progress.md)。
- Agentの判断記録：[`docs/08_decisions.md`](https://github.com/zawa356/RomRaider_agent/blob/main/docs/08_decisions.md)、[`docs/07_history.md`](https://github.com/zawa356/RomRaider_agent/blob/main/docs/07_history.md)、[`AGENTS.md`](https://github.com/zawa356/RomRaider_agent/blob/main/AGENTS.md)、[`docs/09_open_issues.md`](https://github.com/zawa356/RomRaider_agent/blob/main/docs/09_open_issues.md)。
- **旧引継ぎ**：両repoの`docs/handoff/2026-10-13_chat_handoff.md`は**16時台の過去スナップショット**。資料自体は保存済みだが**今夜の現在地の参照元にしない**。当該文書より本書と現行進捗／Git実体を優先する。
- Agentの旧PoC接続規約 `docs/10_interfaces.md` とServerの**製品v1正式IF**を混同しない。
- **本書は会話本文の逐語的アーカイブではない**。何が実装済みか、なぜ止めたか、何が実証済みかはGitとリンク先CIを唯一の証跡として扱う。

## B. 2026-10-13 22時頃JSTの引継ぎ時点

| 対象 | 確認済みmain・PR | 状況 |
| --- | --- | --- |
| Agent `zawa356/RomRaider_agent` | `022d9daf36c957d62a2ff91b7ce61c690ebac779`／[PR #25](https://github.com/zawa356/RomRaider_agent/pull/25) merged | Phase `2.1-D2b-2c-4b-2d-2a` 合成診断まで |
| Server `zawa356/RomRaiderServer` | `6d9db50aaa12e216e677c2a0bf9fc34216f2eb36`／[PR #37](https://github.com/zawa356/RomRaiderServer/pull/37) merged | 進捗正本同期済み。製品Server機能変更なし |
| 両リポジトリ | open PR **0件**（この指示書作成前） | 以後必ず現時点を再確認 |

**本書をcommit/mergeするとmain SHAは変わる。今夜のCodexは必ず新しいmainから分岐すること。**

直近に完了した工程：

- 4b-2c：[Agent PR #23](https://github.com/zawa356/RomRaider_agent/pull/23)。CloudPC隔離実FastAPI/PostgreSQL16へ現行AgentのTSV/journalを送信、実SQLで**合成6件/2 profile、重複0、ACK/replay PASS**。
- 4b-2d-1：[Agent PR #24](https://github.com/zawa356/RomRaider_agent/pull/24)。**明示的 `--journal-once`、`ROMLOGGER_JOURNAL_WORKER_ENABLE=1`、停止済みwriter限定**。Source/sidecar/cursorの保全、SQLite永続review停止、読取専用状態CLI。CloudPC合成**419項目PASS**、隔離実Server E2Eは**合成7件/3 profile、重複0、profile/batch ACKと別SQLiteからのreplay PASS**。**`--journal-foreground` は未実装**。
- 4b-2d-2a：[Agent PR #25](https://github.com/zawa356/RomRaider_agent/pull/25)。`LiveJournalReadProbe`で **FileChannel READのみ**のbounded診断、`JournalIdentityPrototype.readExisting`によるsidecarの厳格read-only化。CloudPC Linuxの合成**443項目PASS**。160回fsync付きappend＋最大320回probeを追加5反復。**Windowsのwriter排他FileLockはreaderのreadを拒否**：[初回Fail #38400570091](https://github.com/zawa356/RomRaider_agent/actions/runs/38400570091)。テストはBLOCKEDと明記しwriter close後の読取だけを確認。
- [Agent main journal CI #38401683741](https://github.com/zawa356/RomRaider_agent/actions/runs/38401683741) と[製品SQLite CI #38401683627](https://github.com/zawa356/RomRaider_agent/actions/runs/38401683627) はWindows/Linuxとも**試験ステップPASS**。Windowsでライブ読取が実現したわけではない。[Agent main E2E #38401683632](https://github.com/zawa356/RomRaider_agent/actions/runs/38401683632) はガードPASSだが、**実Server接続ステップはsecret未設定でSKIPPED**。
- [Server main CI #38402073017](https://github.com/zawa356/RomRaiderServer/actions/runs/38402073017) はSupervisor unit/compose smoke PASS。
- **直近4b-2d-2aでCloudPC実Postgres E2Eは再実行していない**。以前の7件PASSと混同しない。

現状の**大きな未解決**：旧PoCのvolatile queue飽和で既に落ちた計測値を復元できない／writerの`fsync`前データ欠損、**Windows FileLockのライブreader拒否**、明示的な**durable watermark（fsync確定位置）未実装**、原本ローテーション、容量/ディスクフル、電源断、Supervisor通知、Zulu8 32bit/実ECU未検証。

## C. CloudPC/GitHub：標準開発環境

**CloudPCが利用可能なら原則ここで編集・ビルド・負荷試験を行う。** ユーザーが用意した開発専用Linux VPSで、パッケージインストールやroot権限の使用は可能。ただし既存インフラを絶対に壊さない。

- MCP名：**ChatGPT CloudPC**。SSHベースのexec/run-script/fs-read/fs-edit/fs-write等（Codexのツール名は環境依存）。同じVPSへの接続がない場合は利用できたと偽らない。代わりにCodex自身の利用可能な隔離Linux環境で試験し、その差を記録する。
- GitHub CLIは`jr2twt`の認証済み。原則 `sudo -n -H -u jr2twt gh ...`、clone/edit/commit/pushも**jr2twt権限**。cloneは `/home/jr2twt/git/<phase-unique-name>` 等の**専用新規dir**へ。過去フェーズの作業ツリーを再利用して上書きしない。
- クローン例：`sudo -n -H -u jr2twt gh repo clone zawa356/RomRaider_agent /home/jr2twt/git/romlogger-codex-4b2d2b-agent -- --depth 1`。Serverも必要なら別ディレクトリへclone。
- **開始時の必須検査**：両repo `origin/main`のSHA、`git status --porcelain=v1 --branch`、`git branch`、`git config user.name/user.email`、open PR／進行中CI／差分・競合。作者は個人GitHubのnoreplyアドレス等、**会社用アドレスを混ぜない**。noreply設定は当該repoローカルに限定。
- Phaseごとに`feat/<phase-...>`、`fix/<...>`、`docs/<...>`の専用ブランチを新しいmainから切る。同時開発が見つかれば重複作業を避け、PRとmainの内容を先に調査する。
- **Git資格情報、SSH鍵、token、環境変数の値を表示・保存・commitしない。** `gh auth status`等は秘匿値に注意。Gitの履歴書き換え、`push --force`、`reset --hard`、rebaseや共有PRの破壊的操作は行わない。
- **Caddy、既存MCPサービス、SSH、GitHub認証、sudoers/iptables/ポート公開・systemdの既存サービスを変更しない**。接続が切れるため特にCaddyの設定/再起動をしない。開発用仮想環境はループバック/隔離portと名前で構築。
- CloudPCには過去の試験で専用PG16展開場所 `/home/jr2twt/git/romlogger-4b2c-pg16` がある場合がある。**停止中/使用中を確認し、既存DBの破壊・削除や既存portを奪わない**。実Postgres試験は新規`romlogger_*_e2e`の空DBを確保し、`ROMLOGGER_E2E_DISPOSABLE=1`を満たすスクリプト経由だけ。既存テストを実行しない場合、DB関連PASSを主張しない。

## D. 今夜取り組む技術Phase（安全な合成範囲で自律進行）

現在の第一優先は **Phase 2.1-D2b-2c-4b-2d-2b**。巨大な一括変更を避け、次の小分割で順序に沿って進む。各PRのコードが主にAgentならAgentに記録、設計正本の進捗はServerに同期する。

**2b-1：Windowsロック互換の非破壊PoCと反例の抽出**

1. 現行 `IngressJournalPrototype.java` の `RandomAccessFile("rw")` + `tryLock`、`LiveJournalReadProbe.java`、`JournalIdentityPrototype.java`、`ProductJournalScanner.java` の責務・コードとCIログを読む。
2. Windowsのmandatory FileLockでもread-only readerが成立する**ロック分離案**（別の`.writer.lock` / 同期fileの専有、journal本体は読取共有）を設計比較し、**合成一時ディレクトリのみ**で新prototypeとして検証。旧writerと新writerの**二重起動を防ぐ移行プロトコル**が証明できるまで、既存writer本体・既存起動設定は変更しない。
3. Windows/Linux GitHub Actions実試験で、異なるJVMの旧writer、新writer、readerの競合を網羅。Windowsでreaderが使えない場合はFAIL/BLOCKEDと記録し「実現済み」にしない。
4. 設計が大きく変わる/旧原本との互換性を失うなら**本番の既存実装へ配線せず、PoC＋設計判断案で止める**。ユーザー承認を翌日に待つ「要判断事項」として記録。

**2b-2：Durable watermarkの独立PoC**

1. 読めた完全フレームは**fsync完了とは違う**。writerが成功した`getFD().sync()`後の（UUID、sequence、byte offset、最後のframe hash等）をreaderに渡す、versionedかつCRC/整合性検査可能な **durable commit-watermark** の候補を設計する。
2. sidecar保存は`tmp-write→fd.sync→atomic rename→directory sync`等のOS差・失敗時挙動を検証し、**Windows/Java8でdir fsyncが使えない可能性**を明記する。片側だけ先行する事故、sidecarの古さ、原本の切り詰め/置換/改変、非原子的更新、クラッシュ中断、quota/ディスク満杯を合成負試験する。
3. watermark不在・破損・UUID不一致・offset矛盾・連番減少は**必ずfail closed**。観測上の完全frameがwatermarkを超えていても製品DBに入れない。
4. 旧原本の自動再発行/補修/削除やSQLite ACK自動消去を行わない。**データ消失ゼロの保証は物理電源断試験前に主張しない**。

**2b-3：合成結合・原本ローテーション境界**

- 2b-1と2b-2のPoCが各OSで確実に成立した場合だけ、独立したテスト用writer/reader/SQLiteの**合成経路**を組み立てる。旧`--journal-once`や製品v1プロトコルを無断で置換しない。ローテーションは原本+sidecar+watermarkの不変セット、ACK前の保全、16ファイル/8MiB上限を含めて設計する。
- PoC成功のみで`--journal-foreground`、実車、X270、Caddy、外部HTTP公開、本番Server/ECU操作へは接続しない。阻害要因が出たらそのPhaseをBLOCKEDとして終え、後続の安全なテスト補強/ドキュメント整備に進んでもよい。

**自主的に進めてよい代替タスク**：追加のCRC/連番/部分frameの故障注入、WindowsとLinuxのテストハーネス、断電を模擬した別JVM異常終了、read-only状態照会の回帰、progress/ADR追補、機械可読schemaやテスト手順の整備。実装可能な小範囲を進め、仕様判断が必要な核心部分は未承認として保留する。

## E. 夜間の承認・安全境界（最重要）

**夜間に自律実施可**：

- private repo内の試験用コード/文書の追加・軽微な整合性修正、合成データの生成、独立portでのローカルJava/Python/Postgresテスト、単体/結合/障害注入試験、CI設定のテスト追加、Phaseごとの専用ブランチ・PR・CI全合格後のmain merge。
- 不具合発見→差分修正→再試験→正確な結果記録。ユーザーへ都度判断を求めず実行する。

**事前承認がない限り実施禁止・明日以降へ保留**：

- 実ECU/車両、X270、OpenPort/J2534、ROM読書き/flash、DTC消去、ECU reset、測定項目の自動切替、走行時ロギング、安全ガード（20項目/2Hz等）の緩和、実環境への自動配備。
- Caddy/MCP/SSH/gh認証/既存systemd・既存リバースプロキシ/ファイアウォール、public domain/DNS/ポート公開、本番DBのmigrationや削除、認証体系・トークンの変更。
- 原本・未ACK SQLite row・journal/sidecar/watermarkの破棄・暗黙修復・自動retention。不可逆なGit操作、秘密情報の公開、PoC→本番への黙示的な仕様転換。
- SRS/承認済み正式通信IFの意味論・運用安全要件を変える重大な仕様変更。必ず代替案・影響・実験結果と「ユーザー承認待ち」を残す。

**失敗したら**：作業を隠して進めない。危険な続行を止め、再現用の合成fixture・単体試験・原本のコピーと観測ログを保存し、担当Phaseに **FAIL/BLOCKED/NOT RUN** を記録する。安全に進める別のPhaseへ移ってよい。

## F. Git履歴・CI・中断復帰の厳格運用

**最重要要請：Codexが利用上限に達してもGitだけで翌日再開できること。実装よりも履歴・実行事実の保全を優先。**

1. **セッション冒頭**：この文書→現行Server/Agent progress→両`origin/main`とopen PR・CI→最後の`docs/handoff/codex_overnight_worklog.md`（後述）を読む。前のCodexセッションが残した専用branch/PR/未commit変更があれば、破棄せず引き継ぐ。
2. **最初のコミット**：専用branch作成後、Agent側の`docs/handoff/codex_overnight_worklog.md`（本引継ぎで初期作成済み。なければ新規作成）へ新項目として「現在の両SHA・Phase・採用方針・次のコマンド・期待試験・禁止ゲート」を追記し**すぐcommit/push**。以後の作業開始地点をリモートへ残す。
3. **必須記録**：Phase、UTC/JST時刻、base SHA、branch、変更ファイル、何を・なぜ変えたか、合格・失敗した試験と**件数**、OS/JDK/DB version、テストした環境、PR URL、workflow run ID、重要ステップ実行有無、commit SHA、Blocker、次の再開コマンド。token・車両の実ログ原本を貼らない。
4. **頻繁なコミット**：設計/テストハーネス→小機能→故障テスト→修正→ADR/progress→CI証跡のように分割。試験が通らない段階も、適切な`test(...): reproduce ... (RED)`コミットで履歴化してよい。WIPは `wip(phase): ... NOT VERIFIED` と明記。**失敗をPASSとしてcommit messageや台帳に記さない**。
5. **最大限の中断耐性**：長いコンパイル/負荷試験/PR CI待ちの前には、`worklog`の現状・残タスクを追記してcommit/pushする。**文書更新を「終わりにまとめて」しない**。数十分をまたぐ段階や限界が近い時はその時点で中間コミット/remote push。
6. **テスト規則**：CloudPC Linuxで実際に`bash scripts/test-ingress-journal-prototype.sh`、`bash scripts/test-ingress-sqlite-receipts.sh`、`bash scripts/test-product-v1-spool.sh`等、変更関連の試験を実行。Javaは `javac --release 8`。WindowsのFileLock挙動は**Windows Actionsで実際に見る**。Linux PASSをWindows PASSと書かない。
7. **CI判定はジョブ内部の実ステップ**：`gh pr checks`や`gh run view <ID> --json jobs`等でjobとstepの`success/failure/skipped`を確認。特にAgentの`ROMLOGGER_SERVER_READ_TOKEN`未設定だと、**workflow自体はSUCCESSでもreal Agent→FastAPI→PostgreSQL部分はSKIPPED**。GitHubのE2E完了と絶対に言い換えない。
8. **PR/merge**：コード/文書、テスト、worklog、Agent progress/ADRを更新してcommit/push→PR作成→最新SHAのCI全成功と内容レビュー→main最新SHA再取得（競合があれば停止・再評価）→安全な通常merge→**mainマージ後CIも確認**。Serverの進捗正本を独立docs-only PRで同期し、Server CI確認→merge。自動マージ待ち・強制マージは禁止。
9. **不測の停止**：PRがopen・CIがpending/failedの状態は必ずworklogで明記。上限に触れた場合にマージを急がない。次のセッションでは`git fetch`・`git status`でWIPを調べ、最後のコミット、PR、Actionsから再開する。
10. **作業完了後**：Caddy/MCP/SSH健全性と未変更、CloudPC隔離試験の停止（**自身で起動したプロセスのみ**）、両repoに未コミット変更がないか確認。最新main SHAとopen PR、未解決をworklog/進捗に残し、翌朝のユーザー向け報告文を`docs/handoff/codex_overnight_report.md`に保存する。

**作業ログの書式（Agentに作成する。追記型、過去行は消さない）**：

```markdown
## 2026-10-13 HH:MM JST — Phase 4b-2d-2b-N / 状態 WORKING|PASS|FAIL|BLOCKED|NOT RUN
- Base: Agent <SHA> / Server <SHA>; branch: <名前>
- Done: <変更内容・理由・変更ファイル>
- Tests: Linux <コマンド・実行件数・PASS/FAIL>; Windows <CI ID・step状態またはNOT RUN>
- Git: <commit(s)>; PR: <URL/open/merged>; main SHA: <SHA or 未変更>
- Risks/unknown: <Windows FileLock/fsync等>
- Next exact step: <これから打つコマンド/修正ファイル>
- Safety: ECU/X270/Caddy/MCP/本番DBへの変更なし（実際に確認した場合のみ）
```

## G. 一時停止・再開時の単一チェックリスト

- [ ] 両private repoの最新main、open PR、worklog、docs progressを読んだ。
- [ ] 旧handoffの古いSHA/Phaseを現在地として扱っていない。
- [ ] CloudPCの専用cloneはjr2twt所有、Git authorは個人noreplyで会社メール不使用。
- [ ] 現Phaseの分岐／WIP／テスト／設計判断を小単位でcommit/pushした。
- [ ] 実行したテストのPASS/FAIL件数とGitHub CIの**step SKIPPED**を区別した。
- [ ] Windows live read BLOCKED、fsync watermark未実装、ECU実機未検証を解決済みと書いていない。
- [ ] Agentの履歴・進捗・ADRとServer進捗正本、夜間worklogを可能な限り同期。
- [ ] open PR／未merge／CI pendingと直後の再開手順がGitから分かる。
- [ ] 不可逆操作、原本削除、車両操作、Caddy/SSHの変更を行っていない。

## H. Codexへの最初の命令（ユーザーがコピーして開始できる要約）

「このリポジトリの `docs/handoff/2026-10-13_codex_overnight.md` を全文読み、Agent側の `docs/handoff/2026-10-13_codex_overnight.md` と `AGENTS.md`、進捗/ADR、両repo最新main・open PRを調べてください。承認待ちの危険な操作をせず、Phase 4b-2d-2bを小さく分割してCloudPCを主環境に実装・Linux/Windows合成テストしてください。**必ず作業開始時にworklogへ追記してcommit/pushし、途中も頻繁にprogress/ADR/worklogとコードをGitへ保存**してください。使用量制限で停止する前にも最後の状態と再開手順がGitHubに残るようにしてください。CIの実ステップ成功とSKIPPEDを厳密に区別し、各PhaseでPR/CI/merge後CIを確認してから次に進んでください。」
