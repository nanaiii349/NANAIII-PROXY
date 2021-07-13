import asyncio
import socket
import struct
import aiosqlite
import time
Max_Token = 200000
vised = []


class item:
    def __init__(self):
        super().__init__()
        self.name = " "
        self.Bandwidth = 0
        self.Token_bucket = 0
        self.lock = asyncio.Lock()


async def dbinit():
    async with aiosqlite.connect(r'E:\Git\Python\Project\connect.db') as db:
        try:
            await db.execute("CREATE TABLE user (username text primary key, password text not null,Bandwidth int)")
        except Exception as e:
            await db.execute("drop table user")
            await db.execute("CREATE TABLE user (username text primary key, password text not null,Bandwidth int)")
        await db.execute("INSERT INTO user (username,password,Bandwidth) VALUES('lty', '2018211349',1000000)")
        await db.execute("INSERT INTO user (username,password,Bandwidth) VALUES('zzl', '2018211346',2000000)")
        await db.execute("INSERT INTO user (username,password,Bandwidth) VALUES('hzz', '2018211362',3000000)")
        await db.commit()


async def add_Token(user):
    start = time.time()
    while True:
        await asyncio.sleep(0.01)
        cur = time.time()
        if(user.lock.locked() == True):
            print("add lock state:", user.lock.locked())
        await user.lock.acquire()
        if(cur-start > 0.01):
            if(user.Token_bucket+user.Bandwidth/100 < Max_Token):
                user.Token_bucket += user.Bandwidth/100
            else:
                user.Token_bucket = Max_Token
            # print("Token_bucket after add:", user.Token_bucket)
            start = cur
        user.lock.release()


async def server_client(nreader, writer, user):
    while True:
        sflag = 0
        message = await nreader.read(40000)
        if len(message) == 0:
            break
        while sflag == 0:
            await asyncio.sleep(0.01)
            await user.lock.acquire()
            if(user.Token_bucket > len(message)):
                # print("Tolocal")
                writer.write(message)
                await writer.drain()
                user.Token_bucket -= len(message)
                # print("Token_bucket after read:", user.Token_bucket)
                sflag = 1
            user.lock.release()


async def client_server(reader, nwriter, user):
    while True:
        cflag = 0
        message = await reader.read(40000)
        if len(message) == 0:
            break
        while cflag == 0:
            await asyncio.sleep(0.01)
            await user.lock.acquire()
            if(user.Token_bucket > len(message)):
                # print("ToWWW")
                nwriter.write(message)
                await nwriter.drain()
                user.Token_bucket -= len(message)
                # print("Token_bucket after witer:", user.Token_bucket)
                cflag = 1
            user.lock.release()


async def handle_echo(reader, writer):

    addr = writer.get_extra_info('peername')
    print(f"request from:{addr}")
    data = await reader.read(4096)
    message = data.decode().split()
    print(f"message:{message}")
    username = message[2]
    password = message[3]
    isUser = 0

    # 查找该用户是否已经被登记
    isVised = -1
    for i in range(len(vised)):
        if username == vised[i].name:
            isVised = i
            print("Verified username:", username)
            isUser = 1
            break
    else:
        async with aiosqlite.connect(r'E:\Git\Python\Project\connect.db') as db:
            async with db.execute(f"SELECT password,Bandwidth FROM user where username='{username}'") as cursor:
                async for row in cursor:
                    if password == row[0]:
                        print("new user")
                        # 创建一个新用户
                        newUser = item()
                        # print(newUser.lock.locked())
                        newUser.name = username
                        newUser.Bandwidth = row[1]
                        # 初始化令牌桶
                        newUser.Token_bucket = Max_Token
                        # 登记该新用户
                        vised.append(newUser)
                        # 操作令牌桶
                        await add_Token(newUser)

                        print("Authentication username:", username)
                        isUser = 1
                        break

    if isUser == 1:
        try:
            nreader, nwriter = await asyncio.open_connection(host=message[0], port=message[1])
            print(f'Connected to {message[0]} {message[1]}')
            reploy = b"200"
        except:
            print("Connected failed \n")
            reploy = b"404"
        writer.write(reploy)
        await writer.drain()
        if reploy == b'200':
            await asyncio.gather(server_client(nreader, writer, vised[isVised]), client_server(reader, nwriter, vised[isVised]))
    else:
        reploy = b'303'
        writer.write(reploy)
        await writer.drain()
        print("Authentication failed")

    print("Close the connection \n")
    writer.close()


async def main():
    await dbinit()
    server = await asyncio.start_server(
        handle_echo, '127.0.0.1', 8848)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')
    async with server:
        await server.serve_forever()

asyncio.run(main())
