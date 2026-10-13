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
| 2.1-D2a | 最新増分Agentの実Server E2E再pin／未完結行・再起動・重複再送 | **実装・CI検証中** | [Server PR #24](https://github.com/zawa356/RomRaiderServer/pull/24)／[Agent PR #9](https://github.com/zawa356/RomRaider_agent/pull/9) |
| 2.1-D2b | データ欠損対策・安全な常駐送信／バックオフ | 未着手 | [Agent進捗](https://github.com/zawa356/RomRaider_agent/blob/main/docs/product_v1_implementation_progress.md) |
| 2.1-D3 | X270 Zulu8 32-bit／電源断／disk-full／実車耐久 | 未着手 | [Issue #7](https://github.com/zawa356/RomRaiderServer/issues/7) |
| 3 | 実ECU全経路の停車試験 | 未着手 | [Issue #8](https://github.com/zawa356/RomRaiderServer/issues/8) |
| 4 | 本番MCP認証、生データ検索・anchor | 未着手 | [Issue #9](https://github.com/zawa356/RomRaiderServer/issues/9) |
| 5–6 | 安全Supervisor・数値監視・解析履歴 | 未着手 | [Issue #10](https://github.com/zawa356/RomRaiderServer/issues/10) |

## 変更履歴

### 2026-10-13 — Phase 2.1-D2a：最新増分Agentを実Server E2Eへ再pin（CI検証中）

- [Agent PR #9](https://github.com/zawa356/RomRaider_agent/pull/9)をmainへ統合。実Server E2Eに使用するJavaテストを旧TSV全量2観測から、新しい`IncrementalTsvBridge`の**定義1行ごとの取込・複数回再起動・未完結LF行・追記3観測**へ更新
- Server [PR #24](https://github.com/zawa356/RomRaiderServer/pull/24)でAgent main **`668ad5230e7e3db4fc592311c857906f43802ad3`** のJavaソース・実E2Eスクリプトを7ファイルのGit blob SHA照合付きテスト専用スナップショットへ更新。原本SHAと各コピーSHAを実際に照合
- CIで実FastAPIと使い捨てPostgreSQL 16へProfile登録→3観測のバッチ送信→全件ACK→**別SQLiteから同じ元TSVを2/2/1行で再取込して重複だけのACK**を検証。DB上の観測3件、Profile1件、`synthetic`属性を照合
- **試験結果はCI完了後に記載する。** この段階はAgentとServerにまたがるCI専用ソースの更新。Agentの車載RuntimeやECU操作には触れない
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
