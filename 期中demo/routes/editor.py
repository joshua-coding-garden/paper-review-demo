# routes/editor.py
# 編輯功能，網址都在 /editor 底下
# 編輯只處理「審查中」的稿件，所以每條 SQL 都帶 status='審查中'
from fastapi import APIRouter, Depends, Request, HTTPException
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from db import getDB
from auth import chkLogin

router = APIRouter()
templates = Jinja2Templates(directory="templates")


# 查看待審查清單(作者、類別、標題)
# 作者名字存在 users 表，所以要 JOIN 才拿得到
@router.get("/papers")
async def reviewList(request: Request, user=Depends(chkLogin("editor")), db=Depends(getDB)):
	cur = await db.execute(
		"SELECT p.id, u.username AS author, p.category, p.title, p.updated_at "
		"FROM papers p JOIN users u ON p.author_id = u.id "
		"WHERE p.status='審查中' ORDER BY p.updated_at;"
	)
	papers = await cur.fetchall()
	return templates.TemplateResponse(
		name="editorList.html", request=request,
		context={"user": user, "papers": papers},
	)


# 查看稿件內容
@router.get("/papers/{pid}")
async def reviewDetail(pid: int, request: Request, user=Depends(chkLogin("editor")), db=Depends(getDB)):
	cur = await db.execute(
		"SELECT p.*, u.username AS author FROM papers p JOIN users u ON p.author_id = u.id "
		"WHERE p.id=%s AND p.status='審查中';",
		(pid,),
	)
	paper = await cur.fetchone()
	if paper is None:
		raise HTTPException(status_code=404, detail="找不到待審查的稿件")
	return templates.TemplateResponse(
		name="paperDetail.html", request=request,
		context={"user": user, "paper": paper},
	)


# 選擇通過：審查中 => 已通過
@router.post("/papers/{pid}/approve")
async def reviewApprove(pid: int, user=Depends(chkLogin("editor")), db=Depends(getDB)):
	cur = await db.execute(
		"UPDATE papers SET status='已通過', updated_at=now() WHERE id=%s AND status='審查中';",
		(pid,),
	)
	if cur.rowcount == 0:
		raise HTTPException(status_code=400, detail="只有「審查中」的稿件可以通過")
	return RedirectResponse(url="/editor/papers", status_code=303)


# 退回稿件：審查中 => 編輯中（作者就能再修改）
@router.post("/papers/{pid}/reject")
async def reviewReject(pid: int, user=Depends(chkLogin("editor")), db=Depends(getDB)):
	cur = await db.execute(
		"UPDATE papers SET status='編輯中', updated_at=now() WHERE id=%s AND status='審查中';",
		(pid,),
	)
	if cur.rowcount == 0:
		raise HTTPException(status_code=400, detail="只有「審查中」的稿件可以退回")
	return RedirectResponse(url="/editor/papers", status_code=303)
