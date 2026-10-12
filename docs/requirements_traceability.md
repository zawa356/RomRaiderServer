# 要件・基本設計トレーサビリティ表

| 項目 | 内容 |
| --- | --- |
| 文書ID | RLG-TRACE |
| 版 | 0.1.0 / 2026-10-12 |
| 対象要件 | [RLG-SRS v1.0.0](system_requirements.md) |
| 状態 | **設計上の対応関係のみ。実装済み・検証済みとは判定しない** |

## 1. 判定ルール

- 「設計上の対応」＝当該基本設計の章に、要件を満たすための方針・責務・契約を記載したこと。
- 「検証観点」＝開発時に確認する対象。**検証実施済みの意味ではない**。
- 既存PoCの実績があっても、それを製品実装済みとして流用判定しない。
- SRS v1.0.0の要件は変更しない。実装の段階順序はSRSの必須・目標の区分を変更しない。
- 以下は全件**設計マッピング済み／製品版実装・検証は未確認**として管理する。個別の技術的未解決項目は[基本設計§12](basic_design.md)と[安全検証計画](safety_validation.md)へ記載する。

## 2. ID単位の対応表

| 要件ID | SRS要求の要旨 | 設計上の参照先 | 検証観点 |
| --- | --- | --- | --- |
| FR-OPS-001 | Windowsクライアントは通常のRomRaider手動利用モードとAI／サーバー連携モードを選んで起動できること。 | basic_design.md §3; safety_validation.md §2 | Windows起動確認 |
| FR-OPS-002 | モードの選択は起動時に行い、運用中の動的切替は要求しない（切替には再起動してよい）。 | basic_design.md §3; safety_validation.md §2 | Windows起動確認 |
| FR-OPS-003 | AI連携モードでは、計測開始・継続・プロファイル管理を連携機構が管理し、通常運用で利用者の同時手動変更を想定しない。競合・外部変更を検知したら安全側に扱うこと。 | basic_design.md §3; safety_validation.md §2 | Windows起動確認 |
| FR-OPS-004 | AI接続やアクティブな計測タスクがなくても、利用可能な状態では基本ロギングを継続すること。 | basic_design.md §3; safety_validation.md §2 | Windows起動確認 |
| FR-OPS-005 | 計測タスク終了後は基本計測に戻り、走行履歴を蓄積し続けられること。 | basic_design.md §3; safety_validation.md §2 | Windows起動確認 |
| FR-OPS-006 | 車載PCで常時GUI操作を必要としないこと。クライアント運用・設定はCLI等の軽量な操作を基本とし、独自GUIを必須にしない。 | basic_design.md §3; safety_validation.md §2 | Windows起動確認 |
| FR-OPS-007 | AIによる自動変更を停止・抑止できる独立した操作手段を持つこと。停止中でも可能な限り既存ログを保全すること。 | basic_design.md §3; safety_validation.md §2 | Windows起動確認 |
| FR-CAP-001 | 車載側でRomRaider／Logger定義から利用候補のパラメーター情報を自動取得できること。 | basic_design.md §6; interfaces/server_agent_wire_v1.md §6 | Logger定義／実ECU |
| FR-CAP-002 | パラメーターID、名称、単位、定義・選択可能性等をサーバーへ自動同期し、AIから参照できること。 | basic_design.md §6; interfaces/server_agent_wire_v1.md §6 | Logger定義／実ECU |
| FR-CAP-003 | 定義・接続先・対応可否の変更を検出して更新できること。 | basic_design.md §6; interfaces/server_agent_wire_v1.md §6 | Logger定義／実ECU |
| FR-CAP-004 | 定義ファイルに存在するだけの項目と、現接続ECUで実際に取得できることが確認された項目を区別できること。 | basic_design.md §6; interfaces/server_agent_wire_v1.md §6 | Logger定義／実ECU |
| FR-CAP-005 | AIが未定義・未対応のパラメーターを想像でプロファイルに混入させても適用されないこと。 | basic_design.md §6; interfaces/server_agent_wire_v1.md §6 | Logger定義／実ECU |
| FR-CAP-006 | 車両・ECUの情報は可能な限り自動識別し、手動設定は自動判別できない項目やサーバー接続・認証等の最小限にすること。 | basic_design.md §6; interfaces/server_agent_wire_v1.md §6 | Logger定義／実ECU |
| FR-CAP-007 | 初期のBP5専用値・PC固有パス等を一般製品の必須設定として固定しないこと。 | basic_design.md §6; interfaces/server_agent_wire_v1.md §6 | Logger定義／実ECU |
| FR-PLAN-001 | 利用者は自然言語で計測目的を指示でき、AIが具体的なパラメーター選択や計測計画へ落とし込めること。 | basic_design.md §6; interfaces/mcp.md §§3,6 | タスク／計画結合 |
| FR-PLAN-002 | AIは利用可能なパラメーター定義・過去ログ・品質情報を参照し、適合する計測プロファイルを生成・提案できること。 | basic_design.md §6; interfaces/mcp.md §§3,6 | タスク／計画結合 |
| FR-PLAN-003 | 利用者はタスク開始時に目的と許容範囲を包括承認でき、同範囲の個別変更ごとに運転者の再承認を要求しないこと。範囲外は承認を求めること。 | basic_design.md §6; interfaces/mcp.md §§3,6 | タスク／計画結合 |
| FR-PLAN-004 | 包括承認はECU安全条件の免除ではない。AIの指示・承認済み範囲・車載側検証の全条件を満たして初めて操作可能とすること。 | basic_design.md §6; interfaces/mcp.md §§3,6 | タスク／計画結合 |
| FR-PLAN-005 | AIは計測目的と通信帯域・応答速度の実測に応じ、基本項目も含めて取得項目を増減・入替できること。基本パラメーターを固定・必須とはしないこと。 | basic_design.md §6; interfaces/mcp.md §§3,6 | タスク／計画結合 |
| FR-PLAN-006 | 変化が速い信号の時間分解能を原則重視しつつ、相関解析に必要な同時計測と帯域制約のバランスをAIが判断できること。 | basic_design.md §6; interfaces/mcp.md §§3,6 | タスク／計画結合 |
| FR-PLAN-007 | プロファイル適用後は更新周波数・間隔・欠損・ECU通信・転送品質を確認し、必要なら計測計画を再評価できること。 | basic_design.md §6; interfaces/mcp.md §§3,6 | タスク／計画結合 |
| FR-PLAN-008 | AIがユーザーへ案内する内容は、計測目的、主要な結果、次の計測条件等の意味ある節目を中心とし、保存・再送等の内部処理を逐一発話しないこと。 | basic_design.md §6; interfaces/mcp.md §§3,6 | タスク／計画結合 |
| FR-PLAN-009 | AIは不足するデータに対し、市街地・巡航・緩やかな加速等の適切な観測条件を提案できるが、交通法規違反・危険運転を指示せず、運転判断は利用者に委ねること。 | basic_design.md §6; interfaces/mcp.md §§3,6 | タスク／計画結合 |
| FR-PLAN-010 | 数分程度（例: 約5分）の計測後に十分性を評価して次の取得へ進む対話上の流れを目標とする。ただし時刻だけで十分と判断せず、観測条件とデータ品質を考慮すること。 | basic_design.md §6; interfaces/mcp.md §§3,6 | タスク／計画結合 |
| FR-PLAN-011 | ChatGPT Liveからの自発的な定期呼び出し・割り込み音声発話は保証できないため、未検証の自動起動を初版の必須動作としないこと。 | basic_design.md §6; interfaces/mcp.md §§3,6 | タスク／計画結合 |
| FR-PLAN-012 | AIからの計画は検証可能な操作要求として受け付け、受理・保留・適用・拒否・失敗・期限切れの結果を追跡できること。 | basic_design.md §6; interfaces/mcp.md §§3,6 | タスク／計画結合 |
| FR-SAFE-001 | ECU／ROMへの書込み・フラッシュ、ROM読書き、ECUリセット、DTC消去・学習値リセット、アクティブテスト、OpenPort FW変更などを製品機能として提供しないこと。許可操作は計測参照・ロガー記録制御・安全なプロファイル | safety_validation.md §§1–6; basic_design.md §6 | 車載安全・実機 |
| FR-SAFE-002 | 走行中も計測プロファイルの自動変更を行えることを製品の目標動作とする。停止時限定を最終仕様として固定しないこと。 | safety_validation.md §§1–6; basic_design.md §6 | 車載安全・実機 |
| FR-SAFE-003 | 実装上の走行中許可は、実ECU通信・ロガー動作を確認した独立の車載安全条件を満たす操作に限る。確認前にPoCの停車ガードを無条件で解除しないこと。 | safety_validation.md §§1–6; basic_design.md §6 | 車載安全・実機 |
| FR-SAFE-004 | 切替に伴う計測ダウンタイム・欠測は許容する。連続無停止計測は要求しない。一方、切替前に取得済みのデータを消失させないこと。欠測時間は欠測と明示すること。 | safety_validation.md §§1–6; basic_design.md §6 | 車載安全・実機 |
| FR-SAFE-005 | 生成プロファイルは適用前に定義整合性、項目数・通信負荷、操作許可範囲、状態・安全条件を検証すること。 | safety_validation.md §§1–6; basic_design.md §6 | 車載安全・実機 |
| FR-SAFE-006 | AIが選ばなかった項目を使う安全判定は成立したと推定しないこと。必要情報が欠ける場合は当該操作を拒否・保留するか、独立した信頼可能な情報源で判定すること。 | safety_validation.md §§1–6; basic_design.md §6 | 車載安全・実機 |
| FR-SAFE-007 | 旧プロファイルで正常に取得できていたのに、切替後に更新周期・通信品質が有意に悪化した場合、安全に可能なら直前の正常プロファイルへ自動復帰すること。 | safety_validation.md §§1–6; basic_design.md §6 | 車載安全・実機 |
| FR-SAFE-008 | フォールバックが安全に実行できない場合、無制限に再試行せず自動変更を停止し、失敗状態を記録・通知可能にすること。 | safety_validation.md §§1–6; basic_design.md §6 | 車載安全・実機 |
| FR-SAFE-009 | サーバー側でデータ到着停止等を検知した場合、原因確認後にクライアントへ復旧要求を出せること。ただし最終的な適用・拒否は車載側が判断すること。 | safety_validation.md §§1–6; basic_design.md §6 | 車載安全・実機 |
| FR-SAFE-010 | サーバー側の未着と、ECU側の収集停止やインターネット断を区別し、未着のみを根拠にむやみにプロファイルを変えないこと。 | safety_validation.md §§1–6; basic_design.md §6 | 車載安全・実機 |
| FR-SAFE-011 | 過去の操作要求を重複・期限切れ・承認範囲外のまま実行しないこと。実行完了の確認前に成功と報告しないこと。 | safety_validation.md §§1–6; basic_design.md §6 | 車載安全・実機 |
| FR-SAFE-012 | 走行中に画面確認・PC操作を要求せず、運転者への情報提示は簡潔にして注意散漫を避けること。 | safety_validation.md §§1–6; basic_design.md §6 | 車載安全・実機 |
| FR-SAFE-013 | 取得したログや統計から故障を安易に断定しない。計測未成立・疑似データ・欠損・推測の区別を維持すること。 | safety_validation.md §§1–6; basic_design.md §6 | 車載安全・実機 |
| FR-DATA-001 | RomRaider稼働中、CSVの記録状態に依存せず取得可能なテレメトリーを継続収集・サーバー転送できること。 | basic_design.md §5; interfaces/server_agent_wire_v1.md §§2–5 | 契約試験／実ECU |
| FR-DATA-002 | 取得済みの全サンプルを間引き・集約で置き換えず、ロスレスな原本としてサーバーDBへ保存すること。 | basic_design.md §5; interfaces/server_agent_wire_v1.md §§2–5 | 契約試験／実ECU |
| FR-DATA-003 | 元の時刻・サンプル順序・計測パラメーターID・名称・単位・適用プロファイル・区間を追跡可能にすること。 | basic_design.md §5; interfaces/server_agent_wire_v1.md §§2–5 | 契約試験／実ECU |
| FR-DATA-004 | サーバーを長期保存の正本とする。通常運用で保存済み原本を自動期限切れ削除しないこと。 | basic_design.md §5; interfaces/server_agent_wire_v1.md §§2–5 | 契約試験／実ECU |
| FR-DATA-005 | 車載側のローカルバッファ／spoolは転送完了まで保護し、保存完了の確認を受けて送信済みとして扱うこと。無期限の二重保管は必須にしない。 | basic_design.md §5; interfaces/server_agent_wire_v1.md §§2–5 | 契約試験／実ECU |
| FR-DATA-006 | 再送時の冪等性・重複排除・欠番／欠落検知・送信失敗の可視化を提供すること。 | basic_design.md §5; interfaces/server_agent_wire_v1.md §§2–5 | 契約試験／実ECU |
| FR-DATA-007 | 計測区間・プロファイルの変更にまたがって時系列を再構成でき、計測していない期間を実測値として補完したと誤認させないこと。 | basic_design.md §5; interfaces/server_agent_wire_v1.md §§2–5 | 契約試験／実ECU |
| FR-DATA-008 | デバイス・車両を識別でき、複数台のログが混同されないこと。 | basic_design.md §5; interfaces/server_agent_wire_v1.md §§2–5 | 契約試験／実ECU |
| FR-DATA-009 | データの集約・統計・可視化用加工は原本を変更せず別扱いとすること。 | basic_design.md §5; interfaces/server_agent_wire_v1.md §§2–5 | 契約試験／実ECU |
| FR-DATA-010 | 転送・保存の限界でデータ喪失が生じた場合、無かったことにせず欠損・ドロップ件数・原因を確認可能にすること。 | basic_design.md §5; interfaces/server_agent_wire_v1.md §§2–5 | 契約試験／実ECU |
| FR-RES-001 | サーバー停止・回線断・MCP未接続でも車載側は可能な限り計測を継続すること。 | basic_design.md §§5–6; interfaces/server_agent_wire_v1.md §§5–6 | 断線・再起動 |
| FR-RES-002 | 接続断中は直前の正常計測構成を基本的に維持し、AIからの新規計画変更は一時停止すること。 | basic_design.md §§5–6; interfaces/server_agent_wire_v1.md §§5–6 | 断線・再起動 |
| FR-RES-003 | 車載側はサーバーがなくても計測品質を監視し、独立の安全条件に従って局所的なフォールバックができること。 | basic_design.md §§5–6; interfaces/server_agent_wire_v1.md §§5–6 | 断線・再起動 |
| FR-RES-004 | 未送信データを安全に蓄積し、回線復旧後に自動再送してサーバー保存へ追いつけること。 | basic_design.md §§5–6; interfaces/server_agent_wire_v1.md §§5–6 | 断線・再起動 |
| FR-RES-005 | 再送・再接続・再起動後の重複処理、未完了要求、古い命令の誤実行を防止すること。 | basic_design.md §§5–6; interfaces/server_agent_wire_v1.md §§5–6 | 断線・再起動 |
| FR-RES-006 | 再接続後はサーバーと実際のロギング状態を照合し、AIによる計画の続きを再開可能にすること。 | basic_design.md §§5–6; interfaces/server_agent_wire_v1.md §§5–6 | 断線・再起動 |
| FR-RES-007 | 自動復旧・再試行は上限と失敗の可観測性を持ち、永久ループや誤った「復旧成功」を避けること。 | basic_design.md §§5–6; interfaces/server_agent_wire_v1.md §§5–6 | 断線・再起動 |
| FR-RES-008 | サーバーからの操作要求は車載側からのアウトバウンド通信等で受け取れること。車載PCへの公開着信ポートを必須としないこと。 | basic_design.md §§5–6; interfaces/server_agent_wire_v1.md §§5–6 | 断線・再起動 |
| FR-SESSION-001 | 走行セッションは原則として自動で開始・終了・識別できること。 | logical_data_model.md §§2–5 | 走行境界判定 |
| FR-SESSION-002 | 計測タスクは走行セッションと独立した概念とし、1回の走行に複数タスク、1タスクに複数走行を関連付けられること。 | logical_data_model.md §§2–5 | 走行境界判定 |
| FR-SESSION-003 | 計測区間ごとのプロファイル・適用時刻・終了理由・変更契機・結果を追跡できること。 | logical_data_model.md §§2–5 | 走行境界判定 |
| FR-SESSION-004 | 短時間停止・エンジンOFF判定等、セッション境界の自動判定に不確実性がある場合も履歴の整合性を維持すること。 | logical_data_model.md §§2–5 | 走行境界判定 |
| FR-MCP-001 | AI向け共通インターフェースは標準MCPとし、固有のAIサービスやプロンプト実装に依存しないこと。 | interfaces/mcp.md §§1–8 | MCP接続互換 |
| FR-MCP-002 | ChatGPTの通常チャット・Liveを初期の正式検証対象とし、他のMCPクライアントは基本互換を目指す。Claude等の個別音声モード保証は求めない。 | interfaces/mcp.md §§1–8 | MCP接続互換 |
| FR-MCP-003 | MCPから最新状態、セッション、パラメーター一覧、計測品質、期間データ、イベント、過去解析結果を参照できること。 | interfaces/mcp.md §§1–8 | MCP接続互換 |
| FR-MCP-004 | MCP経由で計測計画の提出・要求・結果照会、AI解析結果の登録、監視条件の登録ができること。車載操作の実行判定はMCP／AIの外で行うこと。 | interfaces/mcp.md §§1–8 | MCP接続互換 |
| FR-MCP-005 | MCPを介したサーバーからChatGPTへの自発的なツール実行要求・推論開始・音声発話は保証しない。AIへのプッシュを必須機能として記述しないこと。 | interfaces/mcp.md §§1–8 | MCP接続互換 |
| FR-MCP-006 | 通常チャット・Liveの範囲で利用し、バックグラウンドLLM API定期呼出しや従量課金を必要条件としないこと。 | interfaces/mcp.md §§1–8 | MCP接続互換 |
| FR-MCP-007 | MCPツール呼出しの成功・失敗・操作の実行結果を区別し、操作がサーバーに登録された時点を車載側の完了と混同しないこと。 | interfaces/mcp.md §§1–8 | MCP接続互換 |
| FR-MCP-008 | AIが会話開始時に未読の重要イベントを要求して取得できること。チャットを開いただけで必ず自動検索されるとは保証しない。 | interfaces/mcp.md §§1–8 | MCP接続互換 |
| FR-MCP-009 | 一連の対話中にAIが数分おきの再解析・次計測を自発的に行う運用は目標とするが、MCPクライアント側の再呼出し・発話制約を検証すること。 | interfaces/mcp.md §§1–8 | MCP接続互換 |
| FR-ANL-001 | AIは期間・車両・走行セッション・パラメーターで絞った生の時系列データへアクセスできること。 | interfaces/mcp.md §4; logical_data_model.md §6 | 検索契約／実データ |
| FR-ANL-002 | サーバーは集計・統計・概要・時系列抽出等の補助機能を提供するが、生データへの直接アクセスを妨げないこと。 | interfaces/mcp.md §4; logical_data_model.md §6 | 検索契約／実データ |
| FR-ANL-003 | 長期間・大量の結果は分割・段階取得を可能とし、取得範囲・未取得範囲・切り詰めの有無を明示すること。 | interfaces/mcp.md §4; logical_data_model.md §6 | 検索契約／実データ |
| FR-ANL-004 | 時刻と項目間の相関・応答の順序・瞬間的な変化を解析できる時間情報を保持すること。 | interfaces/mcp.md §4; logical_data_model.md §6 | 検索契約／実データ |
| FR-ANL-005 | 品質指標・欠測・定義変更・同期ずれ・合成試験データの区別をAIが判別できること。 | interfaces/mcp.md §4; logical_data_model.md §6 | 検索契約／実データ |
| FR-ANL-006 | AIは必要なら概要を経由せず生データから直接解析を始められること。 | interfaces/mcp.md §4; logical_data_model.md §6 | 検索契約／実データ |
| FR-ANL-007 | AIの結論は単純集計結果よりも走行条件・比較条件・データの十分性を踏まえた解釈を重視すること。 | interfaces/mcp.md §4; logical_data_model.md §6 | 検索契約／実データ |
| FR-HIST-001 | AIはMCP経由で解析結果・調査目的・計測計画・未解決事項をサーバーへ登録できること。 | interfaces/mcp.md §§3,5; logical_data_model.md §7 | 履歴保存・訂正 |
| FR-HIST-002 | 記録には対象車両・セッション・期間・参照データ・根拠・結論・推測の程度を関連付けられること。 | interfaces/mcp.md §§3,5; logical_data_model.md §7 | 履歴保存・訂正 |
| FR-HIST-003 | 異なるチャットから過去の解析結果・未解決事項を取得し、続きの調査に活用できること。 | interfaces/mcp.md §§3,5; logical_data_model.md §7 | 履歴保存・訂正 |
| FR-HIST-004 | 解析結果は追記型で保持し、訂正・補足・撤回・再評価では元の記録を消さず関係を記録すること。 | interfaces/mcp.md §§3,5; logical_data_model.md §7 | 履歴保存・訂正 |
| FR-HIST-005 | 過去の結論が現在有効か、訂正・撤回済みかを識別できること。 | interfaces/mcp.md §§3,5; logical_data_model.md §7 | 履歴保存・訂正 |
| FR-HIST-006 | AIによる重要結果の自発的な登録は促進するが、クライアントが毎回保存ツールを実行する保証はないことを明示し、登録の成否を確認できること。 | interfaces/mcp.md §§3,5; logical_data_model.md §7 | 履歴保存・訂正 |
| FR-MON-001 | ChatGPT非接続でもサーバーが継続的に数値的監視を行えること。 | basic_design.md §7; interfaces/mcp.md §5 | 監視単体／品質 |
| FR-MON-002 | サンプル到着停止、取得周波数低下、通信エラー、欠損・滞留等の計測品質異常を検知・記録できること。 | basic_design.md §7; interfaces/mcp.md §5 | 監視単体／品質 |
| FR-MON-003 | 車両値の外れ値、急変、持続的な逸脱、過去の計測との変化などを条件付きで検出できること。 | basic_design.md §7; interfaces/mcp.md §5 | 監視単体／品質 |
| FR-MON-004 | 既存の統計・時系列解析手法や実績あるライブラリを調査し優先利用すること。個別アルゴリズムは設計で選ぶ。 | basic_design.md §7; interfaces/mcp.md §5 | 監視単体／品質 |
| FR-MON-005 | 走行状態依存性、センサ特性、単発ノイズ、欠測を考慮し、統計的な異常を故障診断と同一視しないこと。 | basic_design.md §7; interfaces/mcp.md §5 | 監視単体／品質 |
| FR-MON-006 | ChatGPTがMCP経由で監視条件を追加・変更でき、登録後はLLMを呼ばずサーバーで評価できること。 | basic_design.md §7; interfaces/mcp.md §5 | 監視単体／品質 |
| FR-MON-007 | イベントの時刻・重要度・対象条件・根拠データ・確認状態等を記録し、後からMCPで検索できること。 | basic_design.md §7; interfaces/mcp.md §5 | 監視単体／品質 |
| FR-MON-008 | Discord Webhook等への通知は任意拡張とし、採用時は重複抑制・頻度制限・通知不能時の記録を考慮すること。 | basic_design.md §7; interfaces/mcp.md §5 | 監視単体／品質 |
| FR-MON-009 | 通知は車載警報装置や車両安全監視システムの代替ではないことを明確にすること。 | basic_design.md §7; interfaces/mcp.md §5 | 監視単体／品質 |
| FR-SEC-001 | 利用者自身がサーバーを展開・運用できること。複数人向けアカウント・テナント管理を必須としない。 | basic_design.md §8; interfaces/mcp.md §2; interfaces/server_agent_wire_v1.md §2 | 認証／権限試験 |
| FR-SEC-002 | 1サーバーで複数車両・複数車載クライアントを識別して管理できること。 | basic_design.md §8; interfaces/mcp.md §2; interfaces/server_agent_wire_v1.md §2 | 認証／権限試験 |
| FR-SEC-003 | 車載クライアント・MCP接続・管理者の資格情報と権限を区別できること。 | basic_design.md §8; interfaces/mcp.md §2; interfaces/server_agent_wire_v1.md §2 | 認証／権限試験 |
| FR-SEC-004 | ログ参照、解析記録の登録、監視条件の設定、計測操作要求、管理操作は適切に権限を分離すること。 | basic_design.md §8; interfaces/mcp.md §2; interfaces/server_agent_wire_v1.md §2 | 認証／権限試験 |
| FR-SEC-005 | 認証済みの安全な外部通信を前提とし、実車データや実操作を匿名の公開MCPから取得・実行できないこと。 | basic_design.md §8; interfaces/mcp.md §2; interfaces/server_agent_wire_v1.md §2 | 認証／権限試験 |
| FR-SEC-006 | DBをインターネットへ直接公開することを前提としない。任意SQL・OSコマンド・任意ファイル操作をMCP経由で無制限に公開しないこと。 | basic_design.md §8; interfaces/mcp.md §2; interfaces/server_agent_wire_v1.md §2 | 認証／権限試験 |
| FR-SEC-007 | 資格情報の発行・失効・差替えができ、秘密情報をGitHubコミット・ログやサンプル設定に含めないこと。 | basic_design.md §8; interfaces/mcp.md §2; interfaces/server_agent_wire_v1.md §2 | 認証／権限試験 |
| FR-SEC-008 | 認証の具体方式はMCPクライアント（特にChatGPT Live）の実対応を検証して選定する。ユーザー管理のためだけに複雑な認証基盤を自作することは要求しない。 | basic_design.md §8; interfaces/mcp.md §2; interfaces/server_agent_wire_v1.md §2 | 認証／権限試験 |
| FR-SEC-009 | 誰が・どの計測操作を要求し・何が許可／拒否／完了されたかを追跡できること。 | basic_design.md §8; interfaces/mcp.md §2; interfaces/server_agent_wire_v1.md §2 | 認証／権限試験 |
| NFR-001 | 運転中の利用でPC操作を要求しないこと。会話・通知は運転への注意を妨げない内容とする。 | basic_design.md §§1–10; safety_validation.md §7 | NFR検証 |
| NFR-002 | ECU計測レートとサーバー転送レイテンシーを混同せず、更新周波数、間隔の分位値、最新サンプル経過時間、ドロップ、送信失敗等を観測可能とする。 | basic_design.md §§1–10; safety_validation.md §7 | NFR検証 |
| NFR-003 | 項目数・定義長・ECU応答等により品質が変わることを考慮し、固定Hz値や固定項目数を製品全体の普遍的な性能保証にしない。 | basic_design.md §§1–10; safety_validation.md §7 | NFR検証 |
| NFR-004 | データ量に応じた段階取得・上限・ページング等でMCP応答の巨大化やサーバー資源枯渇を防ぎ、AIから必要な生データの全量へ到達可能とする。 | basic_design.md §§1–10; safety_validation.md §7 | NFR検証 |
| NFR-005 | 通信障害を前提に、車載側の計測・保全・安全判定をサーバーへの常時到達性に依存させない。 | basic_design.md §§1–10; safety_validation.md §7 | NFR検証 |
| NFR-006 | デバイス・時刻・セッション・区間・計測定義・操作・解析結果の関連付けを維持し、事後の追跡可能性を担保する。 | basic_design.md §§1–10; safety_validation.md §7 | NFR検証 |
| NFR-007 | サーバーはLinux Dockerによる構築・更新・再配置を可能にし、特定のホスティング事業者への依存を避ける。 | basic_design.md §§1–10; safety_validation.md §7 | NFR検証 |
| NFR-008 | 車載側はWindowsとRomRaiderに対応し、PC固有のパスや車種・ECU定義を固定しない。 | basic_design.md §§1–10; safety_validation.md §7 | NFR検証 |
| NFR-009 | 通常利用の設定項目を可能な限り削減し、自動検出・自動同期を優先する。設定を要する場合は検証可能で分かりやすくする。 | basic_design.md §§1–10; safety_validation.md §7 | NFR検証 |
| NFR-010 | ChatGPT/Claude等の従量課金LLM APIを利用しなくても、常時ログ収集・保存・監視が機能する。 | basic_design.md §§1–10; safety_validation.md §7 | NFR検証 |
| NFR-011 | GitHubで第三者が導入できる程度のドキュメントを整備しつつ、他人向け運用保守や全環境へのサポート提供を約束しない。 | basic_design.md §§1–10; safety_validation.md §7 | NFR検証 |
| NFR-012 | RomRaiderへの組込み・配布に関係するライセンス（GPL等）を公開前に確認し、無許可の第三者バイナリや資格情報を再配布しない。 | basic_design.md §§1–10; safety_validation.md §7 | NFR検証 |
| VAL-001 | 実ECUからのサンプル取得とサーバーDBへの保存を確認する（合成selftestの成功だけでは代用しない）。 | safety_validation.md §§7–8 | VAL表参照 |
| VAL-002 | プロファイル切替前に取得したサンプルが失われず、切替による欠測・区間境界が分かることを確認する。 | safety_validation.md §§7–8 | VAL表参照 |
| VAL-003 | 通信断中に車載側が記録を保持し、再接続後に再送でき、重複・欠番を確認できることを検証する。 | safety_validation.md §§7–8 | VAL表参照 |
| VAL-004 | AIやMCPが許可外のECU操作・任意コマンド・危険なプロファイルを実行できないことを確認する。 | safety_validation.md §§7–8 | VAL表参照 |
| VAL-005 | 走行中の切替は静止状態での実機検証から始め、ECU通信負荷・品質・復旧を評価した範囲でのみ段階的に解禁する。 | safety_validation.md §§7–8 | VAL表参照 |
| VAL-006 | 失敗時・通信断時・再起動後に古い指示を二重実行せず、クライアントの最終安全判定が働くことを確認する。 | safety_validation.md §§7–8 | VAL表参照 |

