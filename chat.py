from aiohttp import web


class WSChat:
    def __init__(self, host='0.0.0.0', port=8080):
        self.host = host
        self.port = port
        self.conns = {}

    async def main_page(self, request):
        return web.FileResponse('./index.html')

    async def chat(self, request):
        ws = web.WebSocketResponse(autoclose=False)
        try:
            await ws.prepare(request)
        except web.HTTPException:
            # Отправлять ошибку HTTP
            pass

        async for msg in ws:
            if msg.data == "ping":
                await ws.pong(b"pong")
                continue
            data = msg.json()
            if data['mtype'] == 'INIT':
                _id = data['id']
                self.conns[_id] = ws
                await self.user_enter(_id)
                await self.db.messages()
            elif data['mtype'] == 'TEXT':
                id_to = data['to'] if data['to'] and data['to'] in self.conns else None
                await self.send_msg(data['id'], data['text'], id_to=id_to)

        await self.user_exit(ws)

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

    async def user_exit(self, exit_conn):
        exit_id = self.get_id_by_conn(exit_conn)
        for conn in self.conns:
            if conn == exit_id:
                continue
            msg = {
                'mtype': 'USER_LEAVE',
                'id': exit_id
            }
            await self.conns[conn].send_json(msg)
        await exit_conn.close()
        del self.conns[exit_id]

    def get_id_by_conn(self, conn):
        for _conn in self.conns:
            if self.conns[_conn] == conn:
                return _conn

    def run(self):
        app = web.Application()

        app.router.add_get('/', self.main_page)
        app.router.add_get('/chat', self.chat)

        web.run_app(app, host=self.host, port=self.port)


if __name__ == '__main__':
    WSChat().run()
