from sanic import Sanic
from sanic.response import *
from sanic.exceptions import *
import aiosqlite

app = Sanic("remoteProxyAdmin")
db_name = "connection.db"


@app.exception(NotFound)
async def _404(request, exc):
    return text("errUrl", status=404)


@app.get('/user')  # 查所有
async def get_all_user(request):
    all_user = []
    async with aiosqlite.connect(db_name) as db:
        async with db.execute("select username,passwd,velocity from users") as cusor:
            async for row in cusor:
                user = {'username': row[0], 'passwd': row[1], 'velocity': row[2]}
                all_user.append(user)
    return json(all_user)


@app.get('/user/<username>')  # 查一个
async def get_a_user(request, username):
    async with aiosqlite.connect(db_name) as db:
        async with db.execute(f"select username,passwd,velocity from users where username=\'{username}\'") as cusor:
            async for row in cusor:
                user = {'username': row[0], 'passwd': row[1], 'velocity': row[2]}
                return json(user)


@app.post('/user')  # 增加一个用户
async def add_a_user(request):
    username = request.json.get('username')
    passwd = request.json.get('passwd')
    velocity = request.json.get('velocity')
    if not username or not passwd or not velocity:
        return text("Please complete user information", status=405)
    else:
        async with aiosqlite.connect(db_name) as db:
            async with db.execute(f"select * from users where username=\'{username}\'")as cusor:
                async for row in cusor:
                    return text('This username is already used, please use another one and try again', status=405)
                else:
                    await db.execute(f"insert into users values(\'{username}\',\'{passwd}\',{velocity})")
                    await db.commit()
                    return text(f"Successfully add new user {username}")


@app.put('/user/<username>') #修改用户信息
async def alter_user(request, username):
    origin_passwd = request.json.get('origin_passwd')
    new_passwd = request.json.get('new_passwd')
    velocity = request.json.get('velocity')
    if not username or not origin_passwd or not velocity or not new_passwd:
        return text("Please complete user infomations that holds username, origin_passwd, new_passwd, velocity",
                    status=405)
    async with aiosqlite.connect(db_name) as db:
        async with db.execute(f"select passwd from users where username=\'{username}\'")as cusor:
            async for row in cusor:
                if row[0] != origin_passwd:
                    return text("Origin password is wrong, please try again", status=405)
                else:
                    await db.execute(
                        f"update users set passwd=\'{new_passwd}\',velocity=\'{velocity}\' where username=\'{username}\'")
                    await db.commit()
                    return text(f"Successfully update user {username}'s info")
            else:
                return text(f"No user named {username}", status=404)


@app.delete('/user/<username>') #删除用户
async def delete_user(request, username):
    async with aiosqlite.connect(db_name) as db:
        async with db.execute(f"select * from users where username=\'{username}\'")as cusor:
            async for row in cusor:
                await db.execute(f"delete from users where username=\'{username}\'")
                await db.commit()
                return text(f"Sucessfully delete user {username}")
            else:
                return text(f"No user named {username}", status=404)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=80)
