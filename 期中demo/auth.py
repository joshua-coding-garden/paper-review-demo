# auth.py
# 登入檢查：仿照老師 sessionLogin.py 的 chkLogin，多加一個「角色」檢查
from fastapi import Request, HTTPException
from log import loginLog


def chkLogin(role: str):
	def checker(request: Request):
		user = request.session.get("user")  # 登入時存進 session 的 {id, username, role}

		# 沒登入 → 因為不知道你是誰，所以送你回登入頁
		# (在依賴函式裡不能直接 return RedirectResponse，所以用 303 + Location 來做轉址)
		if user is None:
			loginLog.info(f"未登入 想進 {request.method} {request.url.path} → 轉到登入頁")
			raise HTTPException(status_code=303, headers={"Location": "/login"})

		# 有登入但角色不對 → 例如作者想進編輯頁面，直接拒絕
		if user["role"] != role:
			loginLog.warning(f"權限不足 帳號={user['username']}({user['role']}) 想進 {request.method} {request.url.path}")
			raise HTTPException(status_code=403, detail="你沒有權限使用這個功能")

		return user  # 路由函式拿到的 user 就是這個 dict
	return checker
