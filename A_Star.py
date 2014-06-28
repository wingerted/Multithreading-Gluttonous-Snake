import Queue

STEPS = ((1, 0), (0, 1), (-1, 0), (0, -1))
WIDTH = 500
HEIGHT = 500

def NextNode(tableMap, step, parent, end):
    currentNode = {
        'current' : (parent["current"][0]+step[0], parent["current"][1]+step[1]),
        'value_f' : 0,
        'value_h' : 0,
        'value_g' : parent["value_g"] + 1,
        'parent'  : parent
    }
    currentNode["value_h"] = abs(end["current"][0] - currentNode["current"][0]) + abs(end["current"][1] - currentNode["current"][1])
    currentNode["value_f"] = currentNode["value_h"] + currentNode["value_g"]

    if 0 <= currentNode['current'][0] < WIDTH and \
       0 <= currentNode['current'][1] < HEIGHT and \
       tableMap[currentNode['current'][0]][currentNode['current'][1]] == 0:
        return currentNode
    else:
        return None


    
def A_Star_Search(tableMap, visited, start, end):
    start["value_h"] = abs(end["current"][0] - start["current"][0]) + abs(end["current"][1] - start["current"][1])
    start["value_f"] = start["value_h"] + start["value_g"]
    openList = []
    openList.append(start)
    
    while len(openList) != 0:
        #current = min(openList, key=lambda node : node["value_f"])
        #openList.remove(current)
        openList.sort(key=lambda node : node["value_f"])
        current = openList.pop(0)

        for step in STEPS:
            next = NextNode(tableMap, step, current, end)
            if next != None and visited[next["current"][0]][next["current"][1]] == False:
                flag = False
                for item in openList:
                    if item["current"] == next["current"]:
                        flag = True
                        
                        if item["value_g"] < next["value_g"]:
                            item["value_f"] = next["value_f"]
                            item["value_h"] = next["value_h"]
                            item["value_g"] = next["value_g"]
                            item["parent"] = next["parent"]
                        break
                
                if flag == False:
                    openList.append(next)

        if current["current"] == end["current"]:
            end["parent"] = current["parent"]
            return

        visited[current["current"][0]][current["current"][1]] = True
    

def main():
    tableMap = [[0 for i in range(WIDTH)] for j in range(HEIGHT)]
    visitedMap = [[False for i in range(WIDTH)] for j in range(HEIGHT)]

    tableMap[2][0] = tableMap[2][1] =tableMap[2][2] =tableMap[1][2] = tableMap[0][2] = -1
    
    endNode = {
        'current' : (300, 300),
        'value_f' : 0,
        'value_h' : 0,
        'value_g' : 0,
        'parent'  : None
    }

    startNode = {
        'current' : (0, 0),
        'value_f' : 0,
        'value_h' : 0,
        'value_g' : 0,
        'parent'  : None
    }

    A_Star_Search(tableMap, visitedMap, startNode, endNode)

    result = endNode
    while (result["parent"] != None):
        print(result["current"])
        result = result["parent"]
    
    
if __name__ == '__main__':
    main()
