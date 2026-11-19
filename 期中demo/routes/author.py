# routes/author.py
# 作者功能，網址都在 /author 底下
#
# 共通原則：
#   GET  = 「看」：只讀資料庫、顯示畫面，不會改到資料
#   POST = 「改」：新增/修改/刪除，做完用 303 轉回清單
#          (因為如果停在 POST 的結果頁，使用者按 F5 會再送一次，資料就重複了)
#
# 安全原則：每條 SQL 都加上 author_id=目前登入者，
#   因為就算有人自己亂打網址，也只能動到自己的稿件
from fastapi import APIRouter, Depends, Request, Form, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from db import getDB
from auth import chkLogin

router = APIRouter()
templates = Jinja2Templates(directory="templates")

CATEGORIES = ["研究論文", "技術報告", "評論"]


# 查看投稿稿件清單(類別、標題、審查狀態)
@router.get("/papers")
async def paperList(request: Request, user=Depends(chkLogin("author")), db=Depends(getDB)):
	cur = await db.execute(
		"SELECT id, category, title, status, updated_at FROM papers WHERE author_id=%s ORDER BY updated_at DESC;",
		(user["id"],),
	)
	papers = await cur.fetchall()
	return templates.TemplateResponse(
		name="authorList.html", request=request,
		context={"user": user, "papers": papers},
	)


# 新增投稿 — GET 顯示空白表單
@router.get("/papers/new")
async def paperNew(request: Request, user=Depends(chkLogin("author"))):
	return templates.TemplateResponse(
		name="paperForm.html", request=request,
		context={"user": user, "paper": None, "categories": CATEGORIES},
	)


# 新增投稿 — POST 存進資料庫，狀態一開始是「編輯中」
@router.post("/papers/new")
async def paperInsert(
	category: str = Form(...), title: str = Form(...), content: str = Form(...),
	user=Depends(chkLogin("author")), db=Depends(getDB),
):
	await db.execute(
		"INSERT INTO papers (author_id, category, title, content, status) VALUES (%s, %s, %s, %s, '編輯中');",
		(user["id"], category, title, content),
	)
	return RedirectResponse(url="/author/papers", status_code=303)


# 編輯投稿 — GET 顯示表單，並把舊內容先填好
@router.get("/papers/{pid}/edit")
async def paperEdit(pid: int, request: Request, user=Depends(chkLogin("author")), db=Depends(getDB)):
	cur = await db.execute(
		"SELECT * FROM papers WHERE id=%s AND author_id=%s AND status='編輯中';",
		(pid, user["id"]),
	)
	paper = await cur.fetchone()
	# 找不到 = 不是你的稿，或已經送審不能改了
	if paper is None:
		raise HTTPException(status_code=404, detail="找不到可編輯的稿件")
	return templates.TemplateResponse(
		name="paperForm.html", request=request,
		context={"user": user, "paper": paper, "categories": CATEGORIES},
	)


# 編輯投稿 — POST 更新內容
# WHERE 裡加 status='編輯中'，因為送審後就不該再被修改
@router.post("/papers/{pid}/edit")
async def paperUpdate(
	pid: int, category: str = Form(...), title: str = Form(...), content: str = Form(...),
	user=Depends(chkLogin("author")), db=Depends(getDB),
):
	cur = await db.execute(
		"UPDATE papers SET category=%s, title=%s, content=%s, updated_at=now() "
		"WHERE id=%s AND author_id=%s AND status='編輯中';",
		(category, title, content, pid, user["id"]),
	)
	if cur.rowcount == 0:
		raise HTTPException(status_code=400, detail="只有自己「編輯中」的稿件可以修改")
	return RedirectResponse(url="/author/papers", status_code=303)


# 刪除編輯中稿件
@router.post("/papers/{pid}/delete")
async def paperDelete(pid: int, user=Depends(chkLogin("author")), db=Depends(getDB)):
	cur = await db.execute(
		"DELETE FROM papers WHERE id=%s AND author_id=%s AND status='編輯中';",
		(pid, user["id"]),
	)
	if cur.rowcount == 0:
		raise HTTPException(status_code=400, detail="只有自己「編輯中」的稿件可以刪除")
	return RedirectResponse(url="/author/papers", status_code=303)


# 送出投稿：編輯中 => 審查中
# 狀態檢查直接寫在 WHERE 裡：如果稿件不是「編輯中」，這行就改不到任何資料(rowcount=0)
@router.post("/papers/{pid}/submit")
async def paperSubmit(pid: int, user=Depends(chkLogin("author")), db=Depends(getDB)):
	cur = await db.execute(
		"UPDATE papers SET status='審查中', updated_at=now() "
		"WHERE id=%s AND author_id=%s AND status='編輯中';",
		(pid, user["id"]),
	)
	if cur.rowcount == 0:
		raise HTTPException(status_code=400, detail="只有自己「編輯中」的稿件可以送出")
	return RedirectResponse(url="/author/papers", status_code=303)
