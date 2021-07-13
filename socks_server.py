import asyncio
import socket
import struct
SOCKS_VERSION = 5


async def handle_echo(reader, writer):

    # 读取客户端的报头
    c_header = await reader.read(100)
    print(f"c_header:{c_header}")
    assert c_header[0] == SOCKS_VERSION
    assert c_header[1] > 0

    # 获取报头内的方法
    methods = []
    for i in range(c_header[1]):
        methods.append(c_header[2+i])
    # print(methods)

    if 0 not in set(methods):
        print("Connection failed")
        return

    # 返回服务端报头
    s_header = struct.pack("!BB", SOCKS_VERSION, 0)
    writer.write(s_header)
    await writer.drain()
    # 完成第一次握手

    # 获取客户端请求报
    request = await reader.read(100)
    print(f"request:{request}")
    version, cmd, _, address_type = struct.unpack(
        "!BBBB", request[:4])
    assert version == SOCKS_VERSION
    # 对地址类型分类处理
    if address_type == 1:  # IPv4
        address = socket.inet_ntoa(request[4:8])
    elif address_type == 3:  # Domain name
        domain_length = request[4]
        address = request[5:5+domain_length]
    elif address_type == 4:  # IPv6
        address = socket.inet_ntop(socket.AF_INET6, request[4:20])
    else:
        print("Connection failed")
        return
    # 计算port
    port = request[-2]*256+request[-1]
    print(f"IP:{address}  PORT:{port}")

    # 尝试建立连接
    try:
        if cmd == 1:  # CONNECT
            nreader, nwriter = await asyncio.open_connection(host=address, port=port)
            print('Connected to {} {}'.format(address, port))
        else:
            print("Cmd wrong")
            return
        reploy = "\x05\x00\x00".encode()+request[3:]
    # 连接出错返回错误响应
    except Exception as err:
        print("Connection Failed")
        reploy = struct.pack("!BBBBIH", SOCKS_VERSION,
                             5, 0, address_type, 0, 0)
    # 返回响应报
    writer.write(reploy)
    await writer.drain()

    async def server_client(nreader, writer):
        while True:
            message = await nreader.read(4096)
            writer.write(message)
            await writer.drain()
            if len(message) == 0:
                break

    async def client_server(reader, nwriter):
        while True:
            message = await reader.read(4096)
            nwriter.write(message)
            await writer.drain()
            if len(message) == 0:
                break

    # 符合条件开始交换数据
    if reploy[1] == 0 and cmd == 1:
        await asyncio.gather(server_client(nreader, writer), client_server(reader, nwriter))
    print("Close the connection")
    writer.close()


async def main():
    server = await asyncio.start_server(handle_echo, '127.0.0.1', 8080)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')
    async with server:
        await server.serve_forever()

asyncio.run(main())
