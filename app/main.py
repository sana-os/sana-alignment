import asyncio
import hmac
from contextlib import asynccontextmanager
import httpx
from fastapi import FastAPI, Header, HTTPException, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from .engine import align, KNOWLEDGE_HASH
from .run_trace import ACTIVE_TRACE, RunTrace, TraceStore, save_trace
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
            app.state.trace_store = TraceStore(app.state.settings.trace_dir)
            yield

    app = FastAPI(title='SANA Premise Alignment API', version='0.5.15', description='Powered by SANA OS — https://sana-os.org/ — workflow premise mapping profile', lifespan=lifespan)
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
    async def endpoint(req: AlignRequest, response: Response, authorization: str | None = Header(default=None)):
        token = app.state.settings.service_token
        if token and not hmac.compare_digest((authorization or '').encode(), ('Bearer ' + token).encode()):
            raise HTTPException(401, detail={'code': 'unauthorized'})
        settings = app.state.settings
        trace = RunTrace(req, settings, app.version, KNOWLEDGE_HASH)
        token = ACTIVE_TRACE.set(trace if settings.trace_level != 'off' else None)
        result, error, status = None, None, 500
        try:
            async with asyncio.timeout(settings.timeout * 2 + 5):
                async with app.state.semaphore:
                    result = await align(req, app.state.provider, mapping_retries=trace.retries,
                        mapping_attempts=trace.attempts, request_id=trace.request_id)
        except asyncio.CancelledError:
            error = {'code': 'alignment_cancelled'}
            raise
        except TimeoutError:
            error, status = {'code': 'alignment_timeout'}, 504
        except ProviderError as e:
            error, status = {'code': e.code}, e.status
            if e.issue is not None:
                error['issue'] = e.issue
        finally:
            ACTIVE_TRACE.reset(token)
            saved = save_trace(app.state.trace_store, trace, trace.finish(result, error))
        headers = {'X-SANA-Request-ID': trace.request_id,
                   'X-SANA-Processing-Mode': trace.mode, 'X-SANA-Trace-Status': saved}
        if error is not None:
            return JSONResponse({'detail': error}, status_code=status, headers=headers)
        response.headers.update(headers)
        return result

    return app

app = create_app()
