import re
import os
import shutil

# Return unique humongous objects from jfr log 'humongousObject.log' from JFRParser.java

def getUniqueHOObjects(jfrlogfile, needHTMLFile):
    f = open(jfrlogfile, 'rU')
    HOlist = []
    HOdict = {}
    i = -1
    for line in f:
        match = re.search(r'([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]*)\s\sSizeInMB=([0-9.]*)\sSizeInB=([0-9.]*)\sClass=(.*)\sThread=(.*)\sEndTime=([0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}\.[0-9]*)\sJfrfile=([\w\.\-_\d]*)\sHost=([\w]*)\sStacktrace=(.*\n)', line)

        if match:
            i = i + 1
            HO = {}
            HO['AllocationEndTime'] = match.group(1)
            HO['SizeInB'] = match.group(3)
            HO['jfrfilename'] = match.group(7)
            HO['Host'] = match.group(8)
            HO['Stacktrace'] = []
            HO['Stacktrace'].append(match.group(9))
            HOlist.append(HO)
        else:
            HOlist[i]['Stacktrace'].append(line)
    f.close()

    for HO in HOlist:
        key = ''.join(HO['Stacktrace'])
        if key in HOdict:
            HOdict[key]['Number'] = HOdict[key]['Number'] + 1
            tmp = {}
            tmp['AllocationEndTime'] = HO['AllocationEndTime']
            tmp['SizeInB'] = HO['SizeInB']
            tmp['jfrfilename'] = HO['jfrfilename']
            tmp['Host'] = HO['Host']
            HOdict[key]['HOs'].append(tmp)
        else:
            HOdict[key] = {}
            HOdict[key]['Number'] = 1
            HOdict[key]['HOs'] = []
            tmp = {}
            tmp['AllocationEndTime'] = HO['AllocationEndTime']
            tmp['SizeInB'] = HO['SizeInB']
            tmp['jfrfilename'] = HO['jfrfilename']
            tmp['Host'] = HO['Host']
            HOdict[key]['HOs'].append(tmp)

    if needHTMLFile:
        path = os.path.dirname(os.path.abspath(jfrlogfile)) + os.sep + 'html'
        if os.path.exists(path):
            shutil.rmtree(path)

        os.mkdir(path)
        f = open(path + os.sep + 'index.html', 'w')
        f.write('<html><body>\n')
        f.write('<h1>There are totally ' + str(len(HOlist)) + ' humongous objects. And have ' + str(len(HOdict)) + ' sources with different stacktrace. </h1><br>')
        i = 1
        for key in HOdict:
            tmp = path + os.sep + 'Source' + str(i)
            f1 = open(tmp + '.html', 'w')
            tmpList = key.split('\n')
            list2 = []
            for tmpitem in tmpList:
                temp = tmpitem.replace('<', '&lt;').replace('>', '&gt;')
                if temp.find('successfactors') != -1:
                    temp = '<font color="blue">' + temp + '</font>'
                list2.append(temp)
            f1.write("<h1>Humongous Objects:</h1>")
            for HO in HOdict[key]['HOs']:
                f1.write('<font color="green">AllocationEndTime</font>=' + HO['AllocationEndTime'])
                f1.write(' <font color="green">SizeInB</font>=' + HO['SizeInB'])
                f1.write(' <font color="green">Host</font>=' + HO['Host'])
                f1.write(' <font color="green">jfrfilename</font>=' + HO['jfrfilename'] + '<br>')
            f1.write("<h1>StackTrace:</h1>")
            for lt in list2:
                f1.write(lt)
                f1.write('<br>')
            f1.close()
            f.write('<a href="' + tmp + '.html">' + os.path.basename(tmp) + '</a>: ' + str(HOdict[key]['Number']) + ' # of humongous objects<br>')
            i = i + 1
        f.write('\n</body></html>\n')
        f.close()

    return HOdict
