import re
import os

# Purpose: Data mining of G1TraceEagerReclaimHumongousObjects. Get the following list:
#For humongous region which reclaimed by G1 GC, persist its last info in gcverbose log (when it is reclaimed, during which GC it is reclaimed, etc)
#For humongous region which is still live, persist its last info in gcverbose log

def MyFn(s):
    return s['timestamp']

def MyFnEarliestTimeStamp(s):
    return s['earlistTimestamp']

def parseGCVerboseLog(gclogfile, needParsingResult):
    f = open(gclogfile, 'rU')
    G1TraceEagerReclaimHumongousObjects = []

    for line in f:
        match = re.search(r'([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]{3})\+([0-9]{4}):\s[0-9\.]*:\s#([0-9]+):\s\[GC pause.*', line)
        if match:
            timestamp = match.group(1)
            timezone = match.group(2)
            gcnumber = match.group(3)
        else:
            G1TraceEagerReclaimHumongousObject = {}
            eagerReclaimHumongousObjectsMatch = re.search(r'(Live|Dead)\shumongous\sregion\s([0-9]+)\ssize\s([0-9]+)\sstart\s([0-9a-zA-Z]*)\slength\s([0-9]*)\swith\sremset\s([0-9]*)\scode\sroots\s([0-9]*)\sis\smarked\s([0-9]*)\sreclaim\scandidate\s([0-9]*)\stype\sarray\s([0-9]*)', line)
            if eagerReclaimHumongousObjectsMatch:
                G1TraceEagerReclaimHumongousObject['timestamp'] = timestamp
                G1TraceEagerReclaimHumongousObject['timezone'] = timezone
                G1TraceEagerReclaimHumongousObject['gcnumber'] = gcnumber
                G1TraceEagerReclaimHumongousObject['liveness'] = eagerReclaimHumongousObjectsMatch.group(1)
                G1TraceEagerReclaimHumongousObject['regionIdx'] = eagerReclaimHumongousObjectsMatch.group(2)
                G1TraceEagerReclaimHumongousObject['sizeInB'] = eagerReclaimHumongousObjectsMatch.group(3)
                G1TraceEagerReclaimHumongousObject['startAddressInMemory'] = eagerReclaimHumongousObjectsMatch.group(4)
                G1TraceEagerReclaimHumongousObject['regionLength'] = eagerReclaimHumongousObjectsMatch.group(5)
                G1TraceEagerReclaimHumongousObject['remset'] = eagerReclaimHumongousObjectsMatch.group(6)
                G1TraceEagerReclaimHumongousObject['codeRoot'] = eagerReclaimHumongousObjectsMatch.group(7)
                G1TraceEagerReclaimHumongousObject['isMarked'] = eagerReclaimHumongousObjectsMatch.group(8)
                G1TraceEagerReclaimHumongousObject['isHumongousReclaimCandidate'] = eagerReclaimHumongousObjectsMatch.group(9)
                G1TraceEagerReclaimHumongousObject['isTypeArray'] = eagerReclaimHumongousObjectsMatch.group(10)

                G1TraceEagerReclaimHumongousObjects.append(G1TraceEagerReclaimHumongousObject)
    sortedList = sorted(G1TraceEagerReclaimHumongousObjects, key=MyFn)

    i = 0
    while i < len(sortedList):
        tmp = sortedList[i]

        if tmp['liveness'] == 'Live':
            liveness = False
            a = ""
            earliestTimestamp = tmp['timestamp']
            earliestGCnumber = tmp['gcnumber']
            for temp in sortedList[(i+1):]:
                if temp['liveness'] == 'Dead' and temp['regionIdx'] == tmp['regionIdx']:
                    sortedList.remove(tmp)
                    liveness = False
                    if i > 0:
                        i = i - 1
                    sortedList[sortedList.index(temp)]['earlistTimestamp'] = earliestTimestamp
                    sortedList[sortedList.index(temp)]['earliestGCnumber'] = earliestGCnumber
                    break
                elif temp['liveness'] == 'Live' and temp['regionIdx'] == tmp['regionIdx']:
                    liveness = True
                    a = temp
                    sortedList.remove(temp)
                    if i > 0:
                        i = i - 1
            if liveness:
                a['earlistTimestamp'] = earliestTimestamp
                a['earliestGCnumber'] = earliestGCnumber
                sortedList[sortedList.index(tmp)] = a
        else:
            sortedList[i]['earlistTimestamp'] = sortedList[i]['timestamp']
            sortedList[i]['earliestGCnumber'] = sortedList[i]['gcnumber']
        i = i + 1

    f.close()

    if needParsingResult:
        absPath = os.path.abspath(gclogfile)
        parsingResult = os.path.dirname(absPath) + os.sep + os.path.basename(absPath) + '.parsingresult'
        if os.path.exists(parsingResult):
            os.remove(parsingResult)
        f1 = open(parsingResult, 'w')
        for tmp in sortedList:
            i = 0
            for key in tmp:
                f1.write(key)
                f1.write('=')
                f1.write(tmp[key])
                i = i + 1
                if i == len(tmp):
                    f1.write('\n')
                else:
                    f1.write(' ')
        f1.close()
    return sortedList


''' Comment
Sample of humongous object related GC log
Live humongous region 238 size 9175064 start 0x00007f9875000000 length 1 with remset 0 code roots 0 is marked 0 reclaim candidate 0 type array 1
Dead humongous region 119 size 8388632 start 0x00007f97fe000000 length 1 with remset 1 code roots 0 is marked 0 reclaim candidate 0 type array 0
'''
