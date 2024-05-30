from itertools import product
from functools import reduce

def enumerateAttrs(attrs):
    for key, value in attrs.items():
        names = value.split(".")
        name = names[0]
        yield key, name

def flattenList(inList, outItem, attrs):
    for item in inList:
        assert isinstance(item, dict), f"in list only dicts are expected"
        for row in flatten(item, outItem, attrs):
            # print("flatList", row)
            yield row
            
def flattenDict(inDict, outItem, attrs):
    result = {**outItem}
    # print("flatDict.result", result)
    complexAttrs = []
    for key, value in enumerateAttrs(attrs):
        attributeValue = inDict.get(value, None)
        if isinstance(attributeValue, list):
            complexAttrs.append((key, value))
        elif isinstance(attributeValue, dict):
            complexAttrs.append((key, value))
        else:
            result[key] = attributeValue
    lists = []
    for key, value in complexAttrs:
        attributeValue = inDict.get(value, None)
        prefix = f"{value}."
        prefixlen = len(prefix)
        subAttrs = {key: value[prefixlen:] for key, value in attrs.items() if value.startswith(prefix)}
        items = list(flatten(attributeValue, result, subAttrs))
        lists.append(items)
                     
    if len(lists) == 0:
        yield result
    else:
        for element in product(*lists):
            reduced = reduce(lambda a, b: {**a, **b}, element, {})
            yield reduced
        
def flatten(inData, outItem, attrs):
    if isinstance(inData, dict):
        for item in flattenDict(inData, outItem, attrs):
            yield item
    elif isinstance(inData, list):
        for item in flattenList(inData, outItem, attrs):
            yield item
    else:
        assert False, f"Unexpected type on inData {inData}"