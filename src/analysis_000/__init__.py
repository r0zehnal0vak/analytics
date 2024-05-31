import json
import re
import pandas as pd
from io import BytesIO
import matplotlib.pyplot as plt

from .getDataFrame import ResolveA01

async def table(variables, cookies):
    df = await ResolveA01(variables, cookies)
    # print(pivotdata, flush=True)

    classes = 'table table-striped table-bordered table-hover table-sm'
    return df.to_html(classes=classes)

async def chart(variables, cookies):
    df = await ResolveA01(variables, cookies)

    df.plot.pie(
        figsize=(40, 20), 
        subplots=True,
        legend=False,
        rotatelabels=True
        )
    with BytesIO() as f:
        plt.savefig(f, format="svg")
        svgresult = f.getvalue().decode()

    return svgresult