from src.utils import flatten, queryGQL


async def ResolveA01(variables, cookies):

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

    jsonresponse = await queryGQL(
        query=q,
        variables=variables,
        cookies=cookies
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

    pivotdata = list(flatten(mapped, {}, mapper))
    print(pivotdata)
    df = pd.DataFrame(pivotdata)

    pdf = pd.pivot_table(df, values="user", index="group_name", columns=[], aggfunc="count")

    return pdf