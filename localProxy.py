import asyncio
import socket
import struct
import argparse

SOCKS_VERSION = 5
remote_adr = ' '
remote_port = 0
username = ' '
password = ' '


async def server_client(nreader, writer):
    while True:
        message = await nreader.read(4096)
        print("Tolocal")
        writer.write(message)
        await writer.drain()
        if len(message) == 0:
            break


async def client_server(reader, nwriter):
    while True:
        message = await reader.read(4096)
        print("ToWWW")
        nwriter.write(message)
        await nwriter.drain()
        if len(message) == 0:
            break


async def connectRemote(addr, port, reader, writer, nreader, nwriter):
    requestToRemote = addr.encode() + b" " + str(port).encode() + b" " + \
        str(username).encode() + b" " + str(password).encode()
    nwriter.write(requestToRemote)
    print(f"requestToRemote:{requestToRemote}")
    await nwriter.drain()

    reployFromRemote = await nreader.read(4096)
    print(f"reployFromRemote:{reployFromRemote}")
    # print(reploy)

    # 符合条件开始交换数据
    # print("isConnected", isConnected)
    if reployFromRemote == b"200":
        await asyncio.gather(server_client(nreader, writer), client_server(reader, nwriter))
    elif reployFromRemote == b"404":
        print("Connection Failed")
    elif reployFromRemote == b'303':
        print("Authentication failed")
    print("Close the connection")
    writer.close()


async def https_client(reader, writer, c_header):
    # print(c_header)
    c_header = c_header.decode()
    request = c_header.split()

    if request[0] == "CONNECT":
        if (request[1][:7] == "http://"):
            addr = request[1]
            port = 80
        else:
            addr = request[1].split(":")[0]
            port = request[1].split(":")[1]
            # print(type(addr), type(port))
        print(f"Try to Connect: address:{addr} port:{port} ...")

        try:
            # print(type(remote_adr), type(remote_port))
            print(remote_adr, remote_port)
            nreader, nwriter = await asyncio.open_connection(str(remote_adr).encode(), str(remote_port).encode())
            print(f"Connected Success.")
            reploy = b"HTTP/1.1 200 OK\r\n\r\n"
            writer.write(reploy)
            await writer.drain()

        except Exception as err:
            print(err)
            print("Connected failed")
            reploy = b"HTTP/1.1 404 ERROR\r\n\r\n"
            writer.write(reploy)
            await writer.drain()
            return

        connectRemote(addr, port, reader, writer, nreader, nwriter)


async def socks_client(reader, writer, c_header):
    # 读取客户端的报头
    # print(f"c_header:{c_header}")
    assert c_header[0] == SOCKS_VERSION
    assert c_header[1] > 0

    # 获取报头内的方法
    methods = []
    for i in range(c_header[1]):
        methods.append(c_header[2 + i])
    # print(methods)

    if 0 not in set(methods):
        # print("method error")
        return

    # 返回服务端报头
    s_header = struct.pack("!BB", SOCKS_VERSION, 0)
    writer.write(s_header)
    await writer.drain()
    # 完成第一次握手

    # 获取客户端请求报
    request = await reader.read(100)
    # print(f"request:{request}")
    version, cmd, _, address_type = struct.unpack(
        "!BBBB", request[:4])
    assert version == SOCKS_VERSION
    # 对地址类型分类处理
    if address_type == 1:  # IPv4
        address = socket.inet_ntoa(request[4:8])
    elif address_type == 3:  # Domain name
        domain_length = request[4]
        address = request[5:5 + domain_length]
    elif address_type == 4:  # IPv6
        address = socket.inet_ntop(socket.AF_INET6, request[4:20])
    else:
        # print("address_type error")
        return
    # 计算port
    port = request[-2] * 256 + request[-1]
    # print(f"IP:{address}  PORT:{port}")

    # 尝试建立连接
    try:
        if cmd == 1:  # CONNECT
            nreader, nwriter = await asyncio.open_connection(remote_adr.encode(), str(remote_port).encode())
            # print(f'Connected to {address} {port}')
            reploy = "\x05\x00\x00".encode() + request[3:]
            # 返回响应报
            writer.write(reploy)
            await writer.drain()
        else:
            # print("Cmd wrong")
            return
    # 连接出错返回错误响应
    except Exception as err:
        # print(err)
        # print("Connection Failed")
        reploy = struct.pack("!BBBBIH", SOCKS_VERSION, 5, 0, address_type, 0, 0)
        # 返回响应报
        writer.write(reploy)
        await writer.drain()
        return

    # requestToRemote = address + b" " + str(port).encode() + b" " + \
    #     str(username).encode() + b" " + str(password).encode()
    # nwriter.write(requestToRemote)
    # # print(f"requestToRemote:{requestToRemote}")
    # await nwriter.drain()

    # reployFromRemote = await nreader.read(4096)
    # # print(f"reployFromRemote:{reployFromRemote}")

    # # 符合条件开始交换数据
    # if reployFromRemote == b"200":
    #     await asyncio.gather(server_client(nreader, writer), client_server(reader, nwriter))
    # elif reployFromRemote == b"404":
    #     print("Connection Failed")
    # elif reployFromRemote == b'303':
    #     print("Authentication failed")
    # print("Close the connection")
    # writer.close()

    connectRemote(address, port, reader, writer, nreader, nwriter)


async def selectProtocol(reader, writer):
    c_header = await reader.read(4096)
    if (len(c_header) <= 5 and c_header[0] == SOCKS_VERSION):
        print("Protocol:socks5")
        await socks_client(reader, writer, c_header)
    else:
        print("Protocol:HTTP")
        await https_client(reader, writer, c_header)


async def main():
    server = await asyncio.start_server(selectProtocol, '127.0.0.1', 8080)
    addr = server.sockets[0].getsockname()
    print(f'Serving on {addr}')
    async with server:
        await server.serve_forever()


parser = argparse.ArgumentParser()
parser.add_argument("-ra", dest="remote_adr", default=b"127.0.0.1")
parser.add_argument("-rp", dest="remote_port", default=b"8848")
parser.add_argument("-u", dest="username")
parser.add_argument("-p", dest="password")
args = parser.parse_args()
username = args.username
password = args.password
remote_adr = args.remote_adr
remote_port = args.remote_port
asyncio.run(main())
