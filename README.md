# Gitlab-access-controlled simple web server

This is a web server for Gitlab pages or Gitlab review apps.

これはGitlabのアクセス権限設定に対応して静的コンテンツを提供するサーバーです。  
Gitlab PagesやReview Appにアクセス制御を追加することを目的にしています。

## 構成

このサーバーは、nginx + [oauth2_proxy](https://github.com/bitly/oauth2_proxy) + 本アプリ の構成で利用します。

```
     nginx
       ↓
  oauth2_proxy  ーoauth2 ー→  Gitlab
       ↓                 ｜
     server      ー API ー┘
```


GitlabサーバーのOAuth2機能を使ってoauth2_proxyで認証を行い、
そこで取得したaccess tokenを本アプリに渡します。  
本アプリでは受け取ったaccess tokenを使ってGitlab APIへアクセスし、
対象コンテンツのへアクセス可能かどうかを判定しています。

## コンテンツ

このサーバーが提供するコンテンツは、実行しているカレントディレクトリのファイルになります。  
`/srv/nginx/pages`というディレクトリで実行したのであれば、その中にある`/srv/nginx/pages/file.html`に`http://example.com/file.html`でアクセスできます。

アクセス可否の判定をするにあたって表示するコンテンツがどのプロジェクトに属しているかが問題になります。  
これは、表示対象ディレクトリにプロジェクトIDを記入した`.gitlab-info.json`というファイルを配置して判断します。  

.gitlab-info.jsonのフォーマットは以下の通りです。

```json
{
  "project_id": 1,
  "requires_access_to_code": false
}
```

`project_id`はGitlabのプロジェクトID(数値)です。`requires_access_to_code`がfalseであれば対象のプロジェクトにアクセス可能であればコンテンツを返答します(実質的にGuest権限以上)。逆にtrueにするとgitリポジトリのファイルにアクセス可能な権限がなければアクセスを拒否します(実質的にReporter権限以上)。

表示対象のURLのパスの直下にこの`.gitlab-info.json`ファイルがなければその上位ディレクトリを順番に探索して最初にみつけたものを使います。  
例えば`http://example.com/path/to/index.html`にアクセスしたときに、`/srv/nginx/pages/path/to/.gitlab-info.json`にファイルがなければ`/srv/nginx/pages/path/.gitlab-info.json`を、それもなければ`/srv/pages/.gitlab-info.json`を探します。


## セットアップ方法

実際に利用するときのセットアップ方法の例として、nginx + oauth2_proxy + 本サーバーの構成をDockerで起動できるようにしています。  
docker-compose.yml ファイルの各環境変数を書き換えた上で起動してください。

このサーバーはGitlab Pages用のサーバーとして、`http://myproj.example.com/myfile.html`にアクセスしたら`$PWD/pages/myproj/myfile.html`の内容を返答します。  
実際にGitlab PagesのコンテンツをGitlab-CIで生成するときは、以下のようにして`.gitlab-info.json`を作成してください。

```yaml:.gitlab-ci.yml
# .gitlab-ci.yml
pages:
  script:
    # コンテンツ生成
    - make some contents
    - mv build public
    # .gitlab-info.json生成
    - echo "{\"project_id\": $CI_PROJECT_ID, \"requires_access_to_code\": false}" > public/.gitlab-info.json
  artifacts:
    paths:
      - public
```

具体的なnginxやoauth2_proxyの設定方法については、dockerフォルダ下のファイルを参照してください。


