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

## 2026-10-14 11:24 JST — 4小Phaseの最新最終verification

- Agent36/Server46全MERGED、コードmain126c174a93a6b8a1cf3aa14e90bd6c4902b94055/8804caac79bf887d69dc26087139a95bac500516。最新Agent mainCI38500236200/Server mainCI38500240744全適用steps/jobs success、rawWindows logsでwriter46/47とactualdata-model32を確認。
- 最終レビューfixを含む4Phaseまで完了：原本3案比較、native READ/Zulu8x86、native ownedwrite/flush、post-flush exact-frame integrity。最新Windows17/x64596、x86subset156、Linux/VPS566、legacy44。旧594/154は追加負試験前の範囲。
- Agent[日中report](https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/codex_daytime_report.md)/worklogを最新化。最終metadata docs/daytime-integrity-finalは実行コード変更なしでpublished HEADは再取得する。
- 3b新版marker設計・独立負試験が次。RLC1Windows full56 NOT RUN/BLOCKED、dirUNCONFIRMED、新identity-tag/expected ledger/atomic highwater/receipt/rotation/実機/製品配線の未成立を維持。
- Product code/protocol/DB/Logger/サービス/認証は変更なし。RED213fd22/CI38499434376とfixc72ad0d/GREEN/merged mainまでGitで追跡可能。

## 2026-10-18 — Agent Phase 3b / 3c-1 / 3d-1（Claude、Windows開発VM）独立PoC

