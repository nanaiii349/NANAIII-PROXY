from sanic import Sanic
from sanic.response import *
from sanic.exceptions import *
import aiosqlite

app=Sanic('remoteProxyAdmin')
dbName=r'E:\Git\Python\Project\connect.db'
# app.config.DB_NAME='connect.db'

@app.route('/')
async def test(req):
    return text('Hello World!')

@app.get("/user")
async def getAllUserInfo(req):
    user=[]
    async with aiosqlite.connect(dbName) as db:
        async with db.execute("select username,password,Bandwidth from user") as cusor:
            async for row in cusor:
                tmp = {'username': row[0], 'passwd': row[1], 'Bandwidth': row[2]}
                user.append(tmp)
    return json(user)

@app.get('/user/<username>')
async def getOneUserInfo(req,username):
    async with aiosqlite.connect(dbName) as db:
        async with db.execute(f"select username,password,Bandwidth from user where username=\'{username}\'") as cusor:
            async for row in cusor:
                tmp = {'username': row[0], 'password': row[1], 'Bandwidth': row[2]}
                return json(tmp)

@app.post("/user")
async def addUser(req):
    username=req.json.get('username')
    password=req.json.get('password')
    Bandwidth=req.json.get('Bandwidth')
    print(f"username:{username},password:{password},Bandwidth:{Bandwidth}")
    try:
        async with aiosqlite.connect(dbName) as db:
            await db.execute(f"insert into user values(\'{username}\',\'{password}\',\'{Bandwidth}\')")
            await db.commit()
    except Exception as e:
        return text(f"{e}. when add new user {username}",status=500)
    return text(f"Successfully add new user {username}")

@app.put('/user/<username>')
async def updateUser(req, username):
    oldPassword = req.json.get('oldPassword')
    newPassword = req.json.get('newPassword')
    newBandwidth= req.json.get('newBandwidth')
    print(f"oldPassword:{oldPassword},newPassword:{newPassword},newBandwidth:{newBandwidth}")
    async with aiosqlite.connect(dbName) as db:
        async with db.execute(f"select password from user where username=\'{username}\'")as cusor:
            async for row in cusor:
                if row[0] != oldPassword:
                    return text("password can not match. You have no right to update", status=405)
                else:
                    if not newBandwidth and newPassword:
                        await db.execute(f"update user set password=\'{newPassword}\'where username=\'{username}\'")
                    elif not newPassword and newBandwidth:
                        await db.execute(f"update user set Bandwidth=\'{newBandwidth}\' where username=\'{username}\'")
                    elif newPassword and newBandwidth:
                        await db.execute(f"update user set Bandwidth=\'{newBandwidth}\',password=\'{newPassword}\' where username=\'{username}\'")
                    else:
                        return text(f"Successfully update user: {username}.but you update nothing.")
                    await db.commit()
                    return text(f"Successfully update user: {username}")
            else:
                return text(f"Can not find user: {username}",status=404)

@app.delete('/user/<username>') #删除用户
async def delete_user(req, username):
    password = req.json.get('password')
    async with aiosqlite.connect(dbName) as db:
        async with db.execute(f"select password from user where username=\'{username}\'")as cusor:
            async for row in cusor:
                if row[0] != password:
                    return text("password can not match. You have no right to delect", status=405)
                else:
                    await db.execute(f"delete from user where username=\'{username}\'")
                    await db.commit()
                    return text(f"Successfully update user: {username}")
            else:
                return text(f"Can not find user: {username}",status=404)

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=8000)
