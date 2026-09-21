# Dify：入力済みのAI提案を比較する

使用ファイル：`examples/dify/sana-alignment.en.yml`。
人間の要求と、用意済みのAI提案を入力するワークフローです。
Dify側にLLMノードはありません。SANA側は設定済みのモデルを使用します。

## 1. 取り込みと接続

新しいアプリとしてYAMLを取り込みます。接続済みのアプリを更新する場合は、
環境変数・認証・ネットワーク設定を控えてください。
共通のDocker接続・認証手順は [DIFY.md](DIFY.md) にあります。
`SANA_BASE_URL` の初期値は `http://sana-alignment:8000` です。
これは同じDockerネットワークから解決できる場合の値です。

## 2. 入力する内容

| 欄 | 入れるもの |
| --- | --- |
| Human request | 人間の要求文 |
| AI interpretation | 比較したいAI提案の本文。挨拶の接続確認時は空欄 |
| Response language | `en`、`ja`など。初期値は`en` |

最初は Human request に `Hello`、AI interpretation は空欄で実行し、
`handshake` を確認できます。次のテスト時は前の入力を全選択して置き換えます。

制約衝突を確認する例：

Human request:
```text
Show customer information in next week's demo. Do not use real customer data.
```

AI interpretation:
```text
Connect to the production customer database in read-only mode and display a list.
```

期待する判定は `revision_required` です。実データ禁止と本番DB使用の衝突が
引用付きで残っているかを確認してください。

## 3. モードとJSON

配布版は Build request のPythonコード内で、次を送ります。

```python
"processing_mode": "medium",
```

low/highにする場合は、この値を変更します。出力変数や例外時のデフォルト値に
書く設定ではありません。例外処理は「処理なし」とし、失敗した要求を代替値で送らないでください。
`request_body` の出力型はStringです。HTTP本文にはこの変数だけを設定します。

JSONファイルを使う場合は、`input_message` と `ai_interpretation` の値を
それぞれ復元して貼り付けます。ファイル全体や、引用符と `\n` を含むJSON文字列を
そのまま入力欄に貼らないでください。コードが一度だけJSONへ変換します。

## 4. 結果の読み方と保存

statusだけでなく、Fact・View・Care・unresolvedを確認します。
概要だけでは要求や禁止事項が抜ける場合があります。`mapped` は実行許可ではありません。
実測モード・再試行回数は最終JSONにはないため、HTTP応答ヘッダーのrequest IDと
サーバートレースを対応させます。

成功・失敗とも入力、HTTP応答、最終出力、必要なトレースを保存します。
長文では約7分半の直接API実測があります。配布HTTPノードのreadは600秒、
SANAの標準全体予算は605秒です。プロキシを含む待機時間の境界に注意してください。
接続経路で必要な調整は共通ガイドを参照します。再実行前に失敗したノードを確認します。

LLMに計画自体を作らせる場合は [Plan and Align専用手順](DIFY-PLAN-AND-ALIGN-ja.md) を使います。
