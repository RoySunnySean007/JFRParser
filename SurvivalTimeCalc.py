from datetime import datetime
import HOLogParser
import GCLogParser
import os

def main(jfrlogfile, gclogfolder, codeVersion):

    gclogparsingresults = {}
    KVPairToELK = []
    HOdict = HOLogParser.getUniqueHOObjects(jfrlogfile, False)
    for filename in os.listdir(gclogfolder):
        if filename.startswith('gcverbose') and filename.endswith('log'):
            gclogparsingresults[filename] = GCLogParser.parseGCVerboseLog(gclogfolder + os.sep + filename, False)
    #print HOdict
    i = 0
    for HO in HOdict:
        i = i + 1
        HOs = HOdict[HO]['HOs']
        numberOfHOs = HOdict[HO]['Number']

        for key in HOs:
            jfrfilename = key['jfrfilename']
            # jfrfilename example: humongousObject_DC13BIZX5CFAPP03API_vsa3953704_333.jfr
            # corresponding gcverbose log file name example: gcverbose_DC13BIZX5CFAPP03API_vsa3953704_333.log
            gcDelta = ""
            totalSecondsDelta = ""
            liveness = ""
            endTimeStamp = ""
            otherResults = []
            firstGCNumber = 0
            lastGCNumber = 0
            allocationEndTime = key['AllocationEndTime'][:key['AllocationEndTime'].index('.') + 4]
            allocationEndTimeObject = datetime.strptime(allocationEndTime, '%Y-%m-%dT%H:%M:%S.%f')
            gclogfile = jfrfilename.replace('humongousObject', 'gcverbose').replace('jfr', 'log')
            HORegions = gclogparsingresults[gclogfile]
            SizeInB = key['SizeInB']

            for object in HORegions:

                if object['sizeInB'] == SizeInB and (datetime.strptime(object['earlistTimestamp'],
                                                                    '%Y-%m-%dT%H:%M:%S.%f') - allocationEndTimeObject).total_seconds() > 0:
                    gcDelta = int(object['gcnumber']) - int(object['earliestGCnumber']) + 1
                    totalSecondsDelta = (datetime.strptime(object['timestamp'],
                                                           '%Y-%m-%dT%H:%M:%S.%f') - allocationEndTimeObject).total_seconds()
                    liveness = object['liveness']
                    endTimeStamp = object['timestamp']
                    earliestGCnumber = object['earliestGCnumber']
                    firstGCNumber = object['earliestGCnumber']
                    lastGCNumber = object['gcnumber']
                    for tmpobject in HORegions[(HORegions.index(object) + 1):]:
                        if tmpobject['earliestGCnumber'] == earliestGCnumber and tmpobject['sizeInB'] == SizeInB:
                            otherResults.append([(int(tmpobject['gcnumber']) - int(tmpobject['earliestGCnumber']) + 1),
                                                 (datetime.strptime(tmpobject['timestamp'],
                                                                    '%Y-%m-%dT%H:%M:%S.%f') - allocationEndTimeObject).total_seconds(),
                                                 tmpobject['liveness'], tmpobject['earliestGCnumber'], tmpobject['gcnumber']])
                    break
            tmp = {}
            tmp['ID'] = i
            tmp['SizeInB'] = int(SizeInB)
            tmp['NumberOfGCs'] = gcDelta
            tmp['SurvivalTimeInSecond'] = totalSecondsDelta
            tmp['ELKSearchCriteria'] = 'EndTime:"' + key['AllocationEndTime'] + '" AND Servername:"' + jfrfilename.split('_')[1] + '"'
            tmp['AllocationEndTime'] = key['AllocationEndTime']
            tmp['FirstGCNumber'] = int(firstGCNumber)
            tmp['LastGCNumber'] = int(lastGCNumber)
            tmp['Servername'] = jfrfilename.split('_')[1]
            tmp['Hostname'] = jfrfilename.split('_')[2]
            tmp['TomcatPID'] = int(jfrfilename.split('_')[3].split('.')[0])
            tmp['CodeVersion'] = 'B1902'
            tmp['Liveness'] = liveness

            haveSameSurvivalTimeInSecond = False
            if len(otherResults) > 0:
                others = []
                for tmp1 in otherResults:
                    other = {}
                    other['NumberOfGCs'] = tmp1[0]
                    other['SurvivalTimeInSecond'] = tmp1[1]
                    other['Liveness'] = tmp1[2]
                    other['FirstGCNumber'] = int(tmp1[3])
                    other['LastGCNumber'] = int(tmp1[4])
                    if other['SurvivalTimeInSecond'] == tmp['SurvivalTimeInSecond']:
                        haveSameSurvivalTimeInSecond = True
                    else:
                        haveSameSurvivalTimeInSecond = False

                    needAppend = True
                    if other['NumberOfGCs'] == tmp['NumberOfGCs'] and other['SurvivalTimeInSecond'] == tmp['SurvivalTimeInSecond'] and other['Liveness'] == tmp['Liveness'] and other['FirstGCNumber'] ==tmp['FirstGCNumber'] and other['LastGCNumber'] == tmp['LastGCNumber']:
                        needAppend = False
                    for a in others:
                        if a == other:
                            needAppend = False
                    if needAppend:
                        others.append(other)
                if haveSameSurvivalTimeInSecond:
                    tmp['OtherResults'] = []
                else:
                    tmp['OtherResults'] = others
            else:
                tmp['OtherResults'] = []
            tmp['CodeVersion'] = codeVersion
            tmp['GCVerboseLogFile'] = gclogfile
            KVPairToELK.append(tmp)



    for tmp in KVPairToELK:
        needPrint = False
        if tmp['NumberOfGCs'] > 1:
            needPrint = True
        for otherResult in tmp['OtherResults']:
            if otherResult['NumberOfGCs'] > 1:
                needPrint = True
        if needPrint:
            print tmp

    f = open("JFRLog_GCLog_correlation.Log", 'w')

    for kv in KVPairToELK:
        for key in kv:
            if key!='OtherResults':
                f.write(key)
                f.write('=')
                f.write(str(kv[key]))
                f.write(" ")
            else:
                i = 1
                for OtherResult in kv[key]:
                    f.write('OtherResult_' + str(i) + '=')
                    f.write('Liveness: ' + OtherResult['Liveness'] + ",")
                    f.write('FirstGCNumber: ' + str(OtherResult['FirstGCNumber']) + ",")
                    f.write('LastGCNumber: ' + str(OtherResult['LastGCNumber']) + ",")
                    f.write('NumberOfGCs: ' + str(OtherResult['NumberOfGCs']) + ",")
                    f.write('SurvivalTimeInSecond: ' + str(OtherResult['SurvivalTimeInSecond']) + " ")
                    i = i + 1
        f.write('\n')

    f.close


if __name__ == '__main__':
    main('humongousObject.log', 'XXX', 'XXX')
