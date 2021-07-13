# import asyncio


# async def tcp_echo_client():
#     # while True:
#     reader, writer = await asyncio.open_connection('127.0.0.1', 8888)
#     message = input("Send message:")
#     # print(f'Send: {message!r}')
#     writer.write(message.encode())
#     data = await reader.read(100)
#     print(f'Received: {data.decode()!r}')
#     print('Close the connection')
#     writer.close()


# asyncio.run(tcp_echo_client())

import asyncio
import socket as soc
import struct

async def tcp_echo_client():
    reader, writer = await asyncio.open_connection(
        '127.0.0.1', 8888)
    client_method="\x05\x01\x00"#method=00，无认证连接
    writer.write(client_method.encode())
    await writer.drain()
    server_choose=await reader.read(100)
    print(server_choose)
    if(server_choose[1]==0):
        ip="220.181.38.148"
        port="443"
        request_goal="\x05\x01\x00\x01".encode()+soc.inet_aton(ip)+struct.pack('H',443)
        writer.write(request_goal)
        await writer.drain()
    reploy=await reader.read(100)
    print(f"reploy:{reploy}")
    print('Close the connection')
    writer.close()

asyncio.run(tcp_echo_client())
