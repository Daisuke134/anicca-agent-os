# postiz-safe — Postiz 投稿作成の安全ラッパー

Postiz CLI の `posts:create` を直接叩く代わりに、必ずこのラッパー経由で投稿を作成すること。
根本原因と証拠の正本: anicca-ops `files/postiz-link-fix-2026-11-17.md`。

## なぜ必要か（2026-11-17 実測で確定）

1. **Postiz Cloud は X 投稿の本文から全 URL を作成時にサーバー側で削除する**（環境変数
   `STRIP_LINKS_FROM_X_POSTS` → X プロバイダの `stripLinks()`）。ベンダーが「意図的な仕様で、
   組織ごとの無効化はしない」と公式に回答済み（gitroomhq/postiz-app Issue #1939）。
   下書き・予約・CLI・JSON・shortLink の有無を問わず消える。スレッド／返信の各要素も同様。
   **つまり Postiz Cloud 経由の X 投稿にリンクは絶対に入らない。** 入れて公開すると、
   リンクだけが消えた投稿が何の警告もなく出る。
2. **LinkedIn 等では CLI 既定の shortLink=true が元の URL を dub.sh の短縮リンクへ
   書き換える**。shortLink=false なら元の URL がそのまま保存・公開される（実測済み）。

## 使い方

```bash
# 引数は postiz posts:create と同じ
~/workspace/tools/postiz-safe/postiz-post -c "本文 https://example.com/page" \
  -s 2026-11-18T10:00:00+09:00 -i <integrationId> [--settings '{...}']

# JSON 経路も同じ（shortLink:false を自動注入する）
~/workspace/tools/postiz-safe/postiz-post -j payload.json
```

## ラッパーが強制すること

- R1: shortLink を常に false にする（CLI は `--no-shortLink` を付与、JSON は書き換え）。
- R2: 対象に X チャンネルが含まれ、本文に URL がある場合は**送信前に拒否**する（exit 3）。
  リンクが消えても本当に構わない場合だけ `POSTIZ_SAFE_ALLOW_X_URL=1` を付ける。
- R3: 作成後に posts:list で保存本文を読み戻し、投入した URL が全て残っているか検証する。
  消えていたら exit 4、読み戻し自体が失敗したら exit 5（作成はされているが未検証）。

終了コード: 0=作成＋検証OK / 2=引数・IOエラー / 3=X+URLで拒否 / 4=作成済みだがURL欠落 /
5=作成済みだが未検証 / その他は CLI のコードをそのまま返す。

注意: posts:list は整形済み（ルート投稿の本文のみ）で返るため、R3 の検証対象はルート本文。
X のスレッド／返信要素は R2 の拒否でカバーする（どの要素も同じく剥がされるため）。

## X にリンクを載せたいときの正規ルート

- セルフホスト Postiz（移行締切 2026-11-25）では `STRIP_LINKS_FROM_X_POSTS` を
  設定しなければ剥がされない。ただし自前 X API は URL 入り投稿が $0.20/件の従量課金で、
  「API 新規支払い禁止」との整合は移行メモ §6-4 の親判断待ち。
- それまでは、リンクが要る告知は LinkedIn 等の残る面に載せ、X ではリンクなしで出す。
