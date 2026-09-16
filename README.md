# SANA Premise Alignment API — 0.1.0 prototype

**Powered by SANA OS** — https://sana-os.org/

人の入力とAIの解釈の間にある前提を、実行前に可視化するAPIです。
添付されたSANA原文を保持し、LLM Ambiguity Lab v2の考え方を実APIへ接続する初期実装です。
合意・正しさ・実行許可を判定するものではありません。

## 起動（Docker Desktop / Docker Engine、Linuxコンテナ）

このソースを置いたGitHubリポジトリをcloneし、そのディレクトリで操作します。
配布ZIPを展開しても同じです。公開リポジトリ・コンテナレジストリはまだ作成していません。

```bash
cp .env.example .env
```

Windows PowerShellでは `Copy-Item .env.example .env`。
`.env` の `LLM_BASE_URL`、`LLM_API_KEY`、`LLM_MODEL` を利用先に合わせます。
APIキーはREADMEやGitHubへ書かず、このローカルファイルにだけ設定します。

```bash
docker build -t sana-alignment:0.1.0 .
docker run --rm --name sana-alignment --env-file .env -p 127.0.0.1:8000:8000 sana-alignment:0.1.0
```

まとめて起動する場合:

```bash
docker compose up --build -d
```

ブラウザで http://localhost:8000/docs を開くとAPIを試せます。
Swaggerの `/v1/align` → Try it out → Execute。
`SANA_API_TOKEN`を設定した場合はAuthorization欄に `Bearer 設定したトークン`。
`/healthz` はプロセスの稼働確認のみで、モデル接続の成功を意味しません。

**clone→API設定→docker runだけ**にするには、事前ビルドしたイメージの公開が必要です。
この段階では初回の `docker build` を含みます。公開イメージURLは捏造していません。

## 呼び出し

```bash
curl -X POST http://localhost:8000/v1/align -H "Content-Type: application/json" --data-binary @examples/align.json
```

PowerShellでは `curl` の代わりに `curl.exe`。
認証ありなら `-H "Authorization: Bearer YOUR_SANA_TOKEN"` を追加します。

```json
{
  "input_message": "来週のデモ用に顧客情報を見せたい。実在の顧客データは使えません。",
  "ai_interpretation": "本番の顧客DBを読み取り専用で接続する。",
  "language": "ja"
}
```

`ai_interpretation` は下流AIが明示した理解・予定であり、隠れた思考過程ではありません。
省略時はこのエンジンの読み取りをViewに返し、別のAIの前提を捏造しません。
`context` は任意の `{ "speaker": "human|ai|source", "text": "..." }` の配列。
文脈は古い順に並べます。任意で `representation: "verbatim|summary|unknown"`、
`response_status: "answered|unknown|context_dependent|not_applicable|declined"`、
`omitted_information` を付けられます。要約の省略範囲が不明ならunknownのままにします。
再確認時は修正した入力や必要な過去発言を送り直します。セッション・履歴保存はありません。

`frameworks` 省略なら自動選択、`[]` なら詳細レンズなし、`["RBM","RSM"]` なら明示選択（最大3）。
常設CoreのIntegrated Knowledgeには全体概念が含まれます。
選択レンズは仮説整理に使用し、独立した数値診断器としては実装していません。

## Fact / View / Care

| 出力 | 内容 |
| --- | --- |
| `observations` | 実際に受け取った原文・引用。sourceとquoteで照合可能 |
| `fact` | タスク内の事実主張。真実と認定した情報ではない |
| `view.premises` | 入力に含まれる解釈・評価・枠組み |
| `view.understanding` | このエンジンの暫定的な読み取り |
| `view.hypotheses` | エンジンの仮説、根拠引用、確認質問 |
| `view.premise_gaps` | 人と提示されたAI解釈の差。違いを保持できる |
| `view.unknowns` / `questions` | 次の処理を変える未確定事項・確認質問 |
| `care` | 守りたい利益・優先事項・価値・望む結果。不明ならnull |
| `acknowledgment` | 挨拶などの応答。Careの価値マッピングと分離 |

各前提は `source`、`status`、`support_state`、`materiality`、`execution_effect`、`evidence` を持ちます。
外部検証を行わないため `externally_verified` は常にfalse。
Careの `support_state` は `not_applicable`。価値を事実の証明対象にしません。
挨拶はhandshake。意味がつかめない入力には「わからない」を返し、無理に分析しません。

