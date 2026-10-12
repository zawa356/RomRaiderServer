# RomLogger 文書一覧・正本管理

**最初に読む:** [システム要件定義書 v1.0.0](system_requirements.md) → [システム基本設計書](basic_design.md) → [Server–Agent通信契約v1](interfaces/server_agent_wire_v1.md)。

| 文書 | 文書ID | 責務と位置付け |
| --- | --- | --- |
| [システム要件定義](system_requirements.md) | RLG-SRS | **承認済み v1.0.0**。製品が何を満たすかの正本 |
| [システム基本設計](basic_design.md) | RLG-BD | 主要構成、責務、処理、開発順序 |
| [論理データ設計](logical_data_model.md) | RLG-LDM | 車両・端末・走行・サンプル・タスク・解析の論理関係 |
| [Server–Agent IF 概要](interfaces/server_agent.md) | RLG-IF-SA | IF-001〜007の責務・接続面と背景 |
| [Server–Agent 通信契約v1](interfaces/server_agent_wire_v1.md) | RLG-IF-SA-WIRE | **具体的なAPI形式・ACK・ID・エラーの製品v1設計** |\n| [Agent API OpenAPI 3.1](interfaces/agent_api_v1.openapi.json) | RLG-IF-SA-WIRE（機械可読） | Server側のモック・検証・実装向けAPIスキーマ |
| [MCPインターフェース](interfaces/mcp.md) | RLG-IF-MCP | ツール一覧、行列指定検索、認証、計画操作 |
| [安全・技術検証計画](safety_validation.md) | RLG-SAFETY-VAL | 実車操作のガード、復旧、段階的なVAL試験 |
| [要件トレーサビリティ](requirements_traceability.md) | RLG-TRACE | SRS全119件の設計先・検証観点への対応 |

## 状態を誤認しないために

- RLG-SRS v1.0.0はユーザー承認済みの**要件定義**。その他は**製品向け設計文書**であって実装済みや実機検証済みを意味しない。
- 製品の通信設計v1は、旧PoCの[RomRaider_agent/docs/10_interfaces.md](https://github.com/zawa356/RomRaider_agent/blob/main/docs/10_interfaces.md)とは**独立した世代**。PoCと混在接続できると仮定しない。
- [RomRaiderServer/docs/control_protocol_poc.md](control_protocol_poc.md)、[docs/requirements.md](requirements.md)は旧PoCの実装経緯。製品版SRSに優先しない。
- Serverの正本をAgentリポジトリに複製せず、Agent側の設計やREADMEからリンクする。Agent固有の内部実装資料はAgentリポジトリで保持する。
- 未決・技術検証依存は基本設計末尾、安全検証計画および通信契約の留保事項で管理。設計方針の承認で実車安全制限を解除しない。

## 設計の優先順位

1. 製品要件の正本：RLG-SRS。
2. 主要アーキテクチャと責務：RLG-BD／RLG-LDM。
3. サーバーと車載の接続に関する具体契約：RLG-IF-SA-WIRE（同じ領域で概要書と異なる場合、具体仕様を優先）。
4. ChatGPT等とServerの接続：RLG-IF-MCP。
5. 安全上の実行判断：RLG-SAFETY-VAL（実機検証が終わるまで保守的に適用）。
6. 実装段階の詳細設計・コード：上記規約に従う。変更時は関連文書・テストを同時更新する。

## 開発順序（BD-008）

1. 文書・接続規約と検証条件の整備
2. Server受信・PostgreSQL原本保存・保存確定ACK（合成データ）
3. RRBridge／spool／転送（既存Java Agent再利用を優先）
4. 実ECU → RomRaider → RRBridge → Server実測データの確認
5. MCP読み取り系・ChatGPT接続確認
6. Supervisor・承認・AI計画・安全なプロファイル管理
7. 高度監視・解析履歴・未解決事項の継続管理

## 変更時の最低限のチェック

- SRSの個別要件に対応する設計章があるか。
- ID・版・データ定義・時刻・ACK・再送・重複の契約がServer/Agentで一致するか。
- 実車の未検証操作を「実証済み」と書いていないか。
- 本番MCPが実車情報や車載操作を匿名公開しないか。
- 合成データと実ECUデータを混同していないか。
- **アプリコード変更なしの設計更新であること**をGit差分で確認する。