## 3. 注意すべき境界

- **FR-OPS-003 と BD-003-07:** AI連携モードでの手動介入は自動制御の競合を起こし得る。ローカル操作を優先して自動変更を停止するもので、無制限の併用を保証しない。
- **FR-SESSION-002 と BD-004-01:** 「1走行に複数タスクを紐付け可能」は「同時に複数タスクを実行する」を要求しない。同時実行を原則1件に制限し、時間の重なりはTaskExecutionで識別。
- **FR-DATA-002 と BD-002-05:** 取得後の原本を不要に捨てない。ECU未応答、取得前の障害や物理破損にまで絶対無損失を保証しない。取得→永続spoolの境界でドロップ・失敗を記録。
- **FR-SAFE-002 と FR-SAFE-003:** 走行中切替は目標。安全条件の独立検証までは実装で許可しない。
- **FR-MCP-005/009:** Liveの自発的な再呼出し／発話は保証されず、Serverでの独立した監視と明示的なMCP取得で代替。
- **FR-SEC-005/008:** MCPの本番認証はChatGPT実対応に依存する。匿名で実車データや実操作を公開するという代替案は許されない。
- **NFR-004 とFR-ANL-003:** MCPは1応答を無制限にしないが、ページを辿って原本全件へ到達可能にする。
- **NFR-012:** OSS配布条件は公開前に確認。現時点でライセンス調査完了とは記載しない。

