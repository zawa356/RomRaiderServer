# Server–Agent通信契約 v1 設計確定案

| 項目 | 内容 |
| --- | --- |
| 文書ID | RLG-IF-SA-WIRE |
| 仕様版 | **protocol v1**（本書の設計選択。現行PoCとの互換性なし） |
| 文書版 | 0.2.0 / 2026-10-12 |
| 状態 | **設計案・実装／実機検証前**。ユーザーから文書の技術判断を委任されている |
| 親文書 | [外部IF設計](server_agent.md) / [論理データ設計](../logical_data_model.md) / [要件定義](../system_requirements.md) |\n| 機械可読API定義 | [OpenAPI 3.1 JSON](agent_api_v1.openapi.json) |

本書の「必須」「MUST」は**製品版を実装するときの契約**を表す。対応するJSONリクエスト・レスポンス構造の機械可読な定義は[OpenAPI v1](agent_api_v1.openapi.json)を参照する。意味上の保証（ACK・再送・順序・安全）は本書を正本とする。現行PoCに実装済みであることを意味しない。実装中に変更した場合は契約版と試験を更新する。

## 1. 決定事項

| 項目 | v1の決定 |
| --- | --- |
| 転送 | TLS上のHTTP/1.1以上、UTF-8 JSON、要求応答型 |
| 主体 | 車載側が発信し、Serverへ認証。Serverから車載への直接着信は不要 |
| スプール | ネットワーク送信より前に再起動耐性のあるローカル永続化 |
| ACK | **1バッチ＝1トランザクション。全件commit時のみ全件ACK** |
| 配送保証 | at-least-once。AgentはACK未確定レコードを消さない |
| 冪等 | 原本の不変record_id。既存IDの同一内容は重複扱い、異なる内容は409 |
| データ型 | 観測値はJSON numberの有限数。NaN/Infや不正値は、品質異常イベントとして別に記録 |
| 定義 | プロファイル／パラメーター定義は版付き不変スナップショットを先行登録 |
| 欠落 | 取得順序・Gapイベント・品質状態を独立管理。到着順を取得順とみなさない |
| 転送優先 | 直近データと古い未ACKデータを双方処理し、飢餓を防止 |
| 容量不足 | 未ACK自動破棄禁止。容量逼迫・記録失敗は運用イベントとして明示 |
| 操作 | 非同期、期限／計画版／承認範囲／実車安全判定、重複実行回避 |
| 認証 | **端末ごとのランダムなBearerトークン（初版）**。Server側でハッシュ保存／失効／更新。MCP認証とは別 |
| URI版管理 | `/api/agent/v1/`をプレフィックス。非互換変更はv2へ |
| 専用キャッシュ | 初版必須ではない。PostgreSQL正本から最新値提供 |

追加の外部LLM API、追加のメッセージブローカー、時系列DB、常時WebSocketは初版必須としない。

## 2. 共通規約

### 2.1 HTTPと認証

- 通信: HTTPS。自宅／検証時のloopbackのみHTTPを許す。証明書検証無効化で本番運用しない。
- 各リクエスト `Authorization: Bearer <device-token>`、`Content-Type: application/json`、`Accept: application/json`。
- Serverはトークンからdevice_idを特定し、本文のdevice_id、vehicle_idの割当を照合する。本文の自己申告IDのみでは認証しない。
- Server側で端末トークンを発行／無効化／ローテーション可能とし、ソースやログへの平文露出禁止。初版の個人セルフホスト向けには複雑なPKIを追加しない。
- 接続はAgentから開始。コマンド取得もAgentからのポーリングとする。監視・ログの周期は詳細設計で調整可能。

### 2.2 識別子と順序

| 項目 | v1ルール |
| --- | --- |
| device_id, vehicle_id | Serverの発行するUUID文字列。資格情報・関連づけで検証 |
| run_id, segment_id | 車載で発行するUUIDv4文字列。再起動・複数デバイスで衝突しない |
| profile_revision_id | 車載で発行するUUIDv4。**内容不変**の定義スナップショット識別 |
| record_id | 車載で発行するUUIDv4。spoolに記録後も変えず、再送でも維持 |
| batch_id | **送信ごと**に発行するUUIDv4。異なるバッチ構成は新ID（同一batch_idの再試行では本文を変えない） |
| command_id | Serverが発行するUUIDv4。再配送時に同じID |
| sequence | run内の取得イベント通番（0以上の非負整数）。同一run内で単調増加し、再起動で別runになる |
| timestamp | ISO 8601 / RFC 3339 のUTC時刻文字列、ミリ秒以上の精度（例 `2026-10-12T10:00:01.234Z`） |

