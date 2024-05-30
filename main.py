import websockets
import aiohttp
import asyncio
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, Response
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager

import panel as pn
from bokeh.embed import server_document


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    # app.
    yield
    # Clean up the ML models and release the resources
    

app = FastAPI(lifespan=lifespan)
templates = Jinja2Templates(directory="templates")

@app.get("/analysis/{id}")
async def analysis(request: Request, id):
    authorization = request.cookies.get("authorization", None)
    print(authorization)
    script = server_document(f"http://127.0.0.1:8000/analysis_query/{id}")
    # script = server_document(f"http://127.0.0.1:{pn_server_port}/analysis_query/{id}")
    return templates.TemplateResponse(
        "base.html", {"request": request, "script": script}
    )

@app.get("/")
async def index(request: Request):
    result = """<!DOCTYPE html>
<html>
<head>
<title>Analysis Index</title>
</head><body><a href='/analysis/0'>analysis/0</a></body></html>"""
    return HTMLResponse(result)

##
# proxies to http://app:5000
# https://fastapi.tiangolo.com/tutorial/path-params/
##
@app.get("/analysis_query/{id}/{file_path:path}")
async def script(request: Request, id, file_path):
    params = request.query_params # https://stackoverflow.com/questions/62279710/fastapi-variable-query-parameters
    url = f'http://127.0.0.1:{pn_server_port}/analysis_query/{id}/{file_path}?{params}'
    print("request", url)
    headers = request.headers
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as _response:
            buffer = await _response.content.read()
            print("response", buffer)
            response = Response(
                content=buffer, 
                status_code=_response.status,
                headers=_response.headers)
    return response

@app.get("/static/{file_path:path}")
async def static(request: Request, file_path):
    params = request.query_params # https://stackoverflow.com/questions/62279710/fastapi-variable-query-parameters
    url = f'http://127.0.0.1:{pn_server_port}/static/{file_path}?{params}'
    print("request", url)
    headers = request.headers
    async with aiohttp.ClientSession() as session:
        async with session.get(url, headers=headers) as _response:
            buffer = await _response.content.read()
            # print("response", buffer)
            response = Response(
                content=buffer, 
                status_code=_response.status,
                headers=_response.headers)
    return response

##
# proxies to ws://app:5000
# https://fastapi.tiangolo.com/advanced/websockets/
# https://stackoverflow.com/questions/65361686/websockets-bridge-for-audio-stream-in-fastapi
##

async def ws_binary(ws_a: WebSocket, ws_b: websockets.WebSocketClientProtocol):
    while True:
        data = await ws_a.receive_bytes()
        print("websocket A received:", data)
        await ws_b.send(data)

async def ws_text(ws_a: WebSocket, ws_b: websockets.WebSocketClientProtocol):
    while True:
        data = await ws_b.recv()
        if isinstance(data, str):
            await ws_a.send_text(data)
        elif isinstance(data, bytes):
            await ws_a.send_bytes(data)
        else:
            print("??", data)
        print("websocket A sent:", data)

async def ws_text(ws_a: WebSocket, ws_b: websockets.WebSocketClientProtocol):
    while True:
        data = await ws_b.read_message()
        await ws_a.send_bytes(data)
        print("websocket A sent:", data)



async def forward(ws_a: WebSocket, ws_b: websockets.WebSocketClientProtocol):
    while True:
        data = await ws_a.receive_bytes()
        print("websocket A received:", data)
        await ws_b.send(data)


async def reverse(ws_a: WebSocket, ws_b: websockets.WebSocketClientProtocol):
    while True:
        data = await ws_b.recv()
        await ws_a.send_text(data)
        print("websocket A sent:", data)


# https://gist.github.com/bsergean/bad452fa543ec7df6b7fd496696b2cd8
async def clientToServer(ws: WebSocket, websocket):
    async for message in ws.iter_text():
        await websocket.send(message)


async def serverToClient(ws: websockets.ClientProtocol, websocket):
    async for message in websocket:
        await ws.send_text(message)        

