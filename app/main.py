import asyncio
import hmac
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Header, HTTPException
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .engine import align
from .models import AlignRequest, AlignResponse
from .provider import Provider, ProviderError, Settings

class BodyLimit:
    def __init__(self, app, limit=131072):
        self.app, self.limit = app, limit

    async def __call__(self, scope, receive, send):
        if scope['type'] != 'http':
            return await self.app(scope, receive, send)
        # Bound bodies even when Content-Length is absent/chunked.
        messages, total = [], 0
        while True:
            message = await receive()
            if message['type'] == 'http.disconnect':
                return
            total += len(message.get('body', b''))
            if total > self.limit:
                return await JSONResponse({'detail': {'code': 'request_too_large'}}, status_code=413)(scope, receive, send)
            messages.append(message)
            if not message.get('more_body', False):
                break
        async def replay():
            return messages.pop(0) if messages else await receive()
        await self.app(scope, replay, send)

def create_app(settings=None, provider_override=None):
    @asynccontextmanager
    async def lifespan(app):
        app.state.settings = settings or Settings.from_env()
        async with httpx.AsyncClient(follow_redirects=False, limits=httpx.Limits(max_connections=20)) as client:
            app.state.provider = provider_override or Provider(app.state.settings, client)
            app.state.semaphore = asyncio.Semaphore(4)
            yield

    app = FastAPI(title='SANA Premise Alignment API', version='0.1.0', description='Powered by SANA OS — https://sana-os.org/ — workflow premise mapping profile', lifespan=lifespan)
    app.add_middleware(BodyLimit)

    @app.exception_handler(RequestValidationError)
    async def validation_error(request, exc):
        # FastAPI's default includes the rejected input. Avoid returning submitted private data.
        return JSONResponse({'detail': {'code': 'invalid_request', 'errors': [
            {'loc': e['loc'], 'type': e['type']} for e in exc.errors()
        ]}}, status_code=422)

    @app.get('/healthz')
    async def health():
        return {'status': 'ok', 'provider_connectivity': 'not_checked'}

    @app.post('/v1/align', response_model=AlignResponse)
    async def endpoint(req: AlignRequest, authorization: str | None = Header(default=None)):
        token = app.state.settings.service_token
        if token and not hmac.compare_digest((authorization or '').encode(), ('Bearer ' + token).encode()):
            raise HTTPException(401, detail={'code': 'unauthorized'})
        try:
            async with asyncio.timeout(app.state.settings.timeout * 2 + 5):
                async with app.state.semaphore:
                    return await align(req, app.state.provider)
        except TimeoutError:
            raise HTTPException(504, detail={'code': 'alignment_timeout'}) from None
        except ProviderError as e:
            raise HTTPException(e.status, detail={'code': e.code}) from None

    return app

app = create_app()