- Agent [PR39](https://github.com/zawa356/RomRaider_agent/pull/39)（3b RLC2）、[PR40](https://github.com/zawa356/RomRaider_agent/pull/40)（3c-1 ledger）、[PR41](https://github.com/zawa356/RomRaider_agent/pull/41)（3d-1 rotation）をMERGED。最終Agent mainは `512c8b7`。すべて`src/main/.../prototype`と試験に閉じており、**製品writer・Worker・`v1_*`表・Server IF/ACKへは配線していない**。
- 3b: 新marker RLC2（identity tag付き。RLC1は読み替えない）。PR CIでWindows x64 96 / Linux POSIX 94 / actual Zulu8 x86 97 PASS。Windows directory durabilityは**UNKNOWN**のまま。
- 3c-1: expected identity・highwater・原文receiptを同一SQLite transactionで管理し、3bの反例（stale marker、偽造コピー）をclaim済みsourceで拒否。ledger 27/27/28 PASS。receiptはACK対象外。
- 3d-1: seal、RLM1 manifest、16本quota（明示停止、削除なし）、manifest順のsession ingest。rotation 43/43/44 PASS。
- Server側: 本repoのコード・プロトコル・DBは変更なし。ローカル（Windows VM、PostgreSQL 16.15）で pytest 57 passed。[Server PR48](https://github.com/zawa356/RomRaiderServer/pull/48)でE2E生成物を.gitignoreへ追加。
- 残るゲート: Windows directory durability、物理電源断・OS再起動、製品`v1_source_claims`とsession契約への統合、RLC1からの移行、実機。詳細は [Agent report](https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/claude_phase3b_report.md)。

## 2026-10-18 11:45:42 +09:00 — acceleration Phase A/B (Agent PR43, CI pending)

- Agent targeted review of PR39–41 found no new critical core defect; existing POSIX path-sampled identity/Windows directory durability UNKNOWN/TOFU/history limitations retained.
- Read-only RLC2/SQLite/RLM1 Supervisor diagnostics API and human/JSON CLI implemented in Agent PR43: https://github.com/zawa356/RomRaider_agent/pull/43 . Stable codes cover orphan/tmp, stale marker, identity, manifest, highwater/receipt/claim, quota, durability UNKNOWN and sealed changes.
- SQLite mode=ro alone created WAL/SHM in RED test. Inspector now requires externally quiesced closed checkpointed snapshots, refuses WAL/SHM/journal and opens immutable read-only. No automatic repair/checkpoint, no ACK authority.
- Local real SQLite diagnostics: Windows JDK17 x64 34 PASS; actual Zulu8 x86 35 PASS; VPS Ubuntu24.04 JDK17 34 PASS. Existing VPS ledger27+rotation43 PASS. CI pending; main integration not yet complete.
- Product v1 Worker, production DB and Server wire protocol unchanged. Next: CI step verification and normal merge, then opt-in isolated adapter/E2E. Agent acceleration worklog is the resume entry point.


### 2026-10-18 11:47:00 +09:00 — Agent PR43 merged, PR CI verified

Agent merge 77089a368d3c562bb5b5e8f01ae9e4e6ba90c606. PR CI journal39091138681/spool39091138687 success; real diagnostic steps Linux/Windows and actual Zulu8 x86 step all success. Agent post-merge CI pending. Local Server PostgreSQL16.15 regression: 57 passed (compileall, upgrade twice, check also exit0). Earlier pending entries are historical checkpoints.


## 2026-10-18 11:55:55 +09:00 — acceleration Phase C (Agent PR44, CI pending)

- Agent PR44 https://github.com/zawa356/RomRaider_agent/pull/44 adds executable opt-in synthetic RLC2-to-v1 projection, reusing existing IncrementalTsvBridge conversion via a no-I/O sink. Input RLC2 markers must exactly match persisted ledger highwaters/receipts; manifest order preserves metadata; sample sequence/session reset and TSV conflicts are refused.
- Projection returns source UUID/identity/highwater, original receipts and v1 profile/record JSON in memory only. No product DB/outbox, Worker or HTTP/ACK route is activated. Windows directory durability UNKNOWN retained.
- Current v1_source_claims stores one source key per payload session; physical rotation has multiple UUIDs. Direct product claim/cursor migration remains BLOCKED; Phase D will use dedicated preview tables for a manifest-session and child source claims.
- Local projection Windows17 x64 20, Zulu8 x86 21, VPS Linux17 20 checks PASS; exact comparison against separately invoked legacy importer JSON/IDs/profile. Existing full product spool regressions PASS on Windows and VPS; diagnostics remain 34/35/34. PR CI pending.
- Previous Phase B Agent main CI39091295337/39091295292 and Server main CI39091434142 all success.


### 2026-10-18 11:58:44 +09:00 — Agent PR44 merged / PR CI verified

Agent merge b862651902ad25dc86a3233c00df77dddcaa3919. PR CI39091762536/39091762488 all applicable Linux/Windows/Zulu8 x86 steps success. Existing real-Server workflow39091762524 is gated success with actual REAL Agent→FastAPI→PostgreSQL step SKIPPED (missing private-repo read secret), not E2E PASS. Agent main CI39091939531/39091939477 pending. No formal ACK route added to projection.


## 2026-10-18 12:12:07 +09:00 — acceleration Phase D (Agent PR45, CI pending)

- Agent PR45 https://github.com/zawa356/RomRaider_agent/pull/45 adds dedicated RLP1 .rlc2-preview.db output, preview-only schemas and explicit synthetic CLI. One IMMEDIATE transaction persists manifest history, one logical session claim plus child sources, original receipts, highwater and unchanged v1 JSON. SQL forbids ACK eligibility; no production v1 table, Worker, Server endpoint or original mutation.
- Replay verifies immutable fields, prior row counts and manifest history. Missing/tampered rows fail closed without reconstruction. Test covers foreign/renamed product DB refusal, original bytes, rollback of all six tables, separate-JVM CLI replay, lane conflict and durable history.
- Local Windows final preview34 PASS; earlier x8632/Linux31 before three final missing-record/schema cases (final versions in CI). Linux CLI compile omission RED reproduced and fixed. Destination guard3 tests PASS. Local PostgreSQL16.15 two committed/reconnected passes verify two sources/four receipts/one profile/three records, exact receipts/JSON, no duplicates, rollback and ACK constraint. Actual Server ProfileRevision/Batch models validate locally without HTTP.
- New isolated PostgreSQL16 CI job executes this preview path without private Server checkout; actual Server model validation is explicitly NOT RUN there. Existing HTTP E2E remains separately gated/SKIPPED without its secret. Latest PR CI pending; initial push Linux+PostgreSQL jobs already success.
- Phase C Agent main CI39091939531/39091939477 and Server main39092090529 success. Next: final PR/main CI, then dedicated abrupt-stop/competition fault tests (not yet claimed by Phase D).


### 2026-10-18 12:14:56 +09:00 — PR45 CI success / normal merge requested

PR journal39092722886 includes actual Linux/Windows preview SQLite, Zulu8 x86 and private PostgreSQL16 receipt/replay/rollback/ACK-refusal steps, all success. Product regression39092722876 success. Existing HTTP E2E39092722883 gated success with actual HTTP step SKIPPED; new PG preview step ran. Agent main merge/CI evidence follows in acceleration worklog. Final preview scenario counts verified in CI; local final Windows34 and initial x8632/Linux31 history distinguished above.


## 2026-10-18 12:24:05 +09:00 — acceleration Phase E (Agent PR46, CI pending)

- Agent PR46 https://github.com/zawa356/RomRaider_agent/pull/46 reproduces/fixes abrupt preview restart failure. RED778757d: own rollback journal was refused by immutable input preflight. Fix permits only SQLite-managed recovery of positively identified RLP1 output (safe regular journal/header/identity/no unexpected WAL), then verifies owned schema. Immutable input ledger/original rules unchanged; no manual journal removal or ACK route.
- Four separate-JVM halt stages verify all-or-none receipt/record state and exact replay. Competing CLI workers, exclusive DB lock/no-ACK review, real SQLite ABORT with six-table rollback, original-byte preservation and foreign product DB+journal refusal are covered.
- Local fault tests Windows17 x64 36 / actual Zulu8 x86 37 / VPS Linux17 36 PASS. Preview regression34/35/34 PASS. Physical power loss/real ENOSPC NOT RUN. Operator dry-run/retry boundary documented; CI pending.
- Phase D Agent main39092940711/39092940692 and Server main39093054991 success; preview final CI counts34/35/34 verified from raw logs.


### 2026-10-18 12:27:44 +09:00 — Agent PR46 CI all success / normal merge requested

Journal39093449838 all four jobs success, including actual Windows/Linux preview/fault runs, actual Zulu8 x86 and PostgreSQL verification. Product39093449961 success. RED/owned-output fix and manual dry-run procedures reviewed. Input diagnostics were not relaxed. Agent main merge/CI checkpoint will follow in the worklog.


## 2026-10-18 12:46:10 +09:00 — acceleration Phase F (verification running)

- Agent automation branch pins Java jar SHA256, CPython3.12 Win/Linux x64 PostgreSQL wheels/transitives, and an observed passing PostgreSQL image digest. New Windows one-command wrapper compiles JDK17 Java8 bytecode, executes actual x64/x86 suites, restores environment, logs ignored results and optionally runs strict loopback PG/actual Server model validation. Actual x86 CI job invokes the wrapper. CI checks artifacts/source changes and cancels duplicate push/PR head-branch runs.
- Fresh isolated Python hash install PASS; wrong wheel hash rejected. Valid wrong JAR fixture replaced only after pinned SQLite checksum. Initial YAML command quoting failure fixed (block scalar).
- Full local batch found an intermittent existing Windows concurrent replace denial. Preserved old/staged/original hashes valid; exact denying handle unknown. Test-only correction verifies exact preservation/reader refusal and logs full25-progress BLOCKED when refused, while successful path still requires finalgen26. Deterministic held-marker reader case added; native101 PASS. Core publisher/retry semantics unchanged; fresh native compilation avoids stale common classes.
- Full corrected batch and final CI running. Agent/Server current production runtime/DB are unchanged. Phase E main39093698538/39093698530 and Server39093791658 success.


### 2026-10-18 12:54:25 +09:00 — Phase F local complete batch and PR CI PASS

Actual local Windows batch build/acceleration-20261018-124526.log exited0 with x64/x86, existing regressions, diagnostics35/projection21/preview35/fault37 on each explicit architecture, three destination guards, two PG preview connections and actual Server models. Local symlink fixture and old Windows RLC1 56 scenarios remain NOT RUN/BLOCKED. PR47 journal39094810643 all four jobs success (PowerShell wrapper actually ran, Linux/hash-locked PG ran), product39094810652 success. Existing HTTP E2E gated success remains separate. Normal merge requested; main proof follows in worklog.


## 2026-10-18 13:19:41 +09:00 — acceleration Phase G (Agent PR48, final CI pending)

- Read-only findings add fixed manual next_action and automatic repair false; source-only RLC1/RLC2 preflight reuses existing codec and validates observed envelope/UUID/prefix/frames without ledger/marker creation, migration or fileKey→native reinterpretation. Mixed legacy/new markers block projection; ledger lag/pending state are distinct from corruption. Existing original/durability/ACK gates retained.
- Final local preflight Windows x64 18 / actual Zulu8 x86 19 PASS. Default1000-observation/4-session workload23 checks, larger10000+10 small sessions44 Linux/45 actual x86 PASS:10100 records/10111 receipts/22 cursors/11 logical claims, exact highwaters, duplicate-free replay and input bytes.
- Identical lowercase hex now avoids per-byte Formatter. New x64 inspector validated10001 original-formatter x86 receipts unchanged. Full cold-process before/after tables include all phases/variance in Agent ingress_preflight_load.md; no throughput/power-loss guarantee. Larger replay observed VPS2086→939ms, x8611433→5010ms.
- Agent PR48 final CI pending. Current product v1 single-source claim/cursor migration and Windows directory durability/formal new-path ACK remain blocked; executable preview and diagnostics are complete.
- Phase F main Agent39095250378/39095250377 and Server39095397003 success. Next: PR/main CI, final acceleration report and synchronized resume point.


## 2026-10-18 — acceleration Phase H checkpoint integrity

- Agent PR49 https://github.com/zawa356/RomRaider_agent/pull/49 reproduces unchanged-count event-key replacement (RED b032e04). The previous preview replay inserted the original key again. Fix ec1e5bd independently validates saved source receipt extents, ordered committed prefix and exact prior projected record IDs before writes; inconsistent evidence is retained for review. No product DB schema migration, automatic reconstruction or ACK enablement.
- New negative tests cover changed event key, missing committed records/receipts with adjusted aggregate counters, and exact evidence preservation. Positive active-source append and third-source rotation still import only new rows. Windows x64 preview42/fault36/load23 and VPS Linux42/36/23 PASS; VPS10k/11-session load44 PASS. Actual x86 CI preview43/fault37/load24 PASS; local x86 final suite completing.
- Agent PR49 journal39097642181 (all four jobs) and product39097642133 success. Actual PG verification ran; actual private Server HTTP remains gated/SKIPPED, not counted as new-path ACK. Agent main result follows in final report.
- Phase G Agent PR48 merged33875a2e86dabb91f8b3a93441192595a2a7d08f; main39097392309/39097392286 success. Server PR55 mergedaf30941a4f0128a448389e3dd48d5003191bd2cd; main39097403278 success.

## 2026-10-18 20:51 JST — Codex acceleration final summary

- Agent Phase A–H completed in seven implementation PRs43–49. Final code main e1677c4e8341b1d60d61bd2be11dd57a5e459a43; main journal39124576935 (all4 jobs) and product39124576968 success. Server progress PR50–56 merged, latest code-related progress a1bc6210159f6ee736f084b6f81d3da0d5f9f500/main39124675916 success.
- Deliverables: read-only diagnostics/API/CLI; synthetic opt-in shared-v1 projection; owned/quarantined SQLite transaction store and CLI; guarded isolated PostgreSQL replay; abrupt-stop/competition/DB failures; hash-pinned CI and Windows full batch; migration preflight/manual hints;10k/11-session load/performance; exact committed record-set integrity checks. All are executable and tested; no production schema migration or new-path ACK.
- H final local preview/fault/load Windows x64 42/36/23, actual Zulu8 x86 43/37/24, VPS Linux42/36/23 PASS; Linux10k/11session44 PASS. Local PostgreSQL16.15 twice reconnect/replay and actual ProfileRevision/Batch validation PASS. Server existing regression57 passed earlier. Existing private Server HTTP E2E remains SKIPPED, not counted as HTTP coverage.
- Final report: https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/codex_acceleration_report.md ; append-only worklog in same folder. Final documentation PR50 follows implementation baseline; no code changes. Report includes all merge/CI evidence, RED/GREEN and next versioned multi-source claim/Worker/ACK prerequisites plus resume commands.
- Final environment checks: Docker14 existing services Up, own disposable container absent; no running test process in VPS dedicated root; isolated loopback PG preview schemas0. Synthetic artifacts/evidence retained. Windows directory durability UNKNOWN, physical power loss/real ENOSPC/ECU/X270 NOT RUN; old Windows RLC1 and local symlink limits retained. No original auto-repair/deletion, production service/DB change or history rewrite.

## Phase I-1 — multi-source Agent-local contract v2
- New candidate contract docs/interfaces/rlc2_integration_v2.md distinguishes logical session/manifest/run from physical source UUID/frame sequence/highwater. Wire API remains v1. Dedicated RLI2 revision1 SQLite schema has shared preview tables plus canonical session/run binding and explicit child-source admissions.
- Existing product v1 schema/migrations/ACK untouched. Closed legacy claim/TSV/journal cursor/historical run inventory rejects conflicts without writes. Live old/new Worker coexistence BLOCKED; producers/legacy importers/manifest/ledger must remain quiescent through commit. No production migration or new-path ACK.
- Agent schema13 Windows x64 PASS with transactional migration/rerun/rollback and product DB byte preservation. Cross-platform CI running; engine implementation follows next phase.

## Phase I-1–I-7 — local candidate implementation and actual HTTP verification
- Agent PR52–58 provide versioned isolated RLI2 schema, admitted multi-source atomic ingestion, canonical session/run binding, per-source cursor/receipt preservation, mandatory quiescence/snapshot change detection, strict SQLite schema/integrity checking, independent Supervisor axes, actual loopback HTTP and one-command validation. Existing Server runtime/schema/migrations, product Worker and persistent Agent ACK paths unchanged.
- I-3 RED d08860d reproduced stale commit after source/ledger update; snapshot detection now rejects it. I-4 RED0a27d0d reproduced malformed ACK-column acceptance; authoritative schema checks added. I-6 RED15f04f3 closes SQL whitespace token collision, preserving actual pre-I v0 compatibility. No automatic repair/adoption.
- Local focused proof: Windows integration24 (CLI expansion pending final28), snapshot15, strict schema35, child-JVM faults20, diagnostics36 and actual Server regression57 PASS. Actual Zulu8 prior integration24/snapshot15 PASS; final full x64/x86/VPS batch running.
- Actual Uvicorn/FastAPI over owned loopback sockets and invocation-owned PG schema passed34 HTTP checks: profile/batch persisted, one run across3sources, same-batch duplicates,409/422/reference errors, real committed-response drop then idempotent resend, actual PG transaction failure, unavailable DB endpoint503, unchanged Agent candidate ACK bytes. Latest migration mirror also uses BIGINT for SQLite signed64, with2^40 probe pending batch.
- User changed validation policy after Actions reported no jobs could start because of payment/spending-limit restrictions (suspected free quota). Local Windows/actualx86/VPS/isolated DB verification plus review are the merge basis. Actions are NOT RUN; no CI-success claim or billing-setting change. Supplementary CI definitions remain available for later rerun.
- Live source ingestion / old-Worker coexistence / production migration / formal new-path ACK remain BLOCKED. Windows directory durability UNKNOWN; physical power loss, real ENOSPC, shared PG service stop, ECU/X270 NOT RUN. HTTP DB-unavailability test uses a reserved non-listening owned loopback port without stopping the shared test cluster.
- Final evidence and exact resume: Agent docs/handoff/codex_product_integration_report.md and append-only codex_product_integration_worklog.md (publication after full matrix and merges).

## Phase I final local verification / Agent merges — 2026-10-18 22:09 JST

- Agent PR52–58 all normally merged, final code main aa55dcd007b48728a320448fb827049254fcb6fd (tested source tree be086297f758133d13632e1a54acd274459b0a39). Existing src/main/.../product/v1 Worker/sender/schema code is unchanged. Server runtime/migrations are also unchanged; this Server PR contains documentation only.
- Full Windows batch build/acceleration-20261018-214753.log exit0: actual JDK17x64 and Zulu8x86, new schema13/engine28/snapshot15/strictschema35/JVM21 each, diagnostics37, preview43/fault44/defaultload32 each. Direct PG preview twice and actual HTTP35 also executed. Server regression57 PASS after explicit migrations twice/check.
- Fresh VPS Linux whole product/journal/native-POSIX/ledger/rotation/diagnostics/candidate suite exit0. New schema13/engine28/snapshot15/strictschema35/JVM20, diagnostics36, preview42/fault43/defaultload31. Large10000+10 small sessions:10100records/10111receipts/22admissions/11bindings, Linux59 and actualx8660 PASS; exact replay/bytes/ACK constraints. Single cold candidate snapshot+project+commit1656ms Linux/10448ms x86, observational only.
- Latest actual HTTP35 PASS on shared disposable test cluster using an invocation-owned schema. A second fresh owned PostgreSQL16.15 cluster also passed the same35 checks including actual immediate process stop -> HTTP503/noACK -> restart and preserved4records. Existing test cluster was never stopped. Initial own-cluster harness pipe/connection-timeout failures and their fixes remain in Agent worklog; no failed run is counted as success.
- Latest input/output/CLI and strict-schema source was reviewed; actual v0 DDL compatibility preserved. Actions jobs could not start (account limit/payment annotation); user explicitly chose local/VPS verification, so no CI PASS is claimed. YAML/PowerShell parsing PASS. Final environment:14existing Docker services Up, no own test process on VPS, no preview/HTTP schemas in shared test PG, all3invocation-owned PG clusters stopped and shared55432ready.
- Remaining gates: live Writer/legacy-Worker coexistence and production v1 migration BLOCKED; formal new-path ACK/auto-send disabled; directory durability UNKNOWN; physical power loss/realENOSPC/ECU/X270/oldWindowsRLC1full56/local privileged symlink/rootSelfTest-with-missingRomRaider.jar NOT RUN. Final report provides exact resume and supplementary Actions rerun instructions.

## 2026-10-19 — Phase II Agent cooperative ownership candidate

Agent PR60–68 normally merged; final implementation main `ca9cfe06d774261be05dd5253b8c90f6cf994f3d`, tested source head `82e1d54da767a545027ecbf82f6fd361d29a2a77`. [Environment bootstrap](https://github.com/zawa356/RomRaider_agent/blob/main/docs/ops/development_environment_bootstrap.md), [final report](https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/codex_phase2_report.md), [contract](https://github.com/zawa356/RomRaider_agent/blob/main/docs/interfaces/lane_ownership_v1.md).

- Retained RLLO1 logical Lane/owner UUID/generation and exact legacy Worker lock; opt-in product TSV/Journal/spool scopes, RLC2 cooperative API and final precommit owner validation. Different physical Sources remain explicitly admitted under one logical run, with existing IDs/ACK preserved.
- Synthetic Writer/Reader publication boundary orders publish/seal/rotation/Manifest/Ledger and snapshot→commit; no noncooperative live or cross-DB atomicity claim. Same configured local ownership root is mandatory; no timed lease/PID takeover.
- Copy-only RMI1 v1 inventory migration/preflight preserves rows/rowids/record IDs/ACK/cursors/profile/delivery/review and original bytes. Atomic DDL rollback, real JVM halt/owned-target recovery, strict schema/trigger/inventory replay; no production apply or automatic downgrade/RLI2 record conversion.
- Windows11 NTFS JDK17x64/actual Zulu8x86/Linux17 focused ownership26, migration19, publication6, cooperative child faults21, actual separate Engine competition7 PASS; product cross-DB/real Worker refusal and completed retry PASS. Full Windows batch `acceleration-20261019-095142.log` exit0. Linux broad journal/product/ledger/rotation/diagnostics/preview regressions PASS. Cooperative10k/11-session load actualx8660/Linux59 PASS (10100records/10111receipts/22admissions/11bindings). Read-only advisory status and manual recovery runbook added.
- Real owned Uvicorn/FastAPI/PostgreSQL HTTP35 PASS including409/422, committed response loss/retry, DB failure and owned PG immediate-stop/restart503/noACK. Agent bytes/ACK unchanged. Server current regression migration-upgrade twice/check and pytest57 PASS,1warning (`server-pytest-20261019-094046.log`). Server runtime/API/migrations are unchanged by this PR.
- Latest Agent Actions39182473844 payment/spending-limit annotation: all jobs steps=[]; **CI NOT RUN (runner not started)**. No billing changes or redispatch; authorized local/VPS verification and review are merge basis.
- Gates retained: production migration, old unknown importers/noncooperative Writers/restored parallel roots and live ECU/Logger integration are not enabled; new formal ACK/auto-send disabled. Windows directory durability UNKNOWN; physical power loss/realENOSPC/X270/ECU NOT RUN. Root test.sh missing RomRaider.jar, local privileged symlinks and old Windows RLC1 full56 remain NOT RUN/BLOCKED. Existing Docker14 Up, existing PG55432ready, own PG stopped, no remaining VPS test JVM.

## 2026-10-19 Phase III Agent配置・切替診断・隔離copy受入

Agent [PR70](https://github.com/zawa356/RomRaider_agent/pull/70)/[71](https://github.com/zawa356/RomRaider_agent/pull/71)/[72](https://github.com/zawa356/RomRaider_agent/pull/72)を取込済み、追加 [PR73](https://github.com/zawa356/RomRaider_agent/pull/73) は 通常merge済み（2026-10-19T14:56:03+09:00）。Agent実装main `c206282119c424c3dd15c66b5cddfb5713d69fac`、最終コード検証head `ed8efd6e6195418feffe77224ef61f2116a6db7b`。

- RLDB1はpaired root/旧DB anchorとcanonical identity/ACL/owner/single-hardlink検査を持つ固定Session用の合成候補。read-only deployment/cutover/copy-state CLIとRLI2 bound entry、RLBA1 inactive copied-target受入、RMI1 schema-reference cleanupと全旧表/rowid/ACK/receipt/claim/cursor/実retry/review状態保全を実装。
- 同一DB別root、target DB alias、recovery WAL alias（別DBを変更し得たRED）をwritable open前に拒否。RMI1の6境界子JVM halt、SQLite busy/source変更、partial backup/full rehearsalを受入。SQL COMMITとWAL/checkpoint完了を混同しない。
- 今回のServer独立実行: 専用loopback PostgreSQL16.15でupgrade二度/check成功、pytest57 passed/1 warning。Agent候補の実FastAPI/owned PG HTTP35 PASS、試験ACKでAgent bytes/ACK不変。既存PG/稼働サービスを停止していない。Server runtime/schema/wire v1は変更しない。
- Windows17 x64/actual Zulu8 x86/Linux17検証と証跡は [Agent Phase III報告](https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/codex_phase3_report.md) / [証跡](https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/phase3_validation_evidence.md)。CIは最新job steps=[]、account payment/spending limitでrunner未開始のCI NOT RUN。課金変更・再dispatchなし。
- **未成立:** RLDB1 manifest置換/次Session/復元rebind authority、完全なprocess/distribution provenance、clone/別host/networkFS global fencing、RMI1→RLI2 physical receipt/record mappingと本番cutover/rollback。固定配置とlow-level multi-session loadを同じ受入としない。Windows directory durability UNKNOWN。実車/X270/OpenPort/ECU、物理電源断/実ENOSPC、正式ACK/本番migration/自動Worker切替はNOT RUN/無効。

次回は [Bootstrap](https://github.com/zawa356/RomRaider_agent/blob/main/docs/ops/development_environment_bootstrap.md) → Phase III報告 → 両repo最新main/PR/進捗から再開する。本節はServer製品機能の追加や本番受入を意味しない。

## 2026-10-19 Phase IV Agent独立レビュー・versioned rebind・provenance・旧v1分類（Server変更なし）

- Agent側では、stacked PR [#75](https://github.com/zawa356/RomRaider_agent/pull/75)→[#76](https://github.com/zawa356/RomRaider_agent/pull/76)→[#77](https://github.com/zawa356/RomRaider_agent/pull/77)→[#78](https://github.com/zawa356/RomRaider_agent/pull/78)→IV-5 で、独立レビューの修正（Windows RLDB1 identityのHigh欠陥ほか）、RLDT1/RLDB2のversioned transition、RLAP1のprovenance、RLPC1の旧v1分類と隔離stagingを追加した。すべて合成専用のopt-in候補。2026-10-19、ユーザーの承認を受けてAgent mainへmergeした（#75 `2e6825c`、#76 `d95950c`、#77 `a76b35c`、#78 `dca2f4d`、#79 `4f80c5e`）。
- Server側の変更は、この文書だけ。runtime・schema・wire v1・migrationは変更していない。Agentが新たに導入した記録（RLDT1/RLDB2/RLAP1/RLPC1/RLLV1）はAgent内部のものであり、Serverの正式ACKや受信APIには接続していない。
- Server main `bb27cd1` を、専用のloopbackテストDBで再検証した。migration upgradeの2回実行とcheckがexit0、pytest 57 passed（warning 1件）。
- 詳細は [Agent Phase IV報告](https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/phase4_report.md) と [証跡](https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/phase4_validation_evidence.md) を参照。CI NOT RUN（runner未起動）。
- 未成立は変わらない: global fencing、本番cutover、正式ACK、原本のない旧v1 recordのRLI2移行、Windows directory durability（UNKNOWN）、実車。

## 2026-10-19 — Phase V Agent provenance/staging hardening (Server runtime unchanged)

Agent [PR80](https://github.com/zawa356/RomRaider_agent/pull/80), implementation `b4b909cc3111c11e58f35b7600e47bea1d6aadfa`, fixes UUID-only journal-cursor provenance, asymmetric duplicate-source handling and incomplete Vault/RLI2 verification. It compares full cursor owner/path/RLC1 payload chain/metadata, retained v1 JSON/canonical fields and actual physical RLC2 source identity; freezes projections; independently verifies all typed Vault columns/schema and all8 exact RLI2 table sets. Historical ACKed NULL bodies remain valid; missing unACKed bodies remain UNKNOWN. Dedicated private staging files are published without overwriting final targets; partial attempts and competitor bytes are preserved. New-path ACK/sending remains disabled.

Server base/runtime head is `d8c7a2f3b96ba278d269074dc40cca7741b4155b`; this progress update changes no Server runtime, migrations, schema or wire contract. Independent dedicated test-DB upgrade twice/check exited0, pytest57 passed/1warning. Actual FastAPI/invocation-owned PG HTTP35 also passed (stop503/noACK/restart, dropped committed response/retry, unchanged Agent ACK bytes). Exact Agent platform/head/log evidence is in the [Phase V report](https://github.com/zawa356/RomRaider_agent/blob/phase5/provenance-hardening/docs/handoff/phase5_report.md) and [validation evidence](https://github.com/zawa356/RomRaider_agent/blob/phase5/provenance-hardening/docs/handoff/phase5_validation_evidence.md).

At final implementation head, focused61 cases pass on Windows JDK17x64 and actual Zulu8x86 (JVM32). Final Linux/full Windows/owned HTTP/load results will be synchronized below after completion; pending results are not PASS. Agent #79 and Server #61 were already merged before Phase V and required no base adjustment. Phase V PRs stay unmerged: latest Actions failures have zero steps (CI NOT RUN), and the supplied Phase V policy prohibits merge without executed CI. No redispatch/billing changes.

Remaining gates include F3 mapped-network-drive detection, old-binary exclusion, extra Transition/SQLite lock/path fault fixtures, global fencing, Windows process/directory provenance/durability UNKNOWN, physical power loss/realENOSPC and production/real-car acceptance. Full v1 inventory remains in RMI1/unchanged v1; RLLV1 is experimental record evidence, not a complete database backup or approved product storage version.

Final implementation b4b909c Linux61 focused cases, Phase III/IV, full candidate/schema/snapshot/JVM regression, exact10000 staging and10000+10sessions load all pass. Final-head actual x86 staging10000 and owned HTTP35 pass. A frozen exact-head Windows full x64/x86 batch is still running; its outcome will be appended after completion. Current focused/platform results do not imply product/production acceptance.

Agent final entry-guard head `928d43fb96452b4e4f989352d8627549c1e23a4d` adds exactly one early dedicated RLI2 final-name check to broad baseline b4b909c. A valid-source RED demonstrated acceptance of product.db before this guard. Final focused62 cases pass on Windows17x64, real Zulu8x86(JVM32), Linux17. Broad/load/HTTP results remain explicitly at b4b909c; no cross-head relabelling. Server runtime still d8c7a2f and unchanged.

Final broad Windows acceptance at b4b909c completed exit0: full JDK17x64/actual Zulu8x86 batch,2533 PASS lines (Phase III/IV/product/spool/ingress/SQLite/preview/integration/ownership/copy/native plus focused61 per architecture). Log SHA256769fac249566bf33d38bfdddeef4f91fe325ca2e71d7164b44c7f94e2cd11504. Final guard928d43f focused62×Windows64/actual32/Linux remains separate evidence; no cross-head PASS claim. Optional direct PostgreSQL preview was not enabled in the batch; actual owned HTTP35/Server57 were separately verified. Shared55432 remained ready, own HTTP cluster stopped. CI remains unexecuted, so Agent80/Server62 remain unmerged under the current instructions. P1/P2 gaps are explicit in the Agent report/followups; no production/ACK enabling.
## 2026-10-20 — Phase VI Agent安全候補（Server runtime変更なし、未マージ）

Agentは既存の未マージ[PR80](https://github.com/zawa356/RomRaider_agent/pull/80)のhead7da38372044792cde5271932a6134b7c6f156ccbを基準に、[81](https://github.com/zawa356/RomRaider_agent/pull/81)→[82](https://github.com/zawa356/RomRaider_agent/pull/82)→[83](https://github.com/zawa356/RomRaider_agent/pull/83)→[84](https://github.com/zawa356/RomRaider_agent/pull/84)→[85](https://github.com/zawa356/RomRaider_agent/pull/85)をstackした。最終runtime/tests固定headはd3941031af4d22c7317055c6d9439cf10e75e364。すべてdefault-off/synthetic-only、未マージ。本Server文書も既存#62のブランチを基準にstackし、重複反映やmainの巻戻しはしない。

- 実子JVMで再現したvault-onlyの後発journal見落とし、旧Lane保持中のabandon、出力親差替え後の競合内部DBへの書込みを修正。旧DBの独立snapshot、abandon時の新旧Lane/Publication保持観測、staging親/workのnative物理ID再確認を追加した。
- Windows配置ではFSアクセス前にGetDriveTypeW/QueryDosDeviceWでFixed/localを確認。Remote/Unknown/subst/timeout/不明出力は拒否する。実SMBはNOT RUNで、mountや未知共有へのアクセスはしていない。
- offline preflightはJAR順序/hash、Java/bitness、世代/manifest/admission、既存lockをread-onlyで検査する。Writer不在はWRITER_UNPROVEN、Windows process/directory durabilityはUNKNOWNで、launch_authorized/production_authorized/ack_eligibleはfalse。正常launcher・旧binaryの普遍的排除・完全な製品readinessはPartialであり、実装済みとしない。
- 前段の固定headでWriter161チェックはWindows17x64/実Zulu8x86/Linux17、drive37チェックとpreflight41チェックはWindows17x64/実x86で成功。最終d394103のWindows全体batch・Linux/loadは実行中で、前段PASSとは区別する。Linux初回はfixture lockの権限をUNSAFE_ACCESSで拒否し、失敗を保全したうえでprivate fixture生成条件を明示して同じコードを再検証中。
- 今回のServer再検証はhead056958dd1973106173e0e9b4c8664324c001ad8a（runtimeはmain d8c7a2f3b96ba278d269074dc40cca7741b4155bと同一）で、専用隔離PG55432のmigration upgrade二度/check exit0、pytest57 passed/1warning。事前にreadyを確認し、既存test serviceのstart/stop/restartはしていない。runtime/schema/wire/migration/Sender接続は変更しない。

正本はmainではなく[Phase VI branch Bootstrap](https://github.com/zawa356/RomRaider_agent/blob/phase6/staging-parent-identity/docs/ops/development_environment_bootstrap.md)→[報告](https://github.com/zawa356/RomRaider_agent/blob/phase6/staging-parent-identity/docs/handoff/phase6_overnight_report.md)→[固定head検証証跡](https://github.com/zawa356/RomRaider_agent/blob/phase6/staging-parent-identity/docs/handoff/phase6_overnight_evidence.md)。最新完了/失敗/再開点をそこで確認する。CIはrunner未開始のNOT RUNであり、本セッションではAgent/Serverの全PR（既存#80/#62を含む）をマージしない。正式ACK・実車・本番移行・自動Sender・既存Worker/サービス操作は無効。
### Phase VI 最終入口差分は53f18a2、広域基準はd394103

追加[Agent PR86](https://github.com/zawa356/RomRaider_agent/pull/86)で、RLDT1 planのchain読取りとcommitのlock作成より前にdrive proofを行う。最終runtime/testsは53f18a27663c0f7f9c8f2398fd3390190f5f5749、d394103の広域検証とは区別する。最新の[Bootstrap](https://github.com/zawa356/RomRaider_agent/blob/phase6/transition-drive-preflight/docs/ops/development_environment_bootstrap.md)→[報告](https://github.com/zawa356/RomRaider_agent/blob/phase6/transition-drive-preflight/docs/handoff/phase6_overnight_report.md)→[証跡](https://github.com/zawa356/RomRaider_agent/blob/phase6/transition-drive-preflight/docs/handoff/phase6_overnight_evidence.md)はPR86のbranchを正本とする。Server runtimeは引き続き変更なし。全PR未マージ、起動/本番/正式ACKは無効。
### Phase VI 最終検証完了 — 2026-10-20

- 最終runtime/tests53f18a2はWindows JDK17x64／実Zulu1.8.0_504 x86（model32 assert）でdrive37・入口順序6・preflight41・transition59＋子lock補助・Phase IV回帰がすべてexit0。Linux17でもPhase VI/III/IV/Vがexit0。正常launcher・Windows process真正性・非協調Writer不在の証明は実装済みとせず、launch/production/ACKはfalseのまま。
- **別headの広域基準d394103**は、Windows全体x64/x86 batchがexit0、3181 PASS行、約60.37分。log SHA256a52a1a9aa70be4b78d16e8ea0052d4a891bce05d9374d014ce69fdc92f16aa43。実x86 staging10000records/10001receiptsもexit0。Linuxは11sessions/10100records/10111receipts/11bindings/22admissions、staging10000、bound10003が成功。最終差分の全広域PASSと読み替えない。
- 実FastAPI/invocation-owned PG HTTP35はd394103 fixtureで成功。自前clusterのimmediate-stop→503/noACK→restart→最終stopを実行し、Agent bytes/ACK不変。既存55432を停止していない。Server runtimeはd8c7a2fと同一、migration二度/check0、pytest57 passed/1warning。Serverの変更はこの進捗文書のみ。
- Windowsの25世代連続publish進行はreplacement拒否でBLOCKED（旧/staged/原本bytes保全、repairなし）。これは全面的な進行保証ではない。true symbolic link権限試験、実SMB、physical power loss、real ENOSPC、実車はNOT RUN。新規専用fixtureのWindows junctionは実行成功。Windows directory durabilityはUNKNOWN、global fencingと完全な旧binary排除は未成立。
- 全Agent/Server PRは未マージ。CIはsteps0のrunner未開始、NOT RUN。billing/dispatch/mergeなし。実測に基づくCI最大時間だけsingle-OS60分／full Windows90分へ変更（構文確認のみ、CI PASSではない）。詳細なhead・失敗・log hash・再開点は最新[Agent証跡](https://github.com/zawa356/RomRaider_agent/blob/phase6/transition-drive-preflight/docs/handoff/phase6_overnight_evidence.md)に集約する。

## 2026-10-20 — Phase VII Agent単一offline candidate入口（Server runtime変更なし、未マージ）

- Agent PR86→[87](https://github.com/zawa356/RomRaider_agent/pull/87)→[88](https://github.com/zawa356/RomRaider_agent/pull/88)→[89](https://github.com/zawa356/RomRaider_agent/pull/89)→[90](https://github.com/zawa356/RomRaider_agent/pull/90)→[91](https://github.com/zawa356/RomRaider_agent/pull/91)、全てdraft・未マージ。最終product runtime 67657d9、最終tests d93a975。
- 独立レビュー（Claude Code）でF1を再現：preflightが承認していた`Rlc2IntegrationCli`は、実子JVMがLane/Publication lockを保持中でも候補DBへ書込めた。新`OfflineCandidateEntry`（RLOE1）のみを承認入口にし、RLOP1起動profile（main class・JAR順序/hash・Java実行体/x86-x64・user・作業dir・owner/data root）、RLSO1所有marker（DB open前に物理identity照合）、supervisorが起動する単一子JVM（`ingestBoundActive`経由のみ書込み）を必須化。diagnoseは常時BLOCKED、production liveは常時拒否。
- 統合readiness RLIR1（15軸、status/code/next）を追加。ただし別reviewセッションがVII-C2（v1 record 0件でclaims/cursorsがあるとcursor PASS扱い）を再現しており、修正は別branchで進行中。
- 合成owned E2E：複数Source保存→再起動0件→rotation→RLDT1でSource明示admission→再pin→子JVM強制kill（commit前・atomic）→再試行→readiness。**実FastAPI/Uvicorn＋invocation-owned PG16で35 checks**（応答喪失/再送、409/422/503、自前PG immediate stop/restart）、Agent候補bytes不変、既存55432は停止せず。Server test ACKはAgent ACKではない。
- Windows JDK17 x64／実Zulu8 x86／Linux17でPhase VII全suite exit0（d93a975）。Phase VI/V/IV回帰はWindows x64・Linuxで67657d9 exit0。Server runtimeはd8c7a2fのまま、pytest57/migrationはPhase VIIで再実行していない。
- 非協調Writer不在はWRITER_UNPROVEN（sidecarなしBEGIN IMMEDIATE/EXCLUSIVEで再現）、Windows process provenance/directory durabilityはUNKNOWN、旧Worker/Sender/CLIは未fence。CIはsteps0でNOT RUN。正本は[Phase VII報告](https://github.com/zawa356/RomRaider_agent/blob/phase7/adversarial/docs/handoff/phase7_report.md)／[証跡](https://github.com/zawa356/RomRaider_agent/blob/phase7/adversarial/docs/handoff/phase7_validation_evidence.md)。

## 2026-10-21 — Phase VIII/IX Agent進捗（Server runtime変更なし、未マージ）

- Agent stack: PR92（Phase VIIレビューclosure）→93（RLDI1 inventory）→94（RLIR1 readiness CLI）→95（RLMS1 10セッション）→96（副main分離）→[97](https://github.com/zawa356/RomRaider_agent/pull/97)→[98](https://github.com/zawa356/RomRaider_agent/pull/98)→[99](https://github.com/zawa356/RomRaider_agent/pull/99)→[100](https://github.com/zawa356/RomRaider_agent/pull/100)。全てdraft・未マージ。CIはjobs steps=0でNOT RUN。
- Phase IX-1（#97）：#96の4 CLIがどのscriptでもbuildされずドキュメント記載の起動が`ClassNotFoundException`になる点を再現し、別tool JARの明示build＋実子JVM試験で修正。x64 multisession初回`CreateProcess error=267`は、%TEMP%配下の空`work`ディレクトリが外部清掃で一括削除されたことと整合（実行者はROOT_CAUSE_NOT_PROVEN）。entryは`WORKING_DIRECTORY_MISSING`で子起動前に拒否。
- Phase IX-2/3（#98/#99）：Windows製品Reader候補RLWR1（JNA、同一handleからidentity/長さ/bytes、fail-closed codes）を合成実装し、x64と実Zulu8 x86で試験。entryの新reader値`WINDOWS_NATIVE_V1_SYNTHETIC`で合成ownedのみ接続（test JARなし、JNA hash固定）。**採用はBLOCKED**：FILE_SHARE_DELETE、JNA配布ライセンス、最小Windows版はowner判断待ち。
- Phase IX-4（#100）：RLDI1で同size/同mtimeのbytes差替え・物理差替えがMATCHEDになる欠陥を再現（RED）し、identity＋hash再検証で修正。新発見F-IX-1：entry自身の必須依存JAR（sqlite-jdbc、JNA）がmain/Manifest Main-Class/multi-release classを含むため、実配布ディレクトリはRLDI1 MATCHEDにならない（緩和せずowner/設計判断）。
- 原本・ACK・Server wire/schemaは不変。production/launch/ACKは無効、WRITER_UNPROVEN、Windows provenance/durability/ACLはUNKNOWN、global old-binary exclusionはNOT_PROVEN。Server pytest/migrationはこの期間に再実行していない（Server変更なし）。正本：[Phase IX report](https://github.com/zawa356/RomRaider_agent/blob/phase9/distribution-hardening/docs/handoff/phase9_report.md)。
