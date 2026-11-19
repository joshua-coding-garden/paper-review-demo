# log.py
# 登入檢查用的 log：同時印在終端機、也寫進 login.log 檔
# 因為瀏覽器上只看得到「帳號或密碼錯誤」，看不出到底錯在哪，
# 所以把每次登入的細節記下來，出問題時打開 login.log 就能查
import logging

loginLog = logging.getLogger("login")
loginLog.setLevel(logging.INFO)
loginLog.propagate = False  # 不要再交給 uvicorn 的 log 印一次，避免重複

if not loginLog.handlers:  # fastapi dev 重新載入時避免重複加 handler
	fmt = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s", "%Y-%m-%d %H:%M:%S")

	fileHandler = logging.FileHandler("login.log", encoding="utf-8")
	fileHandler.setFormatter(fmt)
	loginLog.addHandler(fileHandler)

	consoleHandler = logging.StreamHandler()
	consoleHandler.setFormatter(fmt)
	loginLog.addHandler(consoleHandler)