## 状態と下流接続

| status | 意味 |
| --- | --- |
| `handshake` | 挨拶を受領。分析なし |
| `unknown` | 意味が解釈できない。Careはnull |
| `context_insufficient` | 言葉はわかるがタスク・参照対象を特定できない |
| `needs_clarification` | 実行内容を左右する未確定点がある |
| `mapped` | 今回の出力では重大な未確認点を挙げていない |
| `mapped_with_divergence` | 差を記録したまま扱えるという暫定評価 |

差・仮説の `blocks_execution` がfalseなら、その差だけでは確認待ちにしません。
確認質問はその場合も任意の検証手段として残せます。
**`mapped` でも自動実行の承認ではありません。** `meta.execution_authorized` は常にfalse。
下流は元の入力・出力・出典を保持し、各ワークフローで必要な実行条件を別途判断します。
単なるHTTP 200判定で実行に進まないでください。

HTTP 422は入力形式、401はこのAPIの認証、502はモデルの出力/接続先エラー、
503は接続不可・利用制限、504は時間切れです。通信失敗を「意味不明」に偽装しません。
再試行は呼び出し側で判断します。自動再試行はせず、通常入力は最大2回のLLM呼び出しです。

## 対応プロバイダ

`/chat/completions`、`messages`、`choices[0].message.content` を提供する互換APIを対象とします。
個別製品との接続を確認済みという意味ではありません。
JSONモードに非対応なら `LLM_JSON_MODE=false`。その場合もJSONスキーマ検証は行います。
モデルにはCore・選択レンズ・入出力スキーマを収容できるコンテキスト容量が必要です。
プロバイダ固有API（Anthropicネイティブ等）は未対応です。

ローカル推論サーバー例：Docker Desktopからホストへ接続する場合、
`LLM_BASE_URL=http://host.docker.internal:8001/v1`。
Linux Docker Engineではrunに `--add-host=host.docker.internal:host-gateway` を追加。
ホストのサーバーがコンテナ側から到達可能なアドレスで待受している必要があります。
コンテナ内のlocalhostはホストPCを指しません。

## 開発・検証

Python 3.12。

```bash
python -m venv .venv
# Linux/macOS: source .venv/bin/activate
# PowerShell: .venv\Scripts\Activate.ps1
pip install -r requirements-dev.lock
python -m pytest -q
```

実モデルを使わない契約テストです。APIのJSON検証・出典検証・分岐は検証できますが、
選択したLLMの解釈品質は保証しません。`docs/ACCEPTANCE.md` で実モデルの出力を確認します。
Dockerのビルド・起動確認はGitHub Actionsにも含めています（今回の環境にはDockerなし）。

## 実装範囲

`docs/DESIGN.md` にCore Specificationとの差分と設計判断を明記しています。
Δv計測、対話状態機械、永続学習、検索/RAG、下流実行は含みません。
リクエスト本文・APIキーをアプリのログに保存しませんが、送信先LLMには入力・文脈が送られます。
初期設定はホストPCのlocalhost公開。外部公開時は認証・TLS・利用量制御を配置してください。

## 出典・権利表示

- [SANA OS](https://sana-os.org/)
- [原典リポジトリ](https://github.com/sana-os/sana-os)
- [LLM Ambiguity Lab v2](https://sana-os.org/llm-ambiguity-lab/)
- [LLM Ambiguity Lab v1](https://deshimarusakaguchi.com/llm-ambiguity-lab/)

`knowledge/` は提供資料のコピーです。Core Principleを含め本文は変更していません。
`knowledge/manifest.json` に元ファイル名・SHA-256を記録。READMEは衝突を避けて改名。
本APIと適用プロファイルは新規の派生実装であり、元仕様の完全準拠実装を称しません。
原資料のライセンスは [SANA OS License v1.0](https://github.com/sana-os/sana-os/blob/main/LICENSE.md) を参照。
新規コードの公開ライセンスは所有者による選定前です（MIT等を自動付与していません）。

設計背景として4本の論文を `references/` に同梱しています。
全文を常時プロンプトに追加せず、観察範囲・自己の解釈の点検・構造の出力・Interpreter/Executor分離へ反映しました。
Preference Compassは前提の扱いの参考であり、アンケート・人格評価・関係データベースは実装していません。
