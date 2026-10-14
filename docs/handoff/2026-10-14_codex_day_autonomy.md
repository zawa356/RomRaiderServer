# RomLogger — Codex日中・自律継続開発指示書（2026-10-14）

> **ステータス：引継ぎ指示書／まだ今回のCodex実装は開始していない。**
>
> 利用者は**勤務中で、開発中の質問・操作・承認には原則応答できない**。Codexは既存の承認済み要件・設計・安全境界の内側で、技術的選択、合成PoC実装、修正、テスト、負荷・異常系、Git保存、PR/CI確認、正常なマージ、次の小Phaseへの移行を**自律的・積極的に**行う。小さな判断でユーザーの返答を待たない。一方、**応答がないことは危険操作への承認を意味しない**。危険または重大な互換性変更は、独立PoC・設計比較・試験の範囲で進め、適用の可否は「承認待ち」に残す。
>
> このファイルは**開始時点の方針／履歴スナップショット**であり、現在地は必ず最新の両repo main、open PR、CI、Agentのworklogから再取得する。旧 [2026-10-13夜間指示書](2026-10-13_codex_overnight.md) は履歴として参照し、この日中指示を新しい開発開始点とする。

## 0. 開始前に確認するもの（順序厳守）

1. Server repo `zawa356/RomRaiderServer` の本書、`docs/README.md`、`docs/system_requirements.md`、`docs/basic_design.md`、`docs/implementation_progress.md`、`docs/requirements_traceability.md`、`docs/test_acceptance_plan.md`、`docs/safety_validation.md`、`docs/interfaces/server_agent_wire_v1.md`。
2. Agent repo `zawa356/RomRaider_agent` の `AGENTS.md`、`docs/00_index.md`、`docs/product_v1_implementation_progress.md`、`docs/07_history.md`、`docs/08_decisions.md`、`docs/phase_4b_2d_2b_lock_watermark.md`、`docs/handoff/codex_overnight_report.md`、`docs/handoff/codex_overnight_worklog.md`、**新しい** `docs/handoff/codex_daytime_worklog.md`。
3. GitHubのAgentとServerの**両方**の最新 `origin/main` SHA、全open PR（既存Codex並行実装と競合していないか）、差分、Git author/email（個人noreply）、worktree未コミット差分、必要なCIの**ジョブ内ステップ**を確認する。
4. 作業ブランチを新mainから作り、**コードを書き始める前に** `codex_daytime_worklog.md`へ開始チェックポイント（両main SHA、branch、Phase、仮説、当面の実験、次のコマンド）を追記してcommit/push。**作業が打ち切られても最新のチェックポイントが必ずGitに残ることを最優先**。

## 1. 最終確認済み基準（2026-10-14 10:04 JST頃）

