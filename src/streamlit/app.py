import asyncio
import pandas as pd

import streamlit as st
from streamlit_cookies_controller import CookieController

#region little streamlit hacking
from pathlib import Path
import sys
sys.path.append(str(Path(__file__).resolve().parent.parent.parent))

st.set_page_config('Cookie QuickStart', '🍪', layout='wide')

from src.utils import (
    flatten, streamlit_query
)

# if loop is available
def async_to_sync(awaitable):
    loop = asyncio.get_event_loop()
    return loop.run_until_complete(awaitable)

# current state, loop is not available
def async_to_sync(awaitable):
    loop = asyncio.new_event_loop()
    return loop.run_until_complete(awaitable)

#endregion
controller = CookieController()
cookies = controller.getAll()

queryStr = """
{
  result: userPage(
    where: {memberships: {group: {name: {_ilike: "%uni%"}}}}
  ) {
    id
    email
    name
    surname
    
    presences {
      event {
        id
        name
        startdate
        enddate
        eventType {
          id
          name
        }
      }
      presenceType {
        id
        name
      }
    }
  }
}
"""

q = streamlit_query(queryStr)
gqlresponse = async_to_sync(q(variables={}, cookies=cookies))
data = gqlresponse.get("data", {"result": None})
result = data.get("result", None)
assert result is not None, "data are not available"


mappers = {
    "id": "id",
    "name": "name",
    "surname": "surname",
    "email": "email",
    "eventid": "presences.event.id",
    "eventname": "presences.event.name",
    "startdate": "presences.event.startdate",
    "enddate": "presences.event.enddate",
    "eventTypeid": "presences.event.eventType.id",
    "eventTypename": "presences.event.eventType.name",
    "presenceTypeid": "presences.presenceType.id",
    "presenceTypename": "presences.presenceType.name"
}
# l = len(result)
# l
# result
df = pd.DataFrame(result)
st.dataframe(df, use_container_width=True)


pivotinput = list(flatten(result, {}, mappers))
# l = len(pivotinput)
# l
# pivotinput
# data = await getData()
df = pd.DataFrame(pivotinput)
st.dataframe(df, use_container_width=True)