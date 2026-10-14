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
| 1.2-A | DB障害・ACK喪失・並列再送の耐障害契約試験 | **合成CI合格・PR #16** | [PR #16](https://github.com/zawa356/RomRaiderServer/pull/16) |
| 1.2-B | Agent v1 OpenAPI契約の機械検証と受信境界テスト | **合成CI合格・PR #17** | [PR #17](https://github.com/zawa356/RomRaiderServer/pull/17) |
| 2.1-A | Windows Agent製品版SQLite spool・ACK管理（Linux/Windows合成CI） | **完了（実ECU・HTTP未接続）** | [Agent PR #3](https://github.com/zawa356/RomRaider_agent/pull/3)／[Issue #7](https://github.com/zawa356/RomRaiderServer/issues/7) |
| 2.1-B | Agent側のServer v1 HTTPS/JSON送信・厳密ACK（契約モックCI） | **完了（本物のServer E2Eは未検証）** | [Agent PR #4](https://github.com/zawa356/RomRaider_agent/pull/4) |
| 2.1-C1 | 旧RRBridge TSV→製品SQLiteを読み取り専用に取り込む合成検証 | **完了（実車未接続）** | [Agent PR #5](https://github.com/zawa356/RomRaider_agent/pull/5) |
| 2.1-C2a | **pinした実Agent Java→実FastAPI→PostgreSQLの合成E2E** | **PASS（Agent commit 6dd46835固定／実ECU未確認）** | [E2E CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38346035656) |
| 2.1-C2b | Agent最新main自動同期・継続E2E／既存RRBridge常駐統合 | 未着手（Agent側のPrivate token付きE2EはNOT RUN） | [Agent進捗](https://github.com/zawa356/RomRaider_agent/blob/main/docs/product_v1_implementation_progress.md) |
| 2.1-D1 | 旧TSV増分取込・SQLite永続offset・保存直後クラッシュ復旧 | **完了（Windows/Linux合成CI）** | [Agent PR #8](https://github.com/zawa356/RomRaider_agent/pull/8) |
| 2.1-D2a | 最新増分Agentの実Server E2E再pin／未完結行・再起動・重複再送 | **実Server合成CI PASS・PR #24** | [Server PR #24](https://github.com/zawa356/RomRaiderServer/pull/24)／[Agent PR #9](https://github.com/zawa356/RomRaider_agent/pull/9) |
| 2.1-D2b-1 | 別Java Worker／SQLite永続再試行・要調査停止／既読TSV消失検出 | **Windows/Linux合成CI各208件PASS** | [Agent PR #11](https://github.com/zawa356/RomRaider_agent/pull/11) |
| 2.1-D2b-2a | 旧TSV writerの障害再試行・queue欠損可視化・旧ACKによる原本削除の禁止 | **完了（Linux/Windows合成CI各19件）** | [Agent PR #12](https://github.com/zawa356/RomRaider_agent/pull/12) |
| 2.1-D2b-2b | 最新／過去runの3:1公平配送（ACK永続台帳） | **Agent PR #13マージ済み・合成CI合格** | [Agent PR #13](https://github.com/zawa356/RomRaider_agent/pull/13) |
| 2.1-D2b-2c-1 | S行優先制限によりM/E行へqueue 4096枠を予約 | **Agent PR #15・合成CI合格** | [Agent PR #15](https://github.com/zawa356/RomRaider_agent/pull/15) |
| 2.1-D2b-2c-2 | 旧TSV writerの64KiB分割書込・IOException/RuntimeException後のrollback | **Agent PR #16・合成CI合格** | [Agent PR #16](https://github.com/zawa356/RomRaider_agent/pull/16) |
| 2.1-D2b-2c-3 | writer未fsync待機行・障害状態の観測、queue飽和後の回復試験 | **Agent PR #17マージ・44チェック合成CI合格** | [Agent PR #17](https://github.com/zawa356/RomRaider_agent/pull/17) |
| 2.1-D2b-2c-4a | 永続入口ジャーナル独立PoC（fsync/CRC/seq/quota/異常終了） | **Agent PR #18・Windows/Linux 34チェック合成CI PASS、製品接続なし** | [Agent PR #18](https://github.com/zawa356/RomRaider_agent/pull/18) |
| 2.1-D2b-2c-4b-1 | 独立volatile handoff、専用worker故障保持、stable replay ID | **Agent PR #19・Linux/Windows合成75チェックPASS、実SQLite未接続** | [Agent PR #19](https://github.com/zawa356/RomRaider_agent/pull/19) |
| 2.1-D2b-2c-4b-2a | journal UUID sidecar＋独立実SQLite receipt／cursor原子的commit | **Agent PR #20・Linux/Windows実SQLite回帰PASS、製品v1変換未接続** | [Agent PR #20](https://github.com/zawa356/RomRaider_agent/pull/20) |
| 2.1-D2b-2c-4b-2b | journal原本M/S/E→製品v1 SQLiteの共有変換、cursor CAS、TSV lane排他 | **Agent PR #22マージ、製品SQLite CI両OS合格・実Server E2E未実施（当時）** | [Agent PR #22](https://github.com/zawa356/RomRaider_agent/pull/22) |
| 2.1-D2b-2c-4b-2c | 最新AgentのTSV/journal→SQLite→FastAPI→実PostgreSQL16／重複ACKの隔離E2E | **CloudPC実Server E2E PASS、6合成観測/2プロフィール/重複0、GitHub実Server CIはSKIPPED** | [Agent PR #23](https://github.com/zawa356/RomRaider_agent/pull/23) |
| 2.1-D2b-2c-4b-2d-1 | 停止済みjournal用の明示offline Worker、永続review停止、読み取り専用状態CLI | **Agent PR #24マージ、CloudPC 419チェック＋実Server合成7件/3profiles E2E PASS、Windows/Linux CI PASS** | [Agent PR #24](https://github.com/zawa356/RomRaider_agent/pull/24) |
| 2.1-D2b-2c-4b-2d-2a | writer併行RLJ1 read-only診断とUUID sidecar read-only化 | **Agent PR #25マージ、CloudPC/Linux443項目PASS、Windows mandatory FileLockでライブread BLOCKED、両OS CI PASS** | [Agent PR #25](https://github.com/zawa356/RomRaider_agent/pull/25) |
| 2.1-D2b-2c | 旧PoC queue飽和・電源断前の欠損の根本対策 | **継続中：Linux read-only診断のみ、Windowsライブ読取は現行FileLockで不可。確定watermark／運用Workerへの接続／電源断時無欠損は未実装** | [Issue #7](https://github.com/zawa356/RomRaiderServer/issues/7) |
| 2.1-D2b-2c-4b-2d-2b-1 | Agent lock分離・新旧別JVM排他の独立PoC | **PR #27 merged / Windows・Linux CI PASS（運用非接続）** | [Agent PR #27](https://github.com/zawa356/RomRaider_agent/pull/27) |
| 2.1-D2b-2c-4b-2d-2b-2 | fsync watermark / 原本prefix検証PoC | **PR #28 merged / Linux成立、Windows BLOCKED（安全拒否CI PASS）** | [Agent PR #28](https://github.com/zawa356/RomRaider_agent/pull/28) |
| 2.1-D2b-2c-4b-2d-2b-3 | 新writer/reader/SQLite結合・rotation | **BLOCKED/未実装（両OS成立ゲート未達）、境界設計のみ** | [夜間報告](https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/codex_overnight_report.md) |
| 2.1-D3 | X270 Zulu8 32-bit／電源断／disk-full／実車耐久 | 未着手 | [Issue #7](https://github.com/zawa356/RomRaiderServer/issues/7) |
| 3 | 実ECU全経路の停車試験 | 未着手 | [Issue #8](https://github.com/zawa356/RomRaiderServer/issues/8) |
| 4 | 本番MCP認証、生データ検索・anchor | 未着手 | [Issue #9](https://github.com/zawa356/RomRaiderServer/issues/9) |
| 5–6 | 安全Supervisor・数値監視・解析履歴 | 未着手 | [Issue #10](https://github.com/zawa356/RomRaiderServer/issues/10) |

## 変更履歴

### 2026-10-13 — Agent Phase 2.1-D2b-2c-4b-2d-2a：read-onlyライブ診断とWindows FileLock阻害の確定

- [Agent PR #25](https://github.com/zawa356/RomRaider_agent/pull/25)をmain統合（merge SHA 022d9daf36c957d62a2ff91b7ce61c690ebac779）。Java8 FileChannel.READで原本のmagic/CRC/sequence/UTF-8、8MiB/128KiB上限、未完了tailと変更中原本を検査する診断プローブ追加。
- writer用JournalIdentityPrototype.openは空journalにsidecarを作成し得るため、reader用readExistingを分離。現在のProductJournalScanner/IncrementalTsvBridge.importJournalも既存IDのread-only検証だけ行う。sidecar欠落後のUUID誤発行を防ぐ。
- CloudPC Linuxで旧journal/handoff75＋新live probe24＋製品SQLite/receipt344＝**計443チェックPASS**。160回fsync writerと最大320回reader検査の併行負荷を5反復PASS。
- Windows runnerでは現行writerのmandatory FileLockがFileChannel.read自体を拒否。[初回Fail CI #38400570091](https://github.com/zawa356/RomRaider_agent/actions/runs/38400570091)で現象確認。新テストはWindowsのライブ読取を**BLOCKED**と明記し、writer終了後の全件readと安全な拒否のみPASS。**Windowsライブ読取が可能になったという意味ではない**。
- [Agent PR最終journal CI #38401415386](https://github.com/zawa356/RomRaider_agent/actions/runs/38401415386)、[製品v1 CI #38401415202](https://github.com/zawa356/RomRaider_agent/actions/runs/38401415202)でWindows/LinuxのJava8/実SQLite実ステップ成功。[E2E gate #38401415380](https://github.com/zawa356/RomRaider_agent/actions/runs/38401415380)は安全ゲート成功だが、実Server E2EステップSKIPPED。本PhaseでCloudPC実PostgreSQL E2Eは実行していない。
- **未実装**：fsyncが完了したフレームをreader側から確認するdurable watermark、Windows対応のwriter lock設計、rotation、常駐worker取込、Supervisor実通知、32bit/ディスクフル/物理電源断・実車。診断結果は製品SQLite cursorやServer ACKを進めない。Caddy/MCP/Server実装/本番環境への変更なし。[設計・試験](https://github.com/zawa356/RomRaider_agent/blob/main/docs/phase_2_1_d2b_2c_4b_2d_2a_live_readonly_probe.md)。



### 2026-10-13 — Agent Phase 2.1-D2b-2c-4b-2d-1：offline Journal Worker・持続review停止

- [Agent PR #24](https://github.com/zawa356/RomRaider_agent/pull/24) をmainへ統合（merge SHA b38bbad54b4160fa64b59dbf9aef191a78199b4c）。CloudPCのjr2twt専用cloneで実装、実SQLite/別JVM/実FastAPI→PostgreSQL16の結合検証を実施。
- 新しい --journal-once は ROMLOGGER_JOURNAL_WORKER_ENABLE=1 を要求し、**writerが閉じた専用journal**のみ一回取込。既存 --once/--foreground は旧TSVのままで、自動切替や --journal-foreground は提供しない（journal readerが排他的ロックを取るため）。
- ProductJournalScannerで原本と.identityのペア、同一source UUID重複、元パスの継続性、ディレクトリ境界、8MiB/16ファイル上限、TSV混在、writer競合を事前検査。取込失敗時は SQLite v1_ingress_review_state に初回の定型原因を保存してexit5。再起動後も同DBの旧TSV Workerを含め送信停止、自動解除APIなし。原本・未ACK・ACKを保持。
- ProductIngressStatusの読み取り専用CLI（exit 0/5/6/2）で外部監視が現在のレビュー停止状態を参照できるが、**Supervisor本体への通知は未実装**。NO_REVIEW_LATCHは走行安全の証明ではない。
- CloudPC Java8互換/実SQLiteの新規Scanner25、Worker23、Status12＝60項目追加、製品＋receipt計344＋journal/handoff75＝**419チェックPASS**。別JVMでCRC破損／初回レビュー原因永続化／送信停止・ACK保持も確認。
- CloudPC専用PostgreSQL16/実FastAPI：旧TSV3＋従来journal3＋新Worker別JVM1＝**合成7 records/3 profiles/record ID重複0**を実SQL検証。新Workerはprofile/batch ACK、fresh SQLiteから同じjournalの重複ACKもPASS。
- [Agent PR SQLite CI #38391785190](https://github.com/zawa356/RomRaider_agent/actions/runs/38391785190) はWindows/Linux実試験PASS。[gated E2E #38391785175](https://github.com/zawa356/RomRaider_agent/actions/runs/38391785175) はDB安全ゲートPASSだが、GitHub内の**実Server接続ステップはSKIPPED**（private Server認証secretなし）。CloudPCの実Server E2E成功と区別。
- **非対象**：運用Logger/ECU/X270への自動配線、同時writer read-only、常駐journal監視、物理電源断・Win32bit・disk-full、本番配備、Supervisor通知/復旧承認。Server実装/DB/APIとCaddy/MCPは変更なし。[Agent設計・証跡](https://github.com/zawa356/RomRaider_agent/blob/main/docs/phase_2_1_d2b_2c_4b_2d_1_offline_worker.md)。



### 2026-10-13 — Agent Phase 2.1-D2b-2c-4b-2c：最新Agent実FastAPI/PostgreSQL16隔離E2E

- [Agent PR #23](https://github.com/zawa356/RomRaider_agent/pull/23)をmainへ統合（merge SHA eafcc5f23204aaee5667420948361a8cfeb469a2）。CloudPC上の最新Agent/Serverの両private repository cloneと専用PostgreSQL16を用い、実験を実行。
- Ubuntu公式PostgreSQL16をjr2twt専用作業領域へdeb隔離展開して127.0.0.1:25432の使い捨てDBに接続。systemd PostgreSQL登録・既存5432・Caddy/MCP・本番環境は非変更。FastAPIは127.0.0.1:18083で試験中のみ起動。
- 最新Agentの既存TSV経路と新journal経路から製品SQLite→実FastAPI→PostgreSQL16のプロフィール／バッチ完全ACKと、fresh SQLiteからの重複再送まで実証。実DBに**合成観測TSV3＋journal3＝6件、プロフィール2件、record UUID重複0件**。Serverスキーマ現在版0003_commandsを確認。
- DB誤接続防止の明示opt-in、ループバック限定、DB名romlogger_*_e2e、URLクエリ禁止を追加。DB接続前の負試験6件PASS。旧SQLite/receipt回帰284件、journal/handoff75件（計359）PASS。
- [Agent PR CI #38387724747](https://github.com/zawa356/RomRaider_agent/actions/runs/38387724747) Ubuntu/Windows製品v1試験PASS。[Agent E2E gate #38387724771](https://github.com/zawa356/RomRaider_agent/actions/runs/38387724771)は安全ガードステップPASSだが、**本物のServer E2EはSKIPPED**。CloudPCの実Server PASSとは明確に区別する。
- 実行Worker/Loggerへのjournal自動接続、実車・X270、Windows32bit、電源断、ディスク逼迫は未実装・未検証。Serverアプリ/契約/DBコードを変更したわけではない。詳細：[Agent Phase4b-2c設計証跡](https://github.com/zawa356/RomRaider_agent/blob/main/docs/phase_2_1_d2b_2c_4b_2c_real_postgres_e2e.md)。



### 2026-10-13 — Agent Phase 2.1-D2b-2c-4b-2b：journalから製品v1への明示取込とレーン排他

- [Agent PR #22](https://github.com/zawa356/RomRaider_agent/pull/22)をmainへ統合（Agent SHA f3898a942b3b3b83e7ce77e8b28113a15d806439）。CloudPCのjr2twt隔離cloneで実装・Java8互換コンパイル・実SQLite検証・commit/pushを実施。
- IncrementalTsvBridge.importJournalでjournal M/S/EをCRC/seq/identity検査後、旧TSVと**同じ**profile/record UUIDで製品v1_profiles／v1_recordsに保存。journal専用のsource UUID・path・先頭SHA/累積SHA・定義snapshot付きCAS cursor。製品レコードcommit後にcheckpointする。
- SQLiteにv1_source_claimsを追加しdevice/vehicle/session単位でjournalと増分・旧一括TSVの二重受入れを拒否。旧runレコードのみ存在する移行状態、改ざん後CRC再計算、journalコピー移設、別JVMがrecord commit後/cursor前に異常終了した回復ケースも試験。
- CloudPC：製品v1＋SQLite receipt **284項目PASS**（新規journal→製品試験35件含む）＋journal/handoff **75項目PASS**、計359件。テストの1件追加に伴う旧期待値で初回1件FAIL後、修正し全試験PASS。[PR CI #38384554767](https://github.com/zawa356/RomRaider_agent/actions/runs/38384554767)でUbuntu/Windows製品SQLiteステップPASS。
- **E2E注意**：[real-server-e2e #38384554699](https://github.com/zawa356/RomRaider_agent/actions/runs/38384554699)はjob status successだが、**実Agent→FastAPI→PostgreSQLの試験ステップはskipped**。E2E実施済みと記載しない。
- 取込APIは明示呼び出しまで。Logger callback・実Worker経路・X270・実ECU・本番Server・Caddy/MCPへの配備・変更なし。無欠損、電源断、Windows32bit、ディスクフル、実Server ACKは未検証。詳細：[Agent設計・試験](https://github.com/zawa356/RomRaider_agent/blob/main/docs/phase_2_1_d2b_2c_4b_2b_journal_to_product.md)。



### 2026-10-13 — Agent Phase 2.1-D2b-2c-4b-2a：journal UUID・実SQLite受領原子カーソル

- [Agent PR #20](https://github.com/zawa356/RomRaider_agent/pull/20) をmainへ統合（merge SHA `28f3cb33da038a57442e3234a9c311046a51879d`）。CloudPC `jr2twt`専用作業ツリーでコード編集・Java8互換コンパイル・試験・commit・push・PRを実施。
- journalの固有source UUID/CRCを`.identity` sidecarへ保存。非空journalでID欠落・破損したとき再採番せずfail closed。実SQLiteの**PoC専用**`proto_ingress_rows`原文＋`proto_ingress_cursor`を同一DB transactionでcommit、原本SHA-256と連番を検証。
- CloudPCで新規実SQLite**22チェックPASS**、既存journal＋handoff **75チェックPASS**、製品v1の実SQLite回帰PASS。commit直前例外のrollback、commit後別JVMのRuntime.haltと再起動確認、原本書換え拒否を検証。[Agent PR CI #38381013007](https://github.com/zawa356/RomRaider_agent/actions/runs/38381013007) のLinux/Windows両ジョブで全試験ステップPASS。
- 初回試験はCRC破損fixtureが値を固定`0`にしたため失敗した。必ず異なる値へ変更する修正後、全試験PASS。履歴と[Agent詳細仕様](https://github.com/zawa356/RomRaider_agent/blob/main/docs/phase_2_1_d2b_2c_4b_2a_sqlite_receipts.md)に記録。
- **未解決**：journal+sidecarの原子的な同一性、物理電源断時のディレクトリfsync、Windows32bit、製品`v1_records`へのTSV変換・E2E、取得callbackでの欠損ゼロ保証。**Serverのコード／DB／API、Caddy/MCP、X270、ECU、本番配備に変更なし。** 今回のDB commitは製品Server ACKではない。



### 2026-10-13 — Agent D2b-2c-4b-1：非ブロッキング受渡し／リプレイIDの契約PoC

- [Agent PR #19](https://github.com/zawa356/RomRaider_agent/pull/19) マージ済み（Agent main `550f7da05f0624262713e2d9bb8c24642ec7456e`）。`IngressHandoffPrototype`をLogger/旧TSV/製品v1/Serverと**未接続の独立PoC**として追加。
- callback相当の`offer`は有限queueへの揮発性受理のみ。`drainOne`が専用workerでfsync成功して初めてjournal永続化。I/O失敗時のin-flight保持・運用者の明示復帰・quota終端を合成確認。
- stable journal source UUID＋sequenceを使う決定的record UUIDと分割replayを実装。ただしsource UUIDはファイル内へ永続化されておらず、downstream mockはMapのみ。**実製品SQLite outboxでの重複防止やE2Eは未検証**。
- CloudPC Java8互換で前Phase34件＋新規41件＝75チェックPASS。[Agent PR CI #38377766471](https://github.com/zawa356/RomRaider_agent/actions/runs/38377766471) はWindows/Linuxともに実試験PASS。詳細は[Agent 4b-1の設計と未達ゲート](https://github.com/zawa356/RomRaider_agent/blob/main/docs/phase_2_1_d2b_2c_4b_1_handoff_contract.md)。
- メモリ受理後・fsync前の異常終了での欠損、長期I/O停止・有限queueの飽和は未解決。実車・X270 32bit・物理電源断・実Server E2E・本番配備は未実施。本Serverの実装／DB／通信契約／Caddy/MCPへの変更なし。



### 2026-10-13 — Agent D2b-2c-4a：独立ジャーナルの障害復旧PoC（製品未接続）

- [Agent PR #18](https://github.com/zawa356/RomRaider_agent/pull/18) をmainへ統合（Agent merge SHA `115e5e7d0f9b9b69a08d957769b597ee96b56f7a`）。新しい`prototype.ingress.IngressJournalPrototype`は旧PoC `Stream.java`・製品SQLite outbox・Server側コードとは**未接続**。
- Java8互換でlength/sequence/CRC32付き原文フレーム、レコード単位fsync、OS file lock、quota fail closed、原本無断削除禁止を設計。別JVMがfsync直後に`Runtime.halt(73)`で終了しても再起動後に受領行を再読込できた。
- CloudPCの隔離cloneで34チェックPASS、[Agent PR CI #38374125596](https://github.com/zawa356/RomRaider_agent/actions/runs/38374125596) Ubuntu/Windows両方の実試験ステップPASS。詳細は[Agent設計・検証文書](https://github.com/zawa356/RomRaider_agent/blob/main/docs/phase_2_1_d2b_2c_4a_ingress_journal_prototype.md)。
- **未解決**：fsyncはECU callbackへ直接呼べないため、実際のqueueからの受け渡し・容量上限時の運用停止・既存SQLite outboxとのACK/原本管理・異常終了後のカーソル設計が未実装。物理電源断、X270/Zulu8 32bit、disk-full、実車及び最新Agent→実Server E2Eは未検証。**原本無欠損／製品版対応済みと判断しない**。
- このServerリポジトリへの反映は進捗台帳の同期のみ。Caddy/MCP・Serverコード・DB・本番デプロイに変更はない。



### 2026-10-13 — Agent Phase 2.1-D2b-2c-3：書込障害・volatile backlog可視化と飽和復旧試験

- [Agent PR #17](https://github.com/zawa356/RomRaider_agent/pull/17)／Agent main `95e44e7cc0204c63577d7add609a0f7095d7c67e` へ統合。旧PoC`Stream.java`に`writerPendingLines`・`memoryBufferedLines`・`spoolWriteFailures`・`writerDegraded`・writer最終fsync/障害時刻を追加。PoCの接続規約`docs/10_interfaces.md`C4.1を更新。
- CloudPC上のJava8互換スタブ44項目PASS。writerの疑似I/O不能時に約19.6万サンプルをqueueへ投入、追加10サンプルdropとM/Eメタデータ保持、復旧後の**受け付け済み全195904行の一度限りの保存**・欠損イベント1件の書込を確認。試験は本物のホスト全体をdisk-fullにしていない。
- [Agent PR CI #38372232369](https://github.com/zawa356/RomRaider_agent/actions/runs/38372232369) Ubuntu/Windowsの実試験ジョブが成功。失敗した初回ローカル試験は既存fsync時刻をnullと誤認したテスト期待値の問題で、修正・再実行済み。
- **意味の制限**：監視カウンターは揮発性。writerが無期限停止し、callbackをブロックせず有限queueしか使えなければ無欠損保証は不可能。JVMクラッシュ前の未fsync行は引き続き失われ得る。最新製品Agentによる実PostgreSQL E2E、X270/実ECU、電源断・長期disk-full試験、本番配備は未実施。
- Server製品コード・DB・IFは変更なし。旧PoCメタデータの追加は製品v1 API契約への変更ではない。



### 2026-10-13 — Phase 2.1-D2b-2c-1/2：旧PoC queue保護とwriter負荷・障害試験（Agent main同期）

- [Agent PR #15](https://github.com/zawa356/RomRaider_agent/pull/15)で容量200,000行のqueueにS行のソフト上限195,904行を導入し、M/Eを保持する余地4,096行を確保（メタデータ完全保護ではない）。[main CI #38367748133](https://github.com/zawa356/RomRaider_agent/actions/runs/38367748133) Windows/Linux PASS。
- [Agent PR #16](https://github.com/zawa356/RomRaider_agent/pull/16)で、旧`Stream.java`の行単位TSV書込を64KiB固定チャンクでまとめた。IOException・RuntimeExceptionによる部分書込時はファイル元長への復旧を試み、fsync成功までwriter待機中の原文を保持。2,400行と大行／日本語行／障害注入を含む31チェックがCloudPC上でPASSし、[PR CI #38369893799](https://github.com/zawa356/RomRaider_agent/actions/runs/38369893799) Windows/Linux両方PASS。
- Agent `main`はPR #16マージcommit `72dce98a677e4a2702f56e79f092246b40670ec7`。このServerの更新は**進捗台帳のみ**で、Server製品コードやデプロイは変更しない。
- **未完了**：長期I/O停止でqueueが尽きる場合のS行欠損、電源断時に未fsyncの原本消失、rollback自身が失敗した場合の復旧、X270 Zulu8 32bit／実車/disk-full。サンプル欠損ゼロ、耐久E2E成功、本番配備済みとは記載しない。
- 最新Agent mainを使ったFastAPI/PostgreSQL E2Eは引き続き**NOT RUN**。過去の固定Agent成功CIとは区別。Agent開発中の初回LF文字エスケープ不備によるコンパイル失敗 [run #38369266614](https://github.com/zawa356/RomRaider_agent/actions/runs/38369266614) は修正しており、失敗履歴はAgent台帳に残す。



### 2026-10-13 — チャット上限に伴う引継ぎ正本

- [詳細引継ぎ（このチャットの作業・現在のmain・両repo・合成CI・未実施E2E・次Phase）](handoff/2026-10-13_chat_handoff.md)を追加。**開発コードや仕様を変更する作業ではない**
- 引継ぎスナップショットのServer/Agent main SHAは作成時点のもの。新チャットでは必ずGitHubで最新を検証する
- 特にAgentの「E2E success表示だが実テストstep=skipped」と固定pin版の本物のE2E successを混同しない

### 2026-10-13 — Phase 2.1-D2b-2b：製品Agentの最新・滞留run公平配送

- [Agent PR #13](https://github.com/zawa356/RomRaider_agent/pull/13)をAgent mainに統合。SQLiteの成功ACK台帳で3回は最古run、4回目は最新runを選択し、再起動後も公平配送スロットを保持
- [Windows/Linux spool CI](https://github.com/zawa356/RomRaider_agent/actions/runs/38361475995)で新FairDeliveryTest 19チェックと既存契約試験が成功。[合成Server E2E](https://github.com/zawa356/RomRaider_agent/actions/runs/38361475795)も成功
- 未ACK／障害発生時には公平配送スロットを進めず、重複除去・profile待ち・バッチ確定ACKを変更しない
- **残課題**：旧PoC Streamの200,000行メモリqueueが飽和した場合、取得済み原本を完全復元できない。欠損数の記録は既存実装にあるが根本的な飽和防止は未実装。Phase D2b-2cとして区別する
- Windowsの実車X270 Zulu 8 32bit・電源断・disk-full試験、本番配備、走行中操作は実施していない

### 2026-10-13 — Phase 2.1-D2b-2a：旧TSVの不可逆欠損リスクを低減（Agent側）

- [Agent PR #12](https://github.com/zawa356/RomRaider_agent/pull/12)／Agent main `3086fd5839a5d876989cae22f89fd5ec5b7952f5`：旧`Stream.java`のキューdequeue後TSV書込失敗での原文破棄を停止。fsync成功まで保持し、読取り側と書き込み側でI/O同期
- 旧Receiverの`.sent`を根拠にした**元TSVの自動削除は無効化**。製品Server ACKとは異なるため、未読TSVの喪失を避ける
- bounded queue上限超では依然元観測を復元できない。復旧後に`E queue_overflow lost_lines=N`で**検知した欠損数を明示**。無欠損の完成扱いにしない
- [PR上のWindows/Linux合成CI](https://github.com/zawa356/RomRaider_agent/actions/runs/38355405529)：`Stream.java`をtest stubでコンパイルし、Windows／Linux各19チェック成功
- [Agent履歴台帳](https://github.com/zawa356/RomRaider_agent/blob/main/docs/product_v1_implementation_progress.md)と[設計判断 D-029](https://github.com/zawa356/RomRaider_agent/blob/main/docs/08_decisions.md)に経緯を記録
- **未試験**：X270 Zulu8 32bit、物理電源断・disk-full、満杯queueでの元行の完全保全、最新／過去の公平配送。Agentの実ECU操作・Serverの業務APIは変更していない

### 2026-10-13 — Phase 2.1-D2b-1：製品Workerの永続backoff・障害停止と旧PoC欠損分析

- [Agent PR #11](https://github.com/zawa356/RomRaider_agent/pull/11)で、`v1_delivery_state`による再試行回数／次回期限／要調査停止のSQLite永続化、2秒開始・最大120秒の指数backoff、明示起動の独立`ProductBridgeWorker`を実装。Logger JVM内・ECU操作系は変更しない
- ファイル既読後の消失・symlink・64ファイル超は安全側に停止。`ProductBridgeOnce`も永続停止ゲートを経由し、手動CLIからの暗黙迂回を禁止
- [Agent CI #38351975064](https://github.com/zawa356/RomRaider_agent/actions/runs/38351975064)：Windows/Linuxそれぞれ**SQLite42＋HTTP41＋旧TSV16＋増分37＋retry47＋監視14＋別JVM11＝208項目PASS**。別JVMで定義→計測バッチ→ACK保持を合成HTTPモックで確認
- **旧PoC側の未解決重大リスク**：`Stream.offer()`はqueue満杯で行破棄、`writerLoop()`はキューから行を取り出した**後**にwriteが失敗するとバッファを破棄し得る。`cleanupSpool()`は旧Receiverの`.sent`完了と14日基準でTSVを削除し、製品v1のSQLite／DB保存確定ACKと独立する。製品Workerが初めて監視する前の元TSV消失は検知できない
- [詳細・次Phaseの保全対象](https://github.com/zawa356/RomRaider_agent/blob/main/docs/product_v1_delivery_worker.md)：D2b-2で上流データ保全・旧ファイル削除条件と最新／過去の公平転送を検討。Retry-After・409/422レコード隔離・実車／disk-full／電源断・安全Supervisorは未実装
- **Server側の実E2E pinはD2a時点のAgent commit 668ad523**であり、今回のWorker／永続backoffを含む実Server E2Eは未検証。Client単体CIが成功しても製品完全導入とは扱わない

### 2026-10-13 — Phase 2.1-D2a：最新増分Agentを実Server E2Eへ再pin（CI合格）

- [Agent PR #9](https://github.com/zawa356/RomRaider_agent/pull/9)をmainへ統合。実Server E2Eに使用するJavaテストを旧TSV全量2観測から、新しい`IncrementalTsvBridge`の**定義1行ごとの取込・複数回再起動・未完結LF行・追記3観測**へ更新
- Server [PR #24](https://github.com/zawa356/RomRaiderServer/pull/24)でAgent main **`668ad5230e7e3db4fc592311c857906f43802ad3`** のJavaソース・実E2Eスクリプトを7ファイルのGit blob SHA照合付きテスト専用スナップショットへ更新。原本SHAと各コピーSHAを実際に照合
- CIで実FastAPIと使い捨てPostgreSQL 16へProfile登録→3観測のバッチ送信→全件ACK→**別SQLiteから同じ元TSVを2/2/1行で再取込して重複だけのACK**を検証。DB上の観測3件、Profile1件、`synthetic`属性を照合
- [実E2E CI #38349855164](https://github.com/zawa356/RomRaiderServer/actions/runs/38349855164)で**Agent source manifest照合→Java8コンパイル→途中行／再起動／増分取り込み→実HTTP全件ACK→PostgreSQL観測3件・Profile1件・synthetic属性→別SQLite重複再送**が全てPASS。単なるHTTPモックではない
- [製品版Server CI #38349855179](https://github.com/zawa356/RomRaiderServer/actions/runs/38349855179)：PostgreSQL契約・認証テストとDockerビルド／起動の両ジョブPASS。[旧PoC CI #38349855161](https://github.com/zawa356/RomRaiderServer/actions/runs/38349855161)：回帰ジョブPASS
- Agent／ServerにまたがるCI専用ソースの更新。Agentの車載RuntimeやECU操作には触れない
- 今回もPrivateリポジトリ間を自動追従しない。将来のAgentコード変更時はpin見直しが必要。本物のWindows X270 Zulu 8 32-bit・実ECU／K-Line・Logger callback／常駐スケジューラ・disk-full／電源断・古いQueue overflowの改善は未検証

### 2026-10-13 — Phase 2.1-D1：TSV増分読み込みとローカルSQLiteカーソル保全

- [Agent PR #8](https://github.com/zawa356/RomRaider_agent/pull/8)をmainへ統合。従来の読み取り専用TSV全量再走査を、永続offset／行番号／metadata snapshot付き`IncrementalTsvBridge`に変更。明示CLIで最大256完結行／1回、Logger callback・安全ゲート・旧TSV送信は未変更
- SQLite原本commit後にのみsource cursorを更新し、元ファイルの短縮／既読先頭・境界hash不一致／fileKey変更・CAS競合を保全側へ停止
- [Agent CI #38348638979](https://github.com/zawa356/RomRaider_agent/actions/runs/38348638979)：**WindowsとLinuxの双方で合成136チェックPASS**（SQLite42/HTTP41/旧TSV16/増分37）。原本commit直後cursor更新前の故障注入→再起動時の不変IDで冪等再処理を実DB検証
- [失敗CI #38348269336](https://github.com/zawa356/RomRaider_agent/actions/runs/38348269336)：新規故障注入fixtureのタブ文字誤記で失敗。fixture修正後PASS、原因・修正履歴はAgent側に保持
- [増分取り込み保全設計](https://github.com/zawa356/RomRaider_agent/blob/main/docs/product_v1_incremental_import.md)：fileKey不明時はアンカーhashが補助になるのみで完全なファイル改変検知ではない。旧Queue overflow/TSV writer error/原本削除・電源断・disk-fullの欠損は未解決
- **Server側pinしたAgent実Server E2Eはcommit 6dd46835の旧版**。今回のD1を含む新Agent版との実E2EはD2で再pinして検証するまで未確認。本番操作・自動デプロイは引き続き無効

### 2026-10-13 — Phase 2.1-C2a：実Java Agent→実FastAPI/PostgreSQL E2Eが初めて成功

- Private間認証なしで実結合をCI実行するため、Agent **commit `6dd46835a200d961d517f5bb54f11eb2d7bdd2af`** の実Javaソース5ファイル＋E2EスクリプトをServerの**テスト専用スナップショット**へGit blob SHAと共に固定。原本とコピーのblob一致確認。試験前に各ファイルのSHAを再検査
- [新E2E GitHub Actions](https://github.com/zawa356/RomRaiderServer/actions/runs/38346035656)：`javac --release 8`、使い捨てPostgreSQL 16＋実FastAPI＋端末認証、旧RRBridge合成TSVからSQLite→ProfileRevision PUT→観測2件POST→受領ACK、**別SQLiteから同じ原本UUIDで再送**
- Server DBを直接SELECTし、**`v1_records=2`／`v1_profile_revisions=1`／`source_kind=synthetic`で成功**。HTTP契約モックではなく、本物のJavaコード・Server API・Postgresに対する合成E2E成功
- [試験コードと固定版・追従手順](../tests/e2e/agent_v1_snapshot/README.md)。Agentの現在／将来の`main`に自動追従するわけではないため、最新版E2E成功とは記載しない。Agentリポジトリ側のPrivate相互読取token未設定のE2Eは引き続きNOT RUN
- **未検証**：ECU実機→Logger callback→TSV、X270 Windows/Zulu8 32-bit、常駐自動取り込み、長距離ログ、旧Queue drop/TSV削除・欠損対策、物理電源断、公開TLS接続、MCP/操作制御
- 本番デプロイや車載Profile自動変更は一切追加していない

### 2026-10-13 — Phase 2.1-C1 main CIのWindows Maven403回復

- **失敗履歴**：[Agent main CI #38339774312](https://github.com/zawa356/RomRaider_agent/actions/runs/38339774312)で、Windows runnerがビルド用SQLite JDBC JARをMaven Centralから取得中にHTTP403。テスト開始前に終了。LinuxはPASS
- [Agent修正PR #6](https://github.com/zawa356/RomRaider_agent/pull/6)：公式Maven Centralの2エンドポイントをretry・timeout付きで使用し、破損JARを検査してから配備、GitHub Actionsに依存JARキャッシュを追加
- [修正PR CI](https://github.com/zawa356/RomRaider_agent/actions/runs/38340311640)：Windows/Linuxともに**Spool42＋HTTP41＋TSV16＝99件PASS**
- 実Server E2EはPrivateリポジトリ間の読取認証未設定で引き続き**NOT RUN**。元のmain CIの失敗と対処を過去履歴から消さない

### 2026-10-13 — Phase 2.1-C1：旧RRBridge TSV→製品v1 SQLiteの非破壊取込

- [Agent PR #5](https://github.com/zawa356/RomRaider_agent/pull/5)で、旧RRBridgeのM/S/E TSVを読んで不変ProfileRevision、Observation、Eventの製品v1 JSONを生成する`LegacyTsvBridge`と、一度だけ取り込んでHTTP交換する明示実行用`ProductBridgeOnce`を追加
- [Agent CI](https://github.com/zawa356/RomRaider_agent/actions/runs/38339596749)：Windows／Linuxそれぞれ**SQLite 42 + HTTP 41 + Legacy TSV import 16 = 99項目成功**。合成ログの再読み込み・部分行・原本UUID保存を検証
- [E2E Workflow](https://github.com/zawa356/RomRaider_agent/actions/runs/38339596746)：GitHub両リポジトリがPrivateで相互読取用認証情報未設定。**E2E試験はNOT RUN**。後続の実FastAPI＋PostgreSQL接続テストを準備したが、合格したとは扱わない
- ServerのDB/API本体に変更なし。旧RRBridge`Stream.java`のLogger callback／Queue／TSV senderも未変更。自動起動なし、実車X270／Zulu8 32-bit未確認
- 既存PoCのキューあふれ／TSV writer失敗／14日保持による欠損リスクは残存。全TSV再走査も長期運用には不適。AgentからECU→Serverの無欠損を保証するにはPhase 2.1-C2/Dの検証が必要
- 本作業で合わせて、既存台帳に混入していたリテラル`\\n`をMarkdownの実改行に修復（意味は変更しない）

### 2026-10-13 — Phase 2.1-B：Agent製品v1のHTTP送信／厳密ACK（合成CI合格）

- [Agent PR #4](https://github.com/zawa356/RomRaider_agent/pull/4)で、既存SQLite outboxへ独立したJava8 HTTP送信部品を追加。ProfileRevision先行PUT、同runバッチPOST、完全ACKのみをローカル確認済みにする
- [Agent CI](https://github.com/zawa356/RomRaider_agent/actions/runs/38337837720)でWindows/Linuxそれぞれ**SQLite42件＋ローカルHTTP契約モック41件＝83件成功**。200/201 profile status対応、接続失敗、401/409/422/503、不正レスポンス、ACK喪失後の再起動・重複受信を試験
- セキュリティ：リダイレクト追従無効、HTTPS必須（開発loopback HTTPのみ可）、Bearerのヘッダ出力禁止
- **重要：本物のRomRaiderServer v1（PostgreSQL）へのend-to-endではない。** 既存RRBridgeのLogger callback組込、バックオフ、409/422隔離、Windows X270 Zulu8/実ECU動作はPhase 2.1-C/Dの対象
- Agent側の詳細履歴：[実装進捗](https://github.com/zawa356/RomRaider_agent/blob/main/docs/product_v1_implementation_progress.md)、[送信IFの現状](https://github.com/zawa356/RomRaider_agent/blob/main/docs/product_v1_http_transport.md)
- Server本体API・DBにはこの作業で変更なし

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
- 安全側の修正履歴：承認取消・計画更新後のlease再使用を禁止、不明ローカル実行履歴があるとclaimを拒否、古いreconcile時刻を409で拒否、通信本文サイズ制限を追加
- [PR #15](https://github.com/zawa356/RomRaiderServer/pull/15)／[製品CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38330361959)：PostgreSQLの合成結合試験**28件PASS**、Docker起動／端末登録も成功。[旧PoC CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38330362074)：supervisor／composeの2ジョブ成功

### 2026-10-13 — Phase 1.1-C：ECU／Logger能力情報の同期（作業中）

- Alembic `0002_capabilities`で不変Snapshotとパラメーター適合度の索引表を追加（過去原本を更新しない）
- `PUT /api/agent/v1/capability-snapshots/{snapshot_id}`を端末認証付きで追加
- 定義上の存在／ECU適合推定／実取得確認／非対応／不明を区別したまま保存（定義に存在するだけで実取得済みとは扱わない）
- Idempotentな再送、同一ID別内容の409、重複パラメーター422、認証拒否を実DBで検証
- [PR #14](https://github.com/zawa356/RomRaiderServer/pull/14)／[Product CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38329257391)で**14件PASS**、migration `0002_capabilities`、Dockerスモーク成功。[PoC CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38329257275)も成功。実ECU上での能力発見は**未検証**

### 2026-10-13 — Phase 1.1-B：端末資格情報の管理（作業中）

- 製品版Server専用のローカル管理CLIでトークン再発行・端末失効・状態照会を実装
- 端末IDは不変、資格情報のフィンガープリントだけDB保存。再発行時に旧トークンは即時失効
- 失効は冪等で再有効化は認めない。既存観測・定義・計測実行を削除しない
- PostgreSQL結合試験で旧tokenの401、再発行tokenの200、失効後401、他端末への影響なしを検証
- [PR #13](https://github.com/zawa356/RomRaiderServer/pull/13)／[Product CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38328824590)で**11件PASS**、Docker起動確認。[PoC CI](https://github.com/zawa356/RomRaiderServer/actions/runs/38328824542)も成功

### 2026-10-13 — Phase 1.1-A：Alembicとスキーマ管理

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

### 2026-10-13 夜 — Agent Phase 4b-2d-2b-1 lock分離独立PoC

- [Agent PR #27](https://github.com/zawa356/RomRaider_agent/pull/27): 純粋な.writer.lockは旧writerとの二重起動を両起動順で許す反例。候補は別writer lock＋journal 8MiB位置の1byte guard。既存whole-file lockと交差し、データ領域の別JVM readはWindows/Linuxで成功。旧writer/製品Worker/正式IF/Serverコード・DBは変更なし。
- 初回Linux試験で同一JVMの診断handle closeがPOSIX guardを消すFAIL。所有RandomAccessFileだけで検証する修正後、別JVM所有権matrix39＋既存journal99=138、SQLite/receipt344、計482チェックがWSLとVPS1でPASS。
- Agent journal PR CI38407692420とspool CI38407690527は両OS実ステップsuccess。証跡文書追加後の最新SHA CIは確認中。Agent既存writerのWindows live read BLOCKEDは継続。今回実PostgreSQL E2EはNOT RUN。
- VPS引継ぎとの差: 提供SSHユーザーcodexを利用、新規/home/codex/git/romlogger-codex-4b2d2b-agentで検証、Gitはlocal ghでpush。資格情報をVPSへ転送せずGit bundleで同期。
- PoC→運用、同一JVM別handle統合、quota変更、lockファイル置換/削除は保留。watermark独立PoCが次工程。

#### 2026-10-13 22:52 JST — 2b-1統合証跡

- Agent PR #27 merged、main 60ae43cb366e2d2141905526af3675f0ceb0a759。最新PR76889a6のjournal CI38407931755とspool CI38407931735はWindows/Linuxの実試験/全job success。
- Agent main journal CI38408152381両OS job/実ステップsuccess、main spool CI38408153111両OS試験success（Windows job完了待ち）。後続watermarkはこのCIの最終完了を確認して分岐する。

### 2026-10-13 23:08 JST — 4b-2d-2b-2 watermark候補 / Windows BLOCKED

- [Agent PR #28](https://github.com/zawa356/RomRaider_agent/pull/28): RLC1 104byte候補(UUID/sequence/offset/fileKeyHash/prefixSHA/CRC)、所有handle fsync→tmp force→atomic replace→directory force。原本/marker破損・置換・連番退行・途中更新を拒否、未公開完全tailを取込対象から除外。製品Worker/DB/ACK非接続。
- WSL/VPS1 Linux: 新watermark56＋OS primitive3＋既存journal138=197、SQLite/receipt344、合計541チェック相当。最新VPSはjournal197確認、SQLite344は直前0bef713で確認（以後製品/receiptコード非変更）。
- 初回Windows journal CI38409471808/38409589169 FAIL。OpenJDK Windowsの公開fileKey()は常時null。この条件を緩めずWindowsではwatermark56ケースBLOCKED/NOT RUN、3拒否/保全＋3storage primitiveのみを検証。修正CI38410294031のWindows/Linux実試験success、最新文書SHAのCIは確認中。
- [公式実装](https://github.com/openjdk/jdk17u/blob/master/src/java.base/windows/classes/sun/nio/fs/WindowsFileAttributes.java)を確認し、ensureAccurateMetadataで解決する推測は撤回。既存起動設定への追加はしない。
- 2b-3新writer/reader/SQLite結合は**両OSwatermark成立ゲート未達でBLOCKED**。rotation候補は16ファイル/各8MiB、原本+identity+watermark+lockの保全、ACK前/不明時削除禁止、原本不変path/UUID、persistent cursor/receipt同一transactionを設計記録のみ。
- 代替候補: hardlink anchor/isSameFile、Windows native file index、UUID内包原本形式。既存v1_source_claimsのsession単一source規約とrotationの整合、dir sync/物理電源断、同一JVMhandle closeも未解決。運用承認待ちとして残す。

### 2026-10-14 09:52 JST — 最終統合・検証結果（利用制限から再開）

- Agent PR #28 merged、実装main `e3d76c22fba8fce7f41ad03f6f7c0b386a5794d9`。最新PR CI38492040774/38492040888、main CI38492256469/38492256464は両OS全jobsと実試験success。
- VPS最終実試験f90f103: journal197＋SQLite/receipt344=541 PASS、実装mainへ同期・clean。WSL legacy test.shはignored公式RomRaider1.1.0-NOV26-2025 compile-only jar導入後44 PASS/0 FAIL (最初の欠落compile失敗もAgent履歴に保存)。
- Windows CI: journal143＋SQLite344=487 PASS。watermark full56はBLOCKED/NOT RUN、primitive3+安全拒否/保全3だけ成功。directory force Windows UNCONFIRMED、Linux SYNCED観測。
- [Agent最終文書PR #29](https://github.com/zawa356/RomRaider_agent/pull/29)にreport/worklog/履歴/進捗/入口の最終証跡。現在地はmain/PR/CIを照合して取得する。VPSのServer専用cloneは/home/codex/git/romlogger-codex-4b2d2b-server、文書統合後の両mainを同期する。
- VPS caddy/ssh active、mcp-ssh/ssh-mcp-chatgpt running、codex Java試験残存なし。サービス設定/再起動・認証・既存DB変更コマンドなし。MCP API機能healthはNOT RUN。
- **終了区切り: 独立PoC+安全拒否+文書同期まで。2b-3の結合はBLOCKED/未実装。** Windows原本識別方式とsession/source claim/rotationの契約が次レビュー対象。

## 2026-10-14 日中 — Agent Phase 4b-2d-2b-3a 原本同一性比較

- [Agent PR31](https://github.com/zawa356/RomRaider_agent/pull/31)、[比較設計](https://github.com/zawa356/RomRaider_agent/blob/feat/day-3a-identity/docs/phase_4b_2d_2b_3a_identity_comparison.md)、ADR D-041。test-only fixtureのみ、製品RLJ1/RLI1/RLC1/Worker/DB/ACK/正式IFの変更なし。
- A hardlink anchorは同内容別inode置換を区別するが、whole-set複製は関係を再構築できる。C UUID/headerもコピー可能。A/C単独識別を否決。B NTFS native volume/file indexは推奨実験候補だが製品採用ではない。
- WSL/VPS Linux journal222（旧197+比較25）PASS、CloudPC jr2twt専用clone実SQLite/receipt344 PASS、合計566 unique checks。spool322追加実行は同じ部分の回帰で二重加算しない。
- Agent CI38495966977/f5d87af：Windows Server2025 Temurin17 x64 journal168（旧143+25）+SQLite344+native18=530 unique checks PASS、両OS適用試験steps success。LinuxのWindows native stepは意図したSKIPPED。最新docs head/main CIは後続記録を参照。
- Linux同JVManchor別handle closeはlegacy guardを失う反例。Bはテスト専用JNA5.14.0 core（固定SHA）、NTFS既存read-attributes共有handleのみ。製品lib/distへの追加なし。
- 3b/3c/3dは所有handle binding・expected identity/highwater永続ledger・directory durabilityゲート未達でBLOCKED。Windows既存watermark56 NOT RUN、dir UNCONFIRMED。次の安全な小PhaseはJava8/x86とbound handle read-only診断。実車/ECU/X270/物理電源断/OS再起動/本番配備はNOT RUN。
- CloudPC MCP利用成功、既存gh権限を使用。既存サービス/認証/本番DB変更なし。

## 2026-10-14 — Agent安全代替Phase 3a-compat

- [Agent PR32](https://github.com/zawa356/RomRaider_agent/pull/32)、D-042、[設計](https://github.com/zawa356/RomRaider_agent/blob/test/day-3a-compat/docs/phase_4b_2d_2b_3a_compatibility.md)。同じnative READ handleからNTFS identity/bytesを取得するtest-only診断。NOT_COMMITTED、製品DB/ACKに使わない。
- 実Windows Server2025/Zulu8 **1.8.0_504・32bit**でdata-model32をassert。native18+READ21+comparison25+split39+watermark安全拒否6=109 checks PASS。x86 SQLite/product試験はNOT RUN。X270/Windows10/RomRaider同JVMの成功ではない。
- Windows17/x64 journal168+SQLite/receipt344+native18+READ20=550 unique PASS。Linux CI222+344=566、VPS dedicated phase cloneでjournal222回帰PASS。code032f294 CI38496691143全3jobs/適用steps success。最新docs-head/mainCIは後続記録。
- コピーされたpathnameから旧reader handleへidentityが誤結合しないこと、in-place改変は同じIDでも既読SHAで拒否すること、old writer mandatory lock下のnative READ拒否を実確認。
- 3a PR31/main c58a4ba、Server42/main31ac365のmainCI38496452266/38496457020successも確認済み。
- 3b/3c/3d統合ゲートは未達。writer-owned fsync binding、Windows directory syncUNCONFIRMED、persistent expected ledger/highwaterが未実装。次はsafe alternative 3a-writer-binding、製品形式/DB/Worker/本番は変更しない。

## 2026-10-14 — Agent安全代替Phase 3a-writer-binding

- [Agent PR33](https://github.com/zawa356/RomRaider_agent/pull/33)、D-043、[設計](https://github.com/zawa356/RomRaider_agent/blob/test/day-3a-writer-binding/docs/phase_4b_2d_2b_3a_writer_binding.md)。同一native handleでNTFS identity/owned prefix/WriteFile/FlushFileBuffers、coordination＋native guardのtest-only検証。marker/製品DB/ACKへ接続なし。
- Windows17/x64 nativewriter44、actual Zulu8 1.8.0_504/x86 nativewriter45 PASS。code96e4f15 CI38497582903全3jobs適用steps success、raw Windows logsで件数/actual bitnessを照合。最新docs/mainCIは後続記録。
- Windows17 journal168+SQLite344+native18+READ20+writer44=594 unique checks。x86 subset154（18+21+45+25+39+6）。x86 SQLite/full旧watermark56はNOT RUN。VPS専用phase clone journal222+SQLite344=566 PASS、native writer Linux runtime NOT RUN。
- 原本を置換しない5別JVM所有権matrix、native reader共有、rename拒否、quota/部分原本/改変/UTF16/closed/fault latch、実readonly native flush拒否、flush前後haltを確認。物理電源断/実ENOSPC/OS再起動/X270/実ECUではない。
- 3a比較/compat/nativewriterのTEST primitivesまで成立。既存RLC1 full56はWindows fileKeyでBLOCKED、Windows dirUNCONFIRMED、新marker version・永続expected ID/highwater/原文receipt同transaction・rotationは未実装。3c/3d/製品ライブ配線はBLOCKED。
- 次Phase3bは別branchで新identity tag/versionとmarkerの安全設計・負試験が候補。RLC1の無断読替え、dirUNKNOWNのPASS昇格、SQLite/ACKへの暗黙配線をしない。
- Agent32/Server43のmainCI38497117325/38497121453全適用steps成功確認済み。既存サービス/認証/本番DB非変更。

## 2026-10-14 日中最終verification — 3小Phaseの区切り

- Agent31/32/33、Server42/43/44全MERGED。コードcheckpoint Agentbd8e70ba88fe2e0e5c8af43379d31651a7594088 / Server5a9cdb3eccff47aa065e7078f4d072c8a6fe28c1。Agent[最終報告PR34](https://github.com/zawa356/RomRaider_agent/pull/34)でreport/worklog/進捗を最新化。
- Agent mainCI38498047914 attempt1はWindows SQLite依存JAR取得が両Maven endpointでHTTP404、実SQLite/native-following steps NOT RUN/SKIPPEDでFAIL。原本/コード不具合を示すログではなかった。同一version/条件でretryしattempt2全3jobs/実steps success、失敗を隠さずAgent worklogへ保存。
- merged mainのCloudPC VPS実試験 journal222+SQLite/receipt344=566 PASS。Windows17/x64594 unique checks、actual Zulu8 1.8.0_504/x86subset154、WSLlegacy44 PASS。x86 SQLite/full旧watermark56/実Agent→PostgresE2E/物理電源断/X270/ECUはNOT RUN。
- Server mainCI38498052348のunit/compose/SQL round-trip適用steps success。これを実Agent E2Eと呼ばない。最終docs-only merge後のmain SHAは再取得する。
- native NTFS candidateのID/read/write/flush same-handle primitivesは成立。旧RLC1 Windows/full56、dir同期UNCONFIRMED、新identity-tag/marker version、永続expected ledger/highwater/receipt同transaction、seal/rotation、製品ライブ配線は未成立。次の安全な作業は別Phase3bの独立marker設計・負試験。
- CloudPCサービスread-only確認：caddy/ssh active、mcp-ssh/ssh-mcp-chatgpt running。試験Java子プロセス残存なし、既存サービス設定/認証/本番DB変更なし。
- 詳細・正確な再開コマンド：[Agent日中report](https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/codex_daytime_report.md)、[追記worklog](https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/codex_daytime_worklog.md)。

## 2026-10-14 — 最終レビュー追加Phase 3a-writer-integrity / D-044

- [Agent PR36](https://github.com/zawa356/RomRaider_agent/pull/36)でprivate TEST native writerのpost-flush new frame照合を強化。flush直後にpayload x→yとCRCを再計算すると、old prefix/CRC/sequenceだけでは誤ったmemory Proofを返す不足をレビューで発見。製品/marker/DB/ACKへ配線しておらず影響は候補fixture内。
- RED213fd22 CI38499434376/rawjob115642618293でWindows17/x64 AssertionErrorを実再現。x86 REDはx64 baseline失敗でSKIPPED/NOT RUN、Linux回帰success。
- Fixc72ad0d：owned handleのpost-flush new frameをWriteFileへ渡したexact bytesと照合し、改変はProof拒否/terminal latch/CRC-valid原本保全。CI38499593483全3jobs success、raw115643128338/115643128598で実確認。
- 最新x64writer46/actualZulu8 1.8.0_504 x86writer47 PASS。combined Windows17/x64596、x86subset156、Linux566。旧594/154/writer44/45は当時のfixture範囲で、この新負試験の成功ではない。最新docs-head/main統合は後続記録。
- 4小Phase（比較/compat/nativewriter/integrity）まで。RLC1 Windows full56/dirUNCONFIRMED、新marker version/永続expected ledger/highwater/rotationのゲートは変わらない。次は別Phase3bのtest-only設計。