IDは仕様上UUID文字列であり、その具体的生成ライブラリは問わない。イベントとサンプルの通番は区別できること。複数値のサンプルを「ECU内で同時刻測定した」とはみなさない。実ECU由来と合成試験由来は `source_kind` で区別する。車載時計とサーバー時計の差は計測品質として扱い、サーバー保存時刻で観測時刻を置き換えない。

### 2.3 共通応答エラー

失敗応答は原則として以下の構造。必須: `error.code`, `error.message`, `error.retryable`, `request_id`。秘密情報、スタックトレース、SQL、ファイルパスを本文に出さない。

```json
{
  "request_id": "ef1c7e33-3b85-4d42-9408-fd64fa19de01",
  "error": {
    "code": "UNKNOWN_PROFILE_REVISION",
    "message": "Referenced profile revision has not been registered",
    "retryable": false,
    "details": {"profile_revision_id": "d97b4da0-6074-4ca2-a078-39ac7f928a85"}
  }
}
```

| HTTP | 意味 | Agent方針 |
| --- | --- | --- |
| 200/201 | 当該IFの**成功本文**の意味を確認する | ACKは `committed` と一致を確認したときのみ確定 |
| 400/422 | スキーマまたは意味検証失敗 | 保持・診断。無限同一再試行せず問題レコード特定 |
| 401/403 | 認証・権限不正 | 保持。再登録／資格情報更新まで自動連打を抑制 |
| 404 | 参照対象なし | 未登録定義／操作ID等を確認して再同期 |
| 409 | ID衝突、版競合、前提不一致 | 既存原本保全。原因を確認するまで誤上書き禁止 |
| 413 | バッチ過大 | 同一record_idを保持し、**新batch_idで小分け**して再送 |
| 426 | サポートしないプロトコル版 | 計測・ローカル保全継続。非互換操作を停止 |
| 429/503 | 制限・一時利用不可 | Retry-Afterがあれば尊重、バックオフ |
| 500系・ネットワーク断 | 保存成否不明 | ACK未確定として再送。Server側冪等処理 |

詳細なエラー文字列の増減は可能でも、コードの意味はv1内で安定させる。未知のエラーコードは安全側に保留する。

## 3. プロファイル定義の登録（IF-001の前提）

`PUT /api/agent/v1/profile-revisions/{profile_revision_id}`

- 本文必須: `protocol_version`（整数=1）、`device_id`、`vehicle_id`、`profile_revision_id`、`logger_definition_fingerprint`、`parameters`（配列）。
- パラメーターの要素必須: `parameter_id`、`name`、`unit`。同一profile_revisionで同一parameter_idは不可。追加定義（換算ID・由来・可用性）は後方互換拡張とする。
- `logger_definition_fingerprint` は設定元定義を区別する識別情報。実装方式（ファイルハッシュ等）はAgent内部設計で決める。
- 同一ID・同一正規化内容なら200 `{"status":"already_registered","profile_revision_id":"..."}`、新規なら201 `{"status":"registered","profile_revision_id":"..."}`。
- 同一ID・異なる内容は409 `PROFILE_REVISION_CONFLICT`。記録を変更しない。
- 定義情報は元の版のまま保持し、後のECU／Logger定義の更新で過去データの解釈を変えない。
- 定義が受信できない期間でも**車載側の取得・spool保存を止めない**。関連サンプルは未ACK保管し、定義の登録後に転送する。

説明用リクエスト（IDは例示）:

```json
{
  "protocol_version": 1,
  "device_id": "278065da-9a67-4cd4-9e4a-b01597da56b7",
  "vehicle_id": "6f58c2f3-b65d-40a1-8e54-f5eff9b02c23",
  "profile_revision_id": "d97b4da0-6074-4ca2-a078-39ac7f928a85",
  "logger_definition_fingerprint": "logger-v-example-1",
  "parameters": [
    {"parameter_id": "P8", "name": "Engine Speed", "unit": "rpm"},
    {"parameter_id": "P13", "name": "Throttle Opening Angle", "unit": "%"}
  ]
}
```

## 4. 計測原本の受信とACK（IF-001/002）

`POST /api/agent/v1/telemetry/batches`

### 4.1 バッチ要求

