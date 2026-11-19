-- 投稿審查系統 資料表
-- 用 Adminer 或 psql 在 mydb 裡執行這個檔案即可

DROP TABLE IF EXISTS "public"."papers";
DROP TABLE IF EXISTS "public"."users";

-- 使用者：role 決定他是作者(author)還是編輯(editor)
CREATE TABLE "public"."users" (
    "id"       serial PRIMARY KEY,
    "username" character varying(20) UNIQUE NOT NULL,
    "password" character varying(50) NOT NULL,
    "role"     character varying(10) NOT NULL CHECK ("role" IN ('author', 'editor'))
);

-- 稿件：author_id 記錄是誰寫的，status 記錄現在走到哪個階段
CREATE TABLE "public"."papers" (
    "id"         serial PRIMARY KEY,
    "author_id"  integer NOT NULL REFERENCES "public"."users"("id"),
    "category"   character varying(20) NOT NULL,
    "title"      character varying(100) NOT NULL,
    "content"    text NOT NULL,
    "status"     character varying(10) NOT NULL DEFAULT '編輯中'
                 CHECK ("status" IN ('編輯中', '審查中', '已通過')),
    "updated_at" timestamp NOT NULL DEFAULT now()
);

-- 測試帳號（密碼都是 1234）
INSERT INTO "public"."users" ("username", "password", "role") VALUES
('author1', '1234', 'author'),
('author2', '1234', 'author'),
('editor1', '1234', 'editor');

-- 示範稿件：三種狀態各一篇，demo 時一登入就有東西看
INSERT INTO "public"."papers" ("author_id", "category", "title", "content", "status") VALUES
(1, '研究論文', '區塊鏈在供應鏈追蹤的應用', '本文探討如何利用區塊鏈不可竄改的特性追蹤商品來源……', '編輯中'),
(1, '技術報告', 'FastAPI 與 PostgreSQL 整合實務', '本報告說明如何以 psycopg 連線池搭配 FastAPI……', '審查中'),
(2, '評論',     '生成式 AI 對程式教育的影響', '近年生成式 AI 快速發展，學生寫程式的方式也隨之改變……', '已通過');
