# RomLogger 設計ドキュメント体系

**2026-10-14 夜間作業の結果・再開点:** [Agent夜間報告](https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/codex_overnight_report.md)、[Agent worklog](https://github.com/zawa356/RomRaider_agent/blob/main/docs/handoff/codex_overnight_worklog.md)。Windows watermark BLOCKEDのためPhase 4b-2d-2b-3結合は未実装。

**最新のCodex夜間開発・再開指示書:** [2026-10-13 Codex引継ぎ（安全ゲート・CloudPC・実装Phase・作業ログ）](handoff/2026-10-13_codex_overnight.md)。[旧チャット移行引継ぎ](handoff/2026-10-13_chat_handoff.md)は過去の基準点。最新実装状態は[実装進捗・変更履歴](implementation_progress.md)とGitHub main/PR/CIを優先。

| 項目 | 内容 |
| --- | --- |
| 設計基準 | **RomLogger製品設計ベースライン v1.0（2026-10-12）** |
| 要件正本 | [RLG-SRS v1.0.0](system_requirements.md)（2026-10-12ユーザー承認済み） |
| 設計範囲 | 基本設計・Server/Agent/MCP/DB詳細設計・外部IF契約・運用・テスト |
| 実装状態 | **設計文書のみ。製品コード変更・実ECU試験の実施を意味しない** |

このフォルダが**RomLogger製品全体の設計文書正本**。車載側`RomRaider_agent`リポジトリからはリンクで参照し、別の製品設計正本を作らない。

## 1. 読む順番

| 順序 | 文書 | 役割 |
| --- | --- | --- |
| 1 | [RLG-SRS 要件定義](system_requirements.md) | 何を／なぜ／どこまで実現するか（承認済み） |
| 2 | [RLG-BD システム基本設計](basic_design.md) | 構成・責務・処理フロー・開発順 |
| 3 | [RLG-ADR 設計判断台帳](design_decisions.md) | 合意済み／委任判断／技術検証待ちの明確化 |
| 4 | [RLG-LDM 論理データ設計](logical_data_model.md) | 車両・走行・Run・Segment・Task・原本の関連 |
| 5 | [RLG-IF-SA Server–Agent IF概要](interfaces/server_agent.md) | IF-001〜007の責務 |
| 6 | [RLG-IF-SA-WIRE 通信契約v1](interfaces/server_agent_wire_v1.md) | **HTTPS/JSON、UUID、バッチ原子的ACK、端末認証・再送・操作** |
| 7 | [Agent API v1 OpenAPI 3.1](interfaces/agent_api_v1.openapi.json) | 通信契約の機械可読なAPI・スキーマ |
| 8 | [RLG-IF-MCP MCPインターフェース](interfaces/mcp.md) | AIからのツールと生データへのアクセス |
| 9 | [MCP Query v1 JSON Schema](interfaces/telemetry_query_v1.schema.json) | 行・列・条件検索の入力／出力の機械可読な定義 |

## 2. 詳細設計・品質資料

| 文書 | 内容 |
| --- | --- |
| [DD-SRV Server詳細設計](server_detailed_design.md) | Python/FastAPI候補、レイヤー、原子的受信、タスク／操作、監視・検索 |
| [DD-DB PostgreSQL物理設計](database_detailed_design.md) | JSONB原本＋検索用値、キー・制約、取り込み順・cursor整合、DDL参考 |
| [DD-AGENT Windows車載詳細設計](agent_detailed_design.md) | RRBridge再利用、SQLite spool候補、Uploader、Supervisor・安全ゲート |
| [DD-MCP MCP・AI解析詳細設計](mcp_detailed_design.md) | OAuth設計、ツール検索意味論、Plan・監視DSL・解析履歴 |
| [DD-OPS 配備・運用詳細設計](operations_detailed_design.md) | Docker/Windows構成、初期設定、診断、更新、ライセンス |
| [DD-TEST 契約・実機・受入テスト計画](test_acceptance_plan.md) | 段階受入・合成/実ECU/Live区分・リリース阻止条件 |
| [RLG-SAFETY-VAL 車載安全・検証方針](safety_validation.md) | 段階的な実車安全ゲート、復帰、既存PoCの安全制限維持 |
| [RLG-TRACE 要件ID対応](requirements_traceability.md) | **FR 101件、NFR 12件、VAL 6件、計119件**の設計対応・検証観点 |

## 3. 仕様間の優先順位と齟齬時の対処

1. 要件定義：RLG-SRSを最優先。**要件自体を設計の都合で変更しない**。
2. 構成・責務：RLG-BD、論理データ：RLG-LDM。
3. 通信形式と保存保証：**RLG-IF-SA-WIRE と対応OpenAPI**。IF-SA概要はその意図の説明。
4. AI／MCP契約：RLG-IF-MCPと詳細設計、Query JSON Schema。
5. 車載の最終安全：RLG-SAFETY-VALとAgent詳細設計。**車載実機で未証明の許可条件は適用しない**。
6. 実装言語、クラス／テーブル物理名、設定閾値などは詳細設計の基準。実装試験により改訂可能だが外部契約・要件の意味を損なわない。

**矛盾発見時は、暗黙に都合のよい仕様を選ばず、どの文書が正本かを判定し、関連文書とテストをまとめて改訂**する。AIが文書の更新を代行する場合も、設計と検証実績を混同しない。

## 4. PoCと製品版の関係

- [RomRaider_agent/docs/10_interfaces.md](https://github.com/zawa356/RomRaider_agent/blob/main/docs/10_interfaces.md)は**動作中のPoCの接続規約**。製品向けServer–Agent v1とは別世代で自動互換はない。
- [Server側PoC制御規約](control_protocol_poc.md)と[旧PoC要件](requirements.md)も現行PoCの検証資料。製品SRSには優先しない。
- 既存RRBridge Java Agentは**再利用第一候補**。コード・API・PoCの暫定閾値を盲目的に製品へ取り込まない。
- 製品版コードの実装開始時には**設計契約v1で動く新Server**と、旧PoCが混在しないよう版・接続先・配布物を区別する。
- PoCに存在する車載の停車ガード・無害なコマンド許可リストを、製品設計文書が完成した理由だけで解除しない。

## 5. 設計完成と未検証の区別

**設計ベースライン v1.0 完成**は、主要な設計判断・IF契約・DB原本・車載保全・MCP検索・運用・試験の仕様がドキュメントで揃ったことを意味する。以下は設計作業の外部にある検証条件として引き続き管理する。

- Java Agentが実ECUサンプルをRomRaider内部から継続取得できるか。
- 独立した走行安全入力と、走行中のプロファイル切替の負荷・安全性。
- ChatGPT通常／Liveで利用できる**実際の**認証・ツール発見・書込み機能。
- Windows spoolの電源断耐性、実測取得周波数／転送遅延・検索性能。
- RomRaider等のライセンス、公開・再配布条件。

これらは[設計判断台帳](design_decisions.md)のTV-01〜10として記録。実装工程での検証まで「未確認」と表記する。

## 6. 開発順序

**設計文書整備 → Server受信・PostgreSQL → RRBridge／車載spool → 実ECU全経路 → MCP参照 → Supervisor・安全なAI計画 → 継続監視・解析履歴 → 条件付き走行中切替の実機検証**。

各段階の受入条件は[DD-TEST](test_acceptance_plan.md)を正本とする。ServerとAgentを独立更新する場合は両者の通信v1契約に従う。

## 7. 更新履歴

| 日付 | 内容 |
| --- | --- |
| 2026-10-12 | 基本設計・IF・データ・安全・要件追跡の初稿を作成 |
| 2026-10-12 | 委任された技術判断によりServer・DB・Agent・MCP・運用・テスト詳細設計を追加し、設計ベースラインv1.0に整理 |\n| 2026-10-13 | MCPで既知サンプルから前後の観測をまとめて取得するanchor検索を追加。is_presentによる未計測行の除外も定義 |
