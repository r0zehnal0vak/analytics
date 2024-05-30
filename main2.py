from fastapi import FastAPI, Request, WebSocket
from fastapi.responses import HTMLResponse, Response
from contextlib import asynccontextmanager
import aiohttp
import json

import pandas as pd
import re

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load the ML model
    # app.
    yield
    # Clean up the ML models and release the resources
       
async def queryGQL(request, query, variables):
    # gqlurl = "http://host.docker.internal:33001/api/gql"
    gqlurl = "http://localhost:33001/api/gql"
    
    payload = {"query": query, "variables": variables}
    cookies = request.cookies
    async with aiohttp.ClientSession() as session:
        # print(headers, cookies)
        async with session.post(gqlurl, json=payload, cookies=cookies) as resp:
            # print(resp.status)
            if resp.status != 200:
                text = await resp.text()
                print(text, flush=True)
                raise Exception(f"Unexpected GQL response", text)
            else:
                text = await resp.text()
                # print(text, flush=True)
                response = await resp.json()
                # print(response, flush=True)
                return response


async def ResolveA01(request):

    q="""
query ($where: GroupInputWhereFilter) {
  result: groupPage(limit: 10000, where: $where) {
    id
    name
    grouptype {
      id
      name
    }
    memberships(limit: 1000) {
      user {
        id
        email
      }
    }
  }
}
"""

    params = request.query_params
    variables = dict(params)
    if "where" in variables:
        wherevalue = variables["where"]
        wherevalue = re.sub(r'{([^:"]*):', r'{"\1":', wherevalue)
        print(wherevalue)
        variables["where"] = json.loads(wherevalue)
    print("variables", variables, flush=True)
    jsonresponse = await queryGQL(
        request=request,
        query=q,
        variables=variables
        )
    
    data = jsonresponse.get("data", {"result": None})
    result = data.get("result", None)
    assert result is not None, f"got {jsonresponse}"
    # print(result, flush=True)

    mapped = [{**group} for group in result]
    # print(mapped, flush=True)
    mapper = {
        "group_name": "name",
        "group_id": "id",
        "user": "memberships.user.email"
    }

    from src.utils import flatten
    
    pivotdata = list(flatten(mapped, {}, mapper))
    print(pivotdata)
    df = pd.DataFrame(pivotdata)

    pdf = pd.pivot_table(df, values="user", index="group_name", columns=[], aggfunc="count")

    return pdf

app = FastAPI(lifespan=lifespan)

@app.get("/analysis/table")
async def analyse(request: Request):
    template = """
<link href="https://stackpath.bootstrapcdn.com/bootstrap/4.4.1/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-Vkoo8x4CGsO3+Hhxv8T/Q5PaXtkKtu6ug5TOeNV6gBiFeWPGFN9MuhOf23Q9Ifjh" crossorigin="anonymous">
<style>
th {
    background: #2d2d71;
    color: white;
    text-align: left;
}
</style>
<body>
%s
</body>
"""

    df = await ResolveA01(request)
    # print(pivotdata, flush=True)

    classes = 'table table-striped table-bordered table-hover table-sm'
    html = template % df.to_html(classes=classes)    
    # html = df.to_html()
    # print(html, flush=True)
    return HTMLResponse(html)


from io import BytesIO
import matplotlib.pyplot as plt
@app.get("/analysis/figure")
async def analyse(request: Request):

    df = await ResolveA01(request)

    plot = df.plot.pie(
        figsize=(40, 20), 
        subplots=True,
        legend=False,
        rotatelabels=True
        )
    with BytesIO() as f:
        plt.savefig(f, format="svg")
        svgresult = f.getvalue().decode()
        print(svgresult[:1000])
    lines = svgresult.split('\n')

    return HTMLResponse('\n'.join(lines[3:]))