from aiohttp import web

# 1. Нужно ли выводить сообщение о том, что лично ты зашел в чат
# 2. Выводить историю публичных сообщений для новых пользователей
# 3. Отслеживать выход из чата


class WSChat:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.conns = {}

    async def main_page(self, request):
        return web.FileResponse('./index.html')

    async def chat(self, request):
        ws = web.WebSocketResponse()
        await ws.prepare(request)

        async for msg in ws:
            if msg.data == "ping":
                await ws.pong(b"pong")
                continue
            data = msg.json()
            if data['mtype'] == 'INIT':
                _id = data['id']
                self.conns[_id] = ws
                await self.user_enter(_id)
            elif data['mtype'] == 'TEXT':
                id_to = data['to'] if data['to'] else None
                await self.send_msg(data['id'], data['text'], id_to=id_to)

    async def send_msg(self, id_from, text, id_to=None):
        if id_to:
            msg = {
                'mtype': 'DM',
                'id': id_from,
                'text': text
            }
            await self.conns[id_to].send_json(msg)
            return

        for conn in self.conns:
            if conn == id_from:
                continue
            msg = {
                'mtype': 'MSG',
                'id': id_from,
                'text': text
            }
            await self.conns[conn].send_json(msg)

    async def user_enter(self, _id):
        for conn in self.conns:
            msg = {
                'mtype': 'USER_ENTER',
                'id': _id
            }
            await self.conns[conn].send_json(msg)

    async def user_exit(self, _id):
        pass

    def run(self):
        app = web.Application()

        app.router.add_get('/', self.main_page)
        app.router.add_get('/chat', self.chat)

        web.run_app(app, host=self.host, port=self.port)


if __name__ == '__main__':
    WSChat().run()
