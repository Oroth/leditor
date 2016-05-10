

def cycleThroughList(option, list):
    currentListPos = list.index(option)
    return list[(currentListPos + 1) % len(list)]