## 4. 実装順序への対応

| 段階 | 中核の対象 | 完了の証拠 |
| --- | --- | --- |
| 1 Server受信基盤 | FR-DATA、FR-RESのServer側、FR-SECのDevice認証 | 合成データで受信・永続化・再送・誤ACK防止 |
| 2 RRBridgeと車載spool | FR-OPSの最小構成、FR-DATA、FR-RES | Windows側耐再起動・未ACK保全 |
| 3 ECU結合 | FR-DATA-001、VAL-001〜003 | ECU実サンプルのServer原本確認 |
| 4 MCP参照 | FR-MCP参照、FR-ANL、FR-SECのMCP認証 | ChatGPT通常／Liveの検証可能な範囲で取得成功 |
| 5 AI計測制御 | FR-CAP、FR-PLAN、FR-SAFE、FR-OPS全体 | 包括承認・安全拒否・旧版拒否・復旧 |
| 6 解析・知見 | FR-MON、FR-HIST | LLMなし数値監視、追記解析と訂正 |

基本設計の完成時と各工程の受入時には、この表の各IDに対する設計・実装・検証の状態を別途更新する。**本表が存在すること自体は、機能達成の証拠ではない。**

## 改訂履歴

| 日付 | 版 | 内容 |
| --- | --- | --- |
| 2026-10-12 | 0.1.0 | RLG-SRSの全FR/NFR/VAL IDを自動抽出し、設計と検証観点へ対応付け |
