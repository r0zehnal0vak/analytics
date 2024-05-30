import websockets
import aiohttp
import asyncio
from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import StreamingResponse, HTMLResponse, Response
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    # app.
    yield
    # Clean up the ML models and release the resources
    

app = FastAPI(lifespan=lifespan)

# https://gist.github.com/bsergean/bad452fa543ec7df6b7fd496696b2cd8
async def clientToServer(ws: WebSocket, websocket: websockets.WebSocketClientProtocol):
    # async for message in ws.iter_text():
    #     print("client say: ", message)
    #     await websocket.send(message)
    while True:
        data = await ws.receive_bytes()
        print("websocket A received:", data)
        await websocket.send(data)   


async def serverToClient(ws: WebSocket, websocket: websockets.WebSocketClientProtocol):
    async for message in websocket:

        print("server say: ", message)
        # await ws.send_text(message)    
        await ws.send_bytes(message)    

streamlit_port = 8501
@app.get("/{file_path:path}")
async def analysis(request: Request, file_path):
    # authorization = request.cookies.get("authorization", None)
    url = f"http://localhost:{streamlit_port}/{file_path}"
    print(f"streamlit GET {file_path}")
    async with aiohttp.ClientSession() as session:
        # print(headers, cookies)
        async with session.get(url, cookies=request.cookies) as resp:
            print(f"GET {file_path}", resp.status)
            # print(resp.headers)
            # print(resp.content_type)
            # print(resp.content)
            if resp.status != 200:
                print(await resp.text())
            # return StreamingResponse(resp.content)
            buffer = await resp.content.read()
            # print("response", buffer)
            # print("response headers", resp.headers)
            headers = {**resp.headers}
            if "Content-Encoding" in headers:
                del headers["Content-Encoding"]
            if "Transfer-Encoding" in headers:
                del headers["Transfer-Encoding"]
            if "Vary" in headers:
                del headers["Vary"]
            response = Response(
                content=buffer, 
                status_code = resp.status,
                headers = headers)
            return response
            
import logging
wslogger = logging.getLogger("websockets.client")
wslogger.setLevel(logging.DEBUG)

@app.websocket("{file_path:path}")
async def wsscript(websocket: WebSocket, file_path):
    ws_b_uri = f"ws://localhost:{streamlit_port}/{file_path}" #"/_stcore/stream"
    
    headers = dict(websocket.headers.items())
    headers_copy = {
        **headers,
        # "sec-websocket-protocol": headers["sec-websocket-protocol"],
    }
    origin = headers.get("origin", "")
    # print("ws:id, file_path", id, file_path)
    print("ws:headers", headers)
    try:
        async with websockets.connect(ws_b_uri, 
            logger=wslogger, 
            origin=origin,
            # subprotocols=["streamlit, PLACEHOLDER_AUTH_TOKEN"],
            subprotocols=["streamlit"],
            # extensions=["permessage-deflate"],
            extra_headers=headers_copy
        ) as ws_streamlit:
            serverheaders = dict(ws_streamlit.response_headers)
            try:
                await websocket.accept(headers=serverheaders)
            except Exception as ei:
                print("ei", ei)
            taskA = asyncio.create_task(clientToServer(websocket, ws_streamlit))
            taskB = asyncio.create_task(serverToClient(websocket, ws_streamlit))
            await asyncio.gather(taskA, taskB)
    except Exception as e:
        print("exception", e)