| 属性 | 型 | 必須 | 意味 |
| --- | --- | --- | --- |
| protocol_version | integer | ○ | 1 |
| batch_id | UUID | ○ | 要求単位のID |
| device_id / vehicle_id | UUID | ○ | 認証済み割当との照合 |
| run_id | UUID | ○ | ロガー取得実行 |
| records | array | ○ | 1件以上の観測／イベントレコード |
| record.kind | enum | ○ | `observation`, `event`, `gap` |
| record.record_id | UUID | ○ | 変化しない原本ID |
| record.segment_id | UUID | ○ | 計測区間識別 |
| record.captured_at | RFC3339 | ○ | 車載観測／発生時刻 |
| record.source_kind | enum | ○ | `ecu` または `synthetic` |
| record.sequence | integer | 観測のみ | run内の取得順、非負 |
| record.profile_revision_id | UUID | 観測のみ | 先行登録済み定義 |
| record.values | array | 観測のみ | `parameter_id`、`value`を持つ要素、同一IDは重複不可 |
| record.event_type | string | event/gapのみ | `logging_start` 等の分類 |
| record.data | object | event/gapのみ | イベント固有の構造化情報。秘密情報を含めない |

観測の `values[].value` は**有限のJSON number**。null／NaN／Infinityや文字列の数値変換を許さない。該当値が未取得ならその値要素を含めず、必要に応じ品質イベントで理由を表現する。0や直近値で補完しない。値の集合が空の観測は保存できず422。記録した順と適用セグメントの整合は検証する。

バッチは1つのrunに属する。複数runのレコードは別バッチへ分ける。record_idは**イベント・gapにも必須**とし、それらも冪等化する。Serverはrunが未登録の場合、認証済みdevice/vehicleと初回サンプルに基づきrunの論理記録を作成可能。走行セッションの境界は別の推定処理で管理する。

説明用リクエスト:

```json
{
  "protocol_version": 1,
  "batch_id": "1c3a92cd-d7c5-4708-aea1-a0a36c8bc4be",
  "device_id": "278065da-9a67-4cd4-9e4a-b01597da56b7",
  "vehicle_id": "6f58c2f3-b65d-40a1-8e54-f5eff9b02c23",
  "run_id": "7ea6c054-1197-4cb6-9439-ee48275646c3",
  "records": [
    {
      "kind": "observation",
      "record_id": "6bdac9f6-d60c-4ee4-afc5-7819dab71fe3",
      "segment_id": "27904521-fd3a-43e6-86de-4a76b89dfa0c",
      "sequence": 501,
      "captured_at": "2026-10-12T10:00:01.234Z",
      "source_kind": "ecu",
      "profile_revision_id": "d97b4da0-6074-4ca2-a078-39ac7f928a85",
      "values": [
        {"parameter_id": "P8", "value": 2840.0},
        {"parameter_id": "P13", "value": 18.4}
      ]
    }
  ]
}
```

### 4.2 永続化トランザクション

Serverはバッチのすべてについて次を確認してから**1 DB transaction**内で確定する。

1. スキーマ、認証主体、割当車両、数量上限を検証。
2. 参照した `profile_revision_id` が永続登録済みで、値のパラメーターIDがその定義集合に属することを検証。
3. `record_id` と取得実行／区間／時刻／値を既存と比較。同一ならduplicate、異なるなら衝突として全体を拒否。
4. **同一run_id + observation.sequence** が別record_idですでに登録済みである場合も衝突として全体拒否（取得順誤り防止）。
5. バッチ内・DB内の全整合条件を満たしたときにのみ保存・commit。
6. commit完了後にのみ `status=committed` を返す。DBロールバック・commit成否不明で成功ACKは禁止。

**部分成功／不正レコード読み飛ばし＋全件ACKは禁止**。データの一意性判定は再送時に内容が変化しないことを前提にし、JSONのキー順・空白など表現上の差ではなく**論理内容の一致**で比較する。監査のため正規化内容または内容ハッシュを保持する。実装で採用する正規化アルゴリズムと単位換算の扱いは詳細設計で固定する。

### 4.3 正常応答

HTTP 200のみ。必須: `status="committed"`、`batch_id`、`record_count`、`inserted_count`、`duplicate_count`。

```json
{
  "status": "committed",
  "batch_id": "1c3a92cd-d7c5-4708-aea1-a0a36c8bc4be",
  "record_count": 1,
  "inserted_count": 1,
  "duplicate_count": 0
}
```

Agentは、応答のbatch_idが送信したものと一致し、`record_count == records.length`、`inserted_count + duplicate_count == record_count`、`status=="committed"`であることを確認し、**確認済みレコードID集合**だけをローカルでACK確定する。上記いずれかが不一致なら未ACKとして扱う。単純なファイル送信位置のみで確認状態を表す設計は不可（再送と最新優先転送で送信順が前後するため）。