| 項目 | 基準 |
| --- | --- |
| Agent main | `0177587dfc4b7bff8852231ca19bbcd8283eeb0a`、[PR #29](https://github.com/zawa356/RomRaider_agent/pull/29) merged |
| Server main | `a2eb1c22c6f3a39c731abd30a725c69b10c2d3f6`、[PR #40](https://github.com/zawa356/RomRaiderServer/pull/40) merged |
| Agent・Serverのopen PR | ともに0（指示書作成前。**本書自体のマージでSHA更新**） |
| Agent CI | [main journal #38492814777](https://github.com/zawa356/RomRaider_agent/actions/runs/38492814777)、[main SQLite #38492817307](https://github.com/zawa356/RomRaider_agent/actions/runs/38492817307) 成功 |
| Server CI | [main #38492814828](https://github.com/zawa356/RomRaiderServer/actions/runs/38492814828) 成功 |
| 直近Codex報告 | [2026-10-14最終報告](https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/codex_overnight_report.md) |

**実装と検証を誇張しないこと。**

- Server v1 FastAPI／PostgreSQL原子的ACK、再送／認証／コマンド台帳等：各種合成CIと実Server合成E2E実績あり。ただし最新Agent自動追従のGitHub Actions上の実Server接続stepはprivate repo secret未設定で**SKIPPED**。
- Agent現行製品のSQLite spool、厳格HTTP ACK、旧TSV増分取込、明示 `--journal-once`、レビュー永続停止は実装済み。**製品用ライブジャーナル常時配線は未実装**。
- 4b-2d-2b-1 [Agent PR #27](https://github.com/zawa356/RomRaider_agent/pull/27)：別writerロックと旧writer競合を、Linux/Windowsで**別JVMの合成PoC**として検証済み。本番writerへの移行は未承認／未実施。Linux POSIXの**同一JVM内で別descriptorをcloseするとロックが解放され得る**反例を発見・修正済み。
- 4b-2d-2b-2 [Agent PR #28](https://github.com/zawa356/RomRaider_agent/pull/28)：RLC1 104-byte fsync watermark、別JVMでの確定prefix検証を**Linuxの独立PoC**として実証。Windowsでは `BasicFileAttributes.fileKey()` がnull、**watermark全56試験はBLOCKED/NOT RUN**。安全拒否・原本保持の回帰だけPASS。dir forceはWindows **UNCONFIRMED**。
- CodexのLinux（VPS/WSL）合成journal197＋製品SQLite344＝**541項目PASS**。Windows Actionsはjournal143＋SQLite344＝**487項目PASS**（watermark本体56は未実行）。旧legacy `test.sh` はJAR依存をテスト専用に導入して44件PASS。これらは**Zulu8 32bit/実ECU/物理電源断の合格ではない**。
- 4b-2d-2b-3：新writer→read committed prefix→製品SQLite／source rotationの**統合はBLOCKED／未実装**。原本識別・永続highwater・Windows等の前提を先に成立させる。

## 2. 開発目標とAIの自律性

今回の目的は「PoCを無限に増やすこと」ではなく、**Windowsでも破壊・誤ACKを防ぐ原本同一性／fsync確定の基盤を確立し、条件が満たされた範囲で製品v1へ段階的に繋ぐこと**。

**フェーズが一つ終わったら、CIと記録を確定したうえで次の小Phaseへ自発的に進む。** ユーザー確認待ちを口実に安全な作業を中断しない。複数小Phaseを連続して構わない。ただし以下の安全ゲートや利用上限時の文書保存が優先。

### Phase 4b-2d-2b-3a：Windows原本同一性の3案を独立比較

- 既存`DurableWatermarkPrototype`、`SplitLockJournalPrototype`、`LiveJournalReadProbe`、`JournalIdentityPrototype`、`ProductJournalScanner`を読み、current fileKey必須箇所と原本保全条件を特定。
- **案A hardlink anchor + Files.isSameFile**：元ジャーナルの同一内容コピー・別inode置換・移設・symlink/hardlink差異・NTFSのリンク権限・再起動・anchor欠落をOS別試験。管理者によるファイルセット複製を誤認しない。
- **案B Windowsネイティブ volume serial/file index**：Java8 **32bit** で利用可能なWindows API/小依存の候補調査、モジュール依存、FSごとの安定性、ファイルhandle権限/共有モード、取得不能時の停止を比較。ネイティブDLLや本番Windowsに導入せず、まずテスト専用PoC。
- **案C ジャーナル内UUID/headerの原本固有ID**：既存RLJ1互換、旧writer/readerの混在、コピーされた同一内容のUUID衝突、ヘッダーCRC改変・原本改変、署名ではないSHA/CRCの限界を整理。**元フォーマットを黙って変更しない**。
- 結論は「推奨案・代替案・否決理由・破壊的移行の有無・移行ゲート」をADRへ残す。どれも満たさなければBLOCKEDのままにし、要件を書き換えて緩和しない。
- 複数JVM／両起動順のold/new writer競合、reader、同一JVM別handle close、quota、部分書込、原本コピー/rename/unlinkの負試験を含める。Windowsは**GitHub Actions実runnerで必ず検証**。Linuxの成功だけで対応とみなさない。

### Phase 4b-2d-2b-3b：cross-platform watermark候補をテスト専用に実装

**3aで安全な案が成立した場合だけ**現行PoCを拡張。RLC1 104-byte形式の仕様変更・version増加はテストと移行互換を明記。

- writerの **journal fsync→watermark tmp sync→atomic rename→directory sync** を分解して、各段階の失敗注入、別JVM`Runtime.halt`、同一内容の別原本置換、旧/途中marker、stale marker、seq/offset退行、UUID衝突、CRC/hash偽造、容量超過を試験。
- 完全なCRCフレームを観測してもwatermarkが証明しなければ**製品SQLiteに入れない**。marker欠損/不整合/未確定dir同期の場合、状況に応じBLOCKED/UNKNOWN/fail closedを明示。
- 永続化保証は**プロセスkillやJVM haltだけで電源断の証明にならない**。Windows directory syncがUNCONFIRMEDなら無理にPASSへ変えない。32bit Zulu8実行試験が未実施ならNOT RUN。

### Phase 4b-2d-2b-3c：SQLite永続highwater・原子cursorの合成結合

**3a/3bのcross-OS厳密な安全条件が成立した場合だけ**、専用機能フラグ下の製品外合成reader/SQLite receiptを開発。

- source UUID、原本identity、source lane/claims、profile revision、record ID、last accepted watermark、既読prefix SHA、cursor CASと原文receiptの**同一DB transaction**整合を検証。
- 前commit/後commitの別JVM停止、二重worker競合、再起動、marker退行、原本改ざん、source複製、既存TSV laneとの競合を負試験。記録数は欠損/重複無し（**試験で投入した範囲のみ**）をSQL照合。
- 初期段階は **test-only/synthetic** に留め、旧`--journal-once`、稼働Logger、Server実IF、実車へ自動切替しない。製品インポータの既存データ形式や互換性を壊す場合、ADR＋承認待ちへ留める。

### Phase 4b-2d-2b-3d：原本ローテーション／seal（独立PoC）

**3cの原子性を確認してから**、原本＋identity＋watermark＋lock/manifestの不可分な取り扱い、旧原本維持・引継ぎ、容量上限8MiB・16本（**PoC上限**）、新UUID、run/session ID継続、source claim規約を検討。

- 未ACK原本自動削除やretention自動化は禁止。容量停止時は必ずfail closed・保全・監視可能状態。
- 旧session単一source契約を変更する必要があれば、単にコードを変えず**仕様変更の承認待ち**とし、その間も安全なテスト拡張を継続。

### 3a等がBLOCKEDの場合に進める代替作業

ユーザーへ確認を投げて停止する代わりに、**既存仕様を変えない独立タスク**へ移動可能：

- Windows/Linux共通の試験基盤拡充、idempotency/property test、故障注入、Windows16/32bitの互換性調査、安全な停止/検知/監視状態CLIの合成検証。
- Agent/Serverの現行schema/APIの契約試験・再送耐久性試験、read-only MCP/queryの製品**非公開・テスト専用**PoC（Phase4に入るならServer進捗へ別Phaseと明記）。
- 実装できない根本問題は、反例・エラーログ・要承認事項を残す。安全な別課題があれば、その課題の実装→CI→PRまで進める。**必ず新しい小Phaseを分ける**。

## 3. CloudPCの運用とGit権限

- **第一選択：ChatGPT CloudPC** の接続済みMCP（exec/run-script/fs-read/fs-write/fs-edit等）で開発、コンパイル、合成試験、隔離PostgreSQL試験。環境側にツールがない場合、Codex自身の隔離Linuxで作業し、**CloudPC未実施を明示**。そもそもツールが使用できるか確認し、SSH認証情報やホスト詳細をユーザーへ求めない。
- CloudPC GitHub CLIは`jr2twt`の認証済みで原則 `sudo -n -H -u jr2twt gh ...`。**ただし昨夜Codex記録には sudo不可のVPS/WSL環境もある**。無理にsudoを直さず、各環境に存在する権限と認証済みGit CLIを使用。ユーザーに会社メール混入の経験があるため、**Git authorは必ず個人noreply**、会社のアドレスを使わない。
- 既存クローンや他セッションのbranchを破壊しない。1Phaseごとの新規専用clone/worktree/branch。`git fetch`、`status`、open PR、remote main、`git config user.email`を確認し、競合する並行PRがあれば重複実装を避ける。
- `git reset --hard`、`push --force`、履歴書換え、他人の未コミット差分破棄は禁止。ログ原本・未ACK row・sidecar・tokenを消さない。
- テスト依存JAR・パッケージは**隔離作業領域のみ**導入してよい。秘密値をコマンド・コミット・ログ・報告に表示しない。新しいテスト用Postgresはループバック・一意DB/portに隔離し、**既存DB/サービスは停止も変更もしない**。
- **Caddy、MCP、SSH、systemd既存サービス、GitHub認証、public DNS/ポート公開、ファイアウォール、既存reverse proxy、本番デプロイは無断で変更しない。**
- ECU/ROM読書き、ECU reset/DTC操作、X270・OpenPort/現車、走行中プロファイル変更、安全ガード緩和、製品Worker本番自動接続、永続原本の自動削除は**追加承認が出るまで禁止**。勤務中で返答がない場合も禁止のまま。

## 4. 進捗を常にGitに残す：中断を前提とした実行手順

> **未保存のコードを書き貯めない。進捗ログもソースと同じくらい重要。**

1. Agent [`docs/handoff/codex_daytime_worklog.md`](https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/codex_daytime_worklog.md)に**セッション開始エントリ**を追記。commit/pushしてから実装開始。作業中も高頻度（設計仮説→RED負試験→実装→修正→合成PASS→CI→PR→merge→次Phase）で追記・commit/push。
2. 各commit messageは**何を・なぜ・PASS/FAIL/未検証のどれか**が分かる内容にする。例 `test(windows): reproduce copied-inode rejection (RED)`、`feat(proto): add Windows file-id fixture (synthetic)`、`docs(progress): mark watermarks Windows BLOCKED`。失敗テストは失敗のまま`RED`と明記し、成功のように記載しない。
3. Agentの`docs/07_history.md`、`docs/08_decisions.md`、`docs/product_v1_implementation_progress.md`と、Serverの**正本**`docs/implementation_progress.md`をPhaseの途中でも最新化。独立docs-only PRでServerの正本を同期する。二つのrepoで記載に矛盾があれば修正。
4. チェックポイントには「日時(JST/UTC)、Phase、base SHA、branch、変更ファイル、コミットSHA、PR URLと状態、検証環境/OS/JDK/コマンドと**試験件数**、具体的な失敗、CI run ID/各実ステップ、未承認ゲート、**次の一手のコマンド**」を記載。
5. 数十分の試験や長いCIの前、使用量制限が近い時は**先にworklogとWIPをcommit/push**する。未完成の試験やコードでも`wip(...): NOT VERIFIED`としてpush可能。ただし失敗中のPRはmergeしない。
6. `bash scripts/test-ingress-journal-prototype.sh`、`bash scripts/test-ingress-sqlite-receipts.sh`、`bash scripts/test-product-v1-spool.sh`、依存JARが揃う場合`bash test.sh`を該当改修の実試験として確認。Javaは`javac --release 8`、ただしこれは32bit Zulu8での実行合格を意味しない。
7. GitHub Actionsは**最新commitのrun**を確認。workflow成功でも本物のServer E2E stepが`skipped`なら、**実Server試験PASSとは報告しない**。Windowsのwatermark 56件を`BLOCKED/NOT RUN`のまま正確に表示。
8. PRは内容確認・main最新SHA/競合チェック→Windows/Linux CI（各実テストステップ成功）→通常merge→**main merge後CI成功**。Server進捗同期のdocs-only PRも同様。失敗・skipを隠さない。
9. セッション停止／利用制限直前：`codex_daytime_worklog.md`と`codex_daytime_report.md`へ「現在地、既存ブランチ、未merge PR、CI未完、次のコマンド、承認待ち」を残し**必ずpush**。次のチャットはmainとworklogの最終エントリを読み、作業treeのWIPを破棄せず再開。
10. 最終報告にはCloudPCへの接続の有無、既存サービスに触れていないことの確認結果、残存テストプロセス、自分が起動した一時資源の停止、open PR、両main SHAを付ける。**利用者への最終メッセージが失われてもGitを読めば実態が分かるようにする**。

## 5. 次のCodexチャットへ貼る短い命令

次の指示をCodexへそのまま渡すこと：

> `zawa356/RomRaiderServer` の `docs/handoff/2026-10-14_codex_day_autonomy.md` を全文読み、Agent側の同名の入口と `AGENTS.md`・最新進捗・ADR・worklog・両repo最新main/PR/CIを確認してください。**ユーザーは勤務中で操作・回答ができません。** 承認済み設計と安全境界の内側なら、CloudPCを積極利用してWindows原本同一性の独立PoC→cross-platform watermark→SQLite原子的highwater→ローテーションの順に、成立した範囲を小Phaseごとに自律実装してください。微細な選択・バグ修正・合成テスト・PR/CI/通常マージについて確認は不要。前提がBLOCKEDなら理由を記録して安全な別開発に移ってください。**毎Phase開始直後からAgentの`codex_daytime_worklog.md`、履歴・ADR・進捗とコードをこまめにcommit/pushし、途中で切れても次のセッションが再開できる次コマンドまで必ず残すこと。** CI内の実stepとSKIPPEDを分け、元データ・未ACK保全、Windows BLOCKED、実車未検証、CloudPC/本番サービス非変更を守ってください。危険・不可逆・実車・Caddy/MCP/本番変更や互換性破壊は承認待ちとして止め、別の安全なPhaseを進めてください。

## 6. 最低限の終了条件（昼間の実行時間が残っていても適用）

- 実装・PoC・設計の**合格証拠と未合格**が分離されている。
- Windows/Linuxで実際に走った試験とNOT RUNが、具体的な件数・OS/JDK・GitHub run・commitに紐づく。
- 原本を壊す操作、未ACK削除、既存writerロックの無条件緩和、未fsyncフレームの誤ACK、危険なECU/サーバー操作を行っていない。
- **Phase完了ならmain/CIとServer進捗まで統合**。途中ならWIP・open PR/失敗を残し、次セッションが続けられる。
- Codexがユーザーの承認を必要とする箇所は「ユーザーへの要判断事項」に分け、別の安全な作業を続ける。

**現場で使える全体製品へ進むことが目的。合成PoCのPASSと本番完成を混同しない。**
