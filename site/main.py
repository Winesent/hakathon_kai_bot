import sqlite3
import uvicorn
from flask import make_response
from fastapi import FastAPI, Form, Response, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi_users.authentication import CookieTransport
from fastapi.responses import RedirectResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.responses import JSONResponse
from utils.JWT import *
from json import dumps

origins = ['https://localhos']
cookie_transport = CookieTransport(cookie_max_age=36000)
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
con = sqlite3.connect("users.db", check_same_thread=False)
cur = con.cursor()
db_session.global_init("db/users.db")
templates = Jinja2Templates(directory="templates")

def bot_call(telegram):
    data = "error"
    return data

@app.get("/registration")
def register(request: Request):
    return templates.TemplateResponse("registration.html", {"request": request})

@app.post("/registration")
def registration(dct):
    db_sess = db_session.create_session()
    data = db_sess.query(User).filter(User.uid == dct[0]).first()
    if not data:
        user = User(
            uid=dct[0],
            fio=dct[1],
            group_number=dct[2],
            points=dct[3],
            password=dct[4],
            admin=dct[5]
        )
        db_sess.add(user)
        db_sess.commit()
        db_sess.close()
        return {"status": "success"}
    return {"status": "exists", "message": "Такой пользователь уже существует"}

@app.get("/")
def log_in(request: Request, msg=""):
    return templates.TemplateResponse("code.html", {"request": request, "password": ""})


@app.post("/index")
def success(request: Request, login=Form()):
    db_sess = db_session.create_session()
    print(login)
    flag = str(db_sess.query(User).filter(User.login == str(login)).first()).split(", ")
    db_sess.close()
    if flag[0] != "None" and (flag[-1] == "False"):
        db_sess = db_session.create_session()
        students = db_sess.query(Shop).all()
        ans = []
        i = 0
        print(students)
        for x in students:
            i = i + 1
            print(str(x).split(", "))
            ans.append(str(x).split(", "))
        print(ans)
        return templates.TemplateResponse("index.html", {
            "request": request,
            "name": flag[0],
            "group": flag[2],
            "points": flag[3],
            "items": ans
        })
    if flag[0] != "None" and (flag[-1] == "True"):
        db_sess = db_session.create_session()
        students = db_sess.query(User).all()
        ans = []
        i = 0
        for x in students:
            i = i + 1
            ans.append(str(x).split(", ").append(i))
        print(ans)
        return templates.TemplateResponse("admin.html",
            {"request": request,
             "students": ans})
    return RedirectResponse(f"/?telegram={login}&msg=неверный+код", 302)



@app.get("/user_information")
def inf(uid):
    db_sess = db_session.create_session()
    data = str(db_sess.query(User).filter(User.uid == int(uid)).first()).split(", ")
    db_sess.close()
    if data:
        ans = dumps({"fio": str(data[0]),  "uid": data[1], "group_number": data[2], "points": data[3]}, ensure_ascii=False)
        return ans
    return "Такого пользователя не существует"


@app.get("/change_user")
def chng(uid, data, do):
    comands = {
        "points": User.points,
        "uid": User.uid,
        "grou_number": User.group_number,
        "fio": User.fio,
        "login": User.login,
        "admin": User.admin
    }
    db_sess = db_session.create_session()
    db_sess.query(User).filter(User.uid == int(uid)).update({do: data})
    db_sess.commit()
    db_sess.close()
    return

if __name__ == "__main__":
    uvicorn.run(app, port=8000)