バッチ全体のvalidation失敗はHTTP 422（全レコード未ACK）。同一ID・異なる内容は409（全レコード未ACK）。失敗時の `details` は問題のrecord_id等を含めて診断可能とする。

Agentは422で同じバッチを永久再送せず、**エラーのrecord_idを特定して分離し、正常レコードを新batch_idで再送する**。不正レコードは別の永続隔離領域に保護したままエラーとして報告する。送信失敗だけで削除しない。分離前のバッチは不可分であり、分割後はrecord_idと内容を変えない。

### 4.4 欠番・未着

Serverは連続したsequenceを前提に到着を待たず、欠番は「未着」とする。後着で解消できる。車載でspool書込失敗・ロガー取得停滞などが確定した場合は、event/gapレコードで範囲と原因を報告する。sequenceが欠けた事実だけで、データ消失確定と判断しない。

## 5. スプールの抽象契約

これはファイル形式やDB選択を強制しない。

- Agentは観測を取得したら**できる限り短時間で永続spoolへ記録し、転送処理とは分離**する。
- 不変record_id、取得順序、run_id、segment_id、profile_revision_idを永続記録。
- 取得コールバックから永続化の間にメモリキュー等を用いる場合、**キューあふれ・電源断・書込失敗によるドロップを観測可能にする**。完全無損失の誤保証をしない。
- 再起動後、未ACKレコード・ACK済み判定・不正隔離レコードを復旧可能。ACK状態自身の更新が電源断で巻戻っても再送で安全（冪等）。
- 転送スケジューラは最新レコード用の機会と過去回収用の機会をともに確保。古いデータを永久に残したり、新しいデータを長時間後回しにしない。
- 空き容量に応じ警告し、未ACKの自動期限削除なし。書き込み不能時はログと品質イベントを残し、自動的に取得を止める等の安全側対処を検討。
- ACK済み原本は容量回収できるが、未確定と確認済みの状態がクラッシュ後も混同されないこと。

## 6. 状態・能力・操作（IF-003〜006）

### IF-003 状態報告

`POST /api/agent/v1/status`

必須: protocol_version, device_id, vehicle_id, reported_at, agent_version, logger_state (`not_started|starting|logging|stopped|error|unknown`), acquisition (`last_observed_at` nullable, `recent_hz` nullable, `drop_count`非負整数), spool (`unacked_records`, `pending_bytes`非負整数)。任意: `run_id`, `segment_id`, `profile_revision_id`, `ecu_state`, `link_error_count`。Serverが受信時刻を別に保持し、古い報告を無条件に最新へ上書きしない。HTTP 200 `{"status":"recorded","server_received_at":"..."}`。

### IF-004 能力情報

`PUT /api/agent/v1/capability-snapshots/{snapshot_id}`

device_id, vehicle_id, logger_version, definition_fingerprint, ecu_identity（分かる場合）, observed_at, parameters（ID・名称・単位・`availability`: `defined|possibly_supported|verified_readable|unsupported|unknown`、根拠）を保存。スナップショットは不変。同じsnapshot_idの異なる内容は409。Serverは古いスナップショットを現在の対応状況と断定しない。パラメーターの「verified_readable」は実ECUの観測履歴等の確認根拠を要する。

### IF-005 操作要求取得

`POST /api/agent/v1/commands/claim`

車載が `device_id`、`vehicle_id`、`current_plan_revision_id`（nullable）、`client_state_revision`（実状態の単調改訂識別）を報告し、Serverは有効期限・対象・認可範囲を検証済みの要求を0件または1件返す。要求には必須: `command_id`、`action`（v1は明示的な許可リストのみ）、`task_id`、`plan_revision_id`、`approval_scope_id`、`issued_at`、`expires_at`、`expected_profile_revision_id`（nullable）。返却時点で車載実行成功とみなさない。重複claimは同一command_idを返し得る。

**Server側の配送リース期限**と**操作自体のexpires_at**を区別する。リース期限後に再配送されても、車載側の記録と実状態照合で二重実行させない。

### IF-006 結果／再同期

`POST /api/agent/v1/commands/{command_id}/report` と `POST /api/agent/v1/reconcile`

Agentは各操作に `command_id`、`report_id`（UUID・冪等ID）、`state`、`observed_profile_revision_id`（nullable）、`result_reason`（nullable）、`reported_at` を報告。状態候補: `received|rejected|applying|applied_unverified|verified|failed|expired|cancelled|unknown`。実行前に期限・版・安全条件・ユーザー介入を再確認し、`verified`のみ計測品質まで確認した成功。

