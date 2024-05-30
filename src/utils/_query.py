import aiohttp
from fastapi import Request

def fastapi_query(q, gqlurl = "http://host.docker.internal:33001/api/gql"):
    async def post(request: Request, variables: dict):
        payload = {"query": q, "variables": variables}
        # headers = {"Authorization": f"Bearer {token}"}
        # cookies = {'authorization': token}
        cookies = request.cookies
        async with aiohttp.ClientSession() as session:
            # print(headers, cookies)
            async with session.post(gqlurl, json=payload, cookies=cookies) as resp:
                # print(resp.status)
                if resp.status != 200:
                    print(await resp.text())
                else:
                    response = await resp.json()
                    return response
    return post

def streamlit_query(q, gqlurl = "http://host.docker.internal:33001/api/gql"):
    async def post(variables: dict={}, cookies: dict={}):
        payload = {"query": q, "variables": variables}
        # headers = {"Authorization": f"Bearer {token}"}
        # cookies = {'authorization': token}
        
        async with aiohttp.ClientSession() as session:
            # print(headers, cookies)
            async with session.post(gqlurl, json=payload, cookies=cookies) as resp:
                # print(resp.status)
                if resp.status != 200:
                    print(await resp.text())
                else:
                    response = await resp.json()
                    return response
    return post