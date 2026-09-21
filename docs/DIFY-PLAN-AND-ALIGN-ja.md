# Dify：LLMで計画を作り、前提を比較する

使用ファイル：`examples/dify/sana-plan-and-align.en.yml`。
人間の要求から選択したLLMが計画を生成し、その計画と元の要求をSANAが比較します。
計画・整理結果を返すところまでのワークフローです。

## 1. 取り込みとモデル選択

YAMLを新しいアプリとして取り込みます。共通の接続・認証は [DIFY.md](DIFY.md) を参照します。
`Draft plan — select model` で、Difyに設定済みのチャットモデルを選択してください。
配布ファイルには特定モデルや認証情報を入れていません。
SANAが使用するモデルは、SANA側の`.env`にある別の設定です。

## 2. 人間の要求だけを入力

Human requestに次の文章を入力し、Response languageを`en`にします。

```text
The demo PC is not connected to the internet. Display entirely fictional customer information in the demo. Do not use real customer data.
```

**過去の長いAI計画をHuman requestに貼り付けないでください。**
今回のAI計画はLLMが新しく生成します。Build requestの接続は次の役割です。

| 変数 | 接続元 |
| --- | --- |
| input_message | Inputの人間の要求 |
| ai_interpretation | Draft planの生成テキスト |
| language | Inputの言語指定 |

## 3. mediumで1回実行

配布版には Build request のPythonコード内のpayloadに
`"processing_mode": "medium"` が入っています。
low/highへの変更もこの値で行います。例外時のデフォルト出力に書かないでください。
例外処理は「処理なし」、HTTPの自動再試行は無効です。

計画が空、または要求・計画が各6,000文字を超えた場合は停止します。
制約を消さないよう自動切り詰めは行いません。
挨拶もこのテンプレートでは計画モデルを通るため、単純な接続確認には比較用アプリを使います。

## 4. 実際の計画と判定を照合

返るものは `original_request`、`proposed_plan`、`status`、`result` です。
人間の入力が保持され、SANAに渡した提案と生成計画が一致することを確認します。
計画は毎回変わるので、必ずmappedになることを合格条件にしないでください。
実データを使う案なら、修正必要と判定されることが適切です。

Careに目標・禁止事項が残り、未指定の件数などが局所的な未指定事項として残っているかを確認します。
概要の引用は選択的です。元の計画・Care・unresolvedを併せて読みます。
AI由来の仮定は確認済み能力ではなく、mappedも実行許可ではありません。

## 5. 保存とタイムアウト

生成計画、送信JSON、HTTP応答本文とヘッダー、最終出力を保存します。
実際のモード・モデル呼び出し数・再試行回数・SANA処理時間は、request IDに対応する
サーバートレースで確認します。最終出力だけから推測しません。

HTTPノードのreadは600秒、SANAの標準全体予算は605秒です。さらに計画LLMの処理時間と
プロキシ・ワークフロー側の上限があります。失敗した場合は「実行追跡」で該当ノードを開き、
HTTP応答またはエラーを確認してください。全体の経過秒数だけでは原因を特定できません。
HTTP/JSONエラーを代替のmapped結果に置き換えないでください。

[今回の成功記録と限界](VALIDATION-0.5.15-plan-and-align.md)／
[既知の限界](KNOWN-LIMITATIONS.md)／[モードとログ](PROCESSING-MODES.md)