再接続・再起動時のreconcileはローカル操作履歴・適用プロファイル実状態・run_id・最後に確認したcommand_id／計画版を提示し、Serverの期待状態と照合。結果不明のコマンドは**新しい操作として自動再実行せず**、安全側の判定に回す。ローカルユーザー介入と安全停止はServerから復帰を強制できない。

## 7. 運用・互換・制限値

- v1の既知フィールドを削除または意味変更しない。追加フィールドは後方互換なoptionalのみ。未知のkind/action・列挙値は安全に拒否し、黙って既知の意味へ読み替えない。
- TLS、端末資格情報、権限が満たされない場合はAgentの**ローカル記録**のみを継続する。
- 初期のバッチ送信は **128レコード以下かつ256KiB以下**を設計初期値として採用する。Serverは最大512KiBの本文受入れを目安とし、超過は413。実際の設定値は両側で整合して変更可能。これらは**設計上の設定初期値**であってK-Lineの性能保証ではない。
- 状態報告の初期間隔は10秒を目安とし、取得品質監視の10秒窓とは独立する。実際の更新頻度・鮮度判定は性能評価により調整可能。
- バッチの送信時刻とDB保存遅延は監視する。正常通信時P95 2秒以内は**検証用の暫定目標**であり、承認済みSRSの普遍的な性能保証ではない。
- Agent側のHTTPクライアントは接続・読み取りのタイムアウトと指数バックオフ、サーバーのRetry-Afterを利用。具体値は詳細設計・運用設定の対象。

## 8. 契約試験（Serverを先行実装できる条件）

| ID | シナリオ | 合格条件 |
| --- | --- | --- |
| CT-01 | 定義の登録と取得バッチの新規保存 | DBコミット後のみcommitted返却 |
| CT-02 | 同じ本文・record_idで再送 | duplicate、原本1件 |
| CT-03 | 同じrecord_idで値だけ変更 | 409、旧原本維持、バッチ全体保存なし |
| CT-04 | 同一run＋sequenceで別record_id | 409、全体ロールバック |
| CT-05 | DB commit前失敗・commit後ACK断 | 未ACK再送で最終的に原本1件 |
| CT-06 | バッチ内の1件が不正 | 422、他のレコードもcommitしない |
| CT-07 | 422後に問題レコードを隔離、残り再送 | 正常分が失われず進む、隔離分を削除しない |
| CT-08 | 定義未登録で観測を送信 | 422、未ACKのまま、定義登録後に再送成功 |
| CT-09 | 古い未ACK大量＋最新観測 | 最新転送と古い回収が双方進行 |
| CT-10 | 偽device_id、別vehicle_id、トークン失効 | 401/403で保存・操作不能 |
| CT-11 | 合成とECU由来を混在 | 適切に区別して検索可能 |
| CT-12 | 旧版・期限・競合・重複command | 車載操作を二重実行しない |
| CT-13 | Agent再起動・spool復旧 | 未ACK・record_id不変、確認済みの二重登録なし |
| CT-14 | 異常な時刻・到着順逆転 | 原本の取得順は保持、未着を即欠落確定しない |
| CT-15 | Server/Agentの異なる対応版 | 非互換操作拒否、Agentのローカル計測継続 |

## 9. 詳細設計・技術検証への留保

HTTP契約の基本的意味論とURIをv1設計選択として置いたが、**実運用確認・実ECUとの適合は未検証**。以下は実装前／実装中に記録して確認する。

1. JSONパース／正規化の正確性、浮動小数点の元表現の扱い、非有限値の障害イベント表現。
2. 大量蓄積時のspool ACK台帳・部分隔離とWindowsプロセス強制終了時の耐久性。
3. 定義フィンガープリントの取得方法、RomRaiderが通知する観測の粒度。
4. Serverが実行可能な安全な数値条件表現と認可条件の厳密なモデル。
5. 資格情報の初回登録手順、TLS証明書展開、複数端末・車両の切替。
6. 実ECUテストの結果（合成自己試験を実車検証扱いしない）。
7. 公開・配布するコード／ライブラリのライセンス確認。

## 改訂履歴

| 日付 | 版 | 内容 |
| --- | --- | --- |
| 2026-10-12 | 0.2.0 | 委任を受け、通信の初版設計選択を具体化。HTTP/JSON、原子的バッチACK、UUID、定義先行同期、初版トークン認証、誤ACK防止と結合試験を明文化 |
