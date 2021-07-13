import asyncio
remote_adr = "127.0.0.1"
remote_port = "8888"


async def tcp_echo_client(message):
    reader, writer = await asyncio.open_connection(
        remote_adr, remote_port)
    print(f'Send: {message!r}')
    writer.write(message.encode())
    data = await reader.read(100)
    print(f'Received: {data.decode()!r}')
    print('Close the connection')
    writer.close()
    
asyncio.run(tcp_echo_client('Hello World!'))
