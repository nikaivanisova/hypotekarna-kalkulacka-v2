"""Request body size limit, enforced before parsing (api/openapi.yaml; review 03 #5).

A declared Content-Length over the limit is refused at once; a streamed (chunked) body is
counted as it arrives and refused as soon as it passes the limit.
"""
from starlette.exceptions import HTTPException
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from mortgage.api.problems import problem

MAX_BODY_BYTES = 1024


class BodySizeLimitMiddleware:
    def __init__(self, app: ASGIApp, max_bytes: int = MAX_BODY_BYTES) -> None:
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope['type'] != 'http':
            await self.app(scope, receive, send)
            return

        declared = dict(scope['headers']).get(b'content-length')
        if declared is not None:
            if not declared.isdigit():
                await problem(400)(scope, receive, send)
                return
            if int(declared) > self.max_bytes:
                await problem(413)(scope, receive, send)
                return

        received = 0

        async def limited_receive() -> Message:
            nonlocal received
            message = await receive()
            if message['type'] == 'http.request':
                received += len(message.get('body', b''))
                if received > self.max_bytes:
                    raise HTTPException(413)  # turned into a problem response by the HTTP handler
            return message

        await self.app(scope, limited_receive, send)