import logging
wslogger = logging.getLogger("websockets.client")
wslogger.setLevel(logging.DEBUG)


async def _forward(
    client: WebSocket, target: websockets.WebSocketClientProtocol
) -> None:
    async for message in client.iter_bytes():
        await target.send(message)


async def _reverse(
    client: WebSocket, target: websockets.WebSocketClientProtocol
) -> None:
    async for message in target:
        await client.send_text(message)

from reverseproxy import WebSocketProxy
@app.websocket("/analysis_query/{id}/{file_path:path}")
async def wsscript0(websocket: WebSocket, id, file_path):
    ws_b_uri = f"ws://127.0.0.1:{pn_server_port}/analysis_query/{id}/{file_path}"
    headers = dict(websocket.headers.items())
    try:
        async with websockets.connect(ws_b_uri, 
            logger=wslogger,
            subprotocols=["bokeh"],
            extra_headers=headers
        ) as target:
            
            await websocket.accept()
            _forward_task = asyncio.create_task(
                _forward(websocket, target)
            )
            _reverse_task = asyncio.create_task(
                _reverse(websocket, target)
            )
            await asyncio.gather(_forward_task, _reverse_task)
    except Exception as ee:
        print('ee', ee)

    # ws_proxy = WebSocketProxy(websocket, ws_b_uri)
    # await ws_proxy(subprotocols=["bokeh"])

#@app.websocket("/analysis_query/{id}/{file_path:path}")
async def wsscript(websocket: WebSocket, id, file_path):
    ws_b_uri = f"ws://127.0.0.1:{pn_server_port}/analysis_query/{id}/{file_path}"
    headers = dict(websocket.headers.items())
    headers_copy = {
        **headers,
        # "sec-websocket-protocol": headers["sec-websocket-protocol"],
    }
    origin = headers.get("origin", None)
    print("ws:id, file_path", id, file_path)
    print("ws:headers", headers)
    try:
        async with websockets.connect(
            ws_b_uri, 
            logger=wslogger,
            origin=origin,
            extra_headers=headers_copy, 
            subprotocols=["bokeh"]
        ) as ws_bokeh:
            serverheaders = dict(ws_bokeh.response_headers)
            print("serverheaders", serverheaders)
            try:
                await websocket.accept(headers=serverheaders)
            except Exception as ei:
                print("ei", ei)

            taskA = asyncio.create_task(clientToServer(websocket, ws_bokeh))
            taskB = asyncio.create_task(serverToClient(websocket, ws_bokeh))
            await asyncio.gather(taskA, taskB)
    except Exception as e:
        print('e', e)


    # await websocket.accept()
    # async with websockets.connect(ws_b_uri) as ws_b_client:
    #     fwd_task = asyncio.create_task(forward(websocket, ws_b_client))
    #     rev_task = asyncio.create_task(reverse(websocket, ws_b_client))
    #     await asyncio.gather(fwd_task, rev_task)


        # fwd_task = asyncio.create_task(ws_binary(websocket, ws_b_client))
        # rev_task = asyncio.create_task(ws_binary(ws_b_client, websocket))
        # fwd_task = asyncio.create_task(ws_text(websocket, ws_b_client))
        # rev_task = asyncio.create_task(ws_text(websocket, ws_b_client))
        # await asyncio.gather(fwd_task, rev_task)
        
    # while True:
    #     data = await websocket.receive_text()
    #     await websocket.send_text(f"Message text was: {data}")

pn_server_port = 5000
##
# app on port 5000
##
from src.analysis_001 import createApp
pn.serve(
    {
        "/analysis_query/0": createApp,
        "/app": "./src/analysis_101/app.ipynb",
        "/analysis/presences": "./src/analysis_101/query_presences_.ipynb",
    },
    address="127.0.0.1",
    port=pn_server_port,
    show=False,

    # websocket_origin=
    # static_dirs={'assets': './assets'},
    # allow_websocket_origin=["127.0.0.1:8000"],
)