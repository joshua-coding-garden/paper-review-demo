# main.py
# 啟動方式: fastapi dev main.py
from fastapi import FastAPI, Depends, Request, Form
from fastapi.responses import RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from db import getDB, lifespan
from log import loginLog

templates = Jinja2Templates(directory="templates")
app = FastAPI(lifespan=lifespan)

# session：讓伺服器記得「現在是誰登入」，換頁也不會忘記
app.add_middleware(
	SessionMiddleware,
	secret_key="paper-review-secret-key",
	max_age=None,
	same_site="lax",
	https_only=False,
)

# 作者、編輯的功能分別放在 routes/ 底下，網址前面自動加上 /author、/editor
from routes.author import router as authorRoute
from routes.editor import router as editorRoute
app.include_router(authorRoute, prefix="/author")
app.include_router(editorRoute, prefix="/editor")


@app.get("/")
async def home(request: Request):
	user = request.session.get("user")
	if user is None:
		return RedirectResponse(url="/login", status_code=303)
	# 依角色送到各自的首頁
	if user["role"] == "editor":
		return RedirectResponse(url="/editor/papers", status_code=303)
	return RedirectResponse(url="/author/papers", status_code=303)


# GET /login：只是「看」登入畫面
@app.get("/login")
async def loginPage(request: Request):
	return templates.TemplateResponse(name="login.html", request=request, context={"error": None})


# POST /login：送出帳密，伺服器去資料庫比對
@app.post("/login")
async def login(request: Request, username: str = Form(...), password: str = Form(...), db=Depends(getDB)):
	ip = request.client.host if request.client else "?"
	# 去掉帳號前後的空白：因為瀏覽器自動填入或手滑多打空格時，
	# 'author1 ' 和 'author1' 對資料庫來說是兩個不同的字串，就會查不到人
	username = username.strip()

	# 先只用帳號查，因為這樣才分得出「帳號不存在」還是「密碼打錯」
	cur = await db.execute(
		"SELECT id, username, password, role FROM users WHERE username=%s;",
		(username,),
	)
	user = await cur.fetchone()

	if user is None or user["password"] != password:
		reason = "帳號不存在" if user is None else "密碼錯誤"
		# repr() 會把看不見的空白、全形字元現出原形，例如 'author1 ' 後面多一個空格
		# 密碼直接印出來方便除錯（demo 用；正式上線的系統不能這樣做）
		loginLog.warning(f"登入失敗 帳號={username!r} 密碼={password!r} 原因={reason} IP={ip}")
		# 畫面上故意不說是哪個錯，避免別人用來猜哪些帳號存在
		return templates.TemplateResponse(
			name="login.html", request=request,
			context={"error": "帳號或密碼錯誤"}, status_code=401,
		)

	loginLog.info(f"登入成功 帳號={username} 角色={user['role']} IP={ip}")
	# 把使用者資料記在 session，之後每個頁面都能知道是誰
	request.session["user"] = {"id": user["id"], "username": user["username"], "role": user["role"]}
	return RedirectResponse(url="/", status_code=303)


@app.get("/logout")
async def logout(request: Request):
	user = request.session.get("user")
	if user:
		loginLog.info(f"登出 帳號={user['username']}")
	request.session.clear()
	return RedirectResponse(url="/login", status_code=303)
