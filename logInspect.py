# ------------------------------------------------------------------------
# -- DISCLAIMER:
# --    This script is provided for educational purposes only. It is NOT
# --    supported by Rubicon Red.
# --    The script has been tested and appears to work as intended.
# --    You should always run new scripts on a test instance initially.
# --
# ------------------------------------------------------------------------

import requests
import getpass
import json
import os
import sys
import time
import math

def getServerJson(url, username, password):
    try:
        response = requests.get(url, auth=(username, password))
        if response.status_code != requests.codes.ok:
            print()
            print("Error connecting to WLS Server!")
            print("HTTP Error code = " + str(response.status_code))
            print("URL  = "+url)
            sys.exit(1)
    except requests.exceptions.Timeout as e:
        print(e)
        sys.exit(1)
    except requests.exceptions.HTTPError as e:
        print(e)
        sys.exit(1)
    except requests.exceptions.RequestException as e:
        # catastrophic error. bail.
        print(e)
        sys.exit(1)
    return json.loads(response.text)

#Get a list of all of the Admin and Managed Servers in the domain
def getServers(wlsDomain,wlsServerUrl,username,password ):
    url = 'http://'+wlsServerUrl+'/management/wls/latest/servers'
    serverJson = getServerJson(url, username, password)
    for server in serverJson["links"]:
        if (server['rel'] != "parent"):
            wlsDomain.addServer(WLSServer(server["title"], server["uri"]))


# Get the url of the list of logs, along with some other basic
# server information
def getLogListUrl(server, username, password):
    serverJson = getServerJson(server.serverUrl, username, password)
    server.setState(serverJson["item"]["state"])
    if server.state == "running":
        server.setHealth(serverJson["item"]["health"]["state"])

    for link in serverJson["links"]:
        if link["rel"] == "logs":
            logListULR = link["uri"]
    return logListULR


#For the given server, get the url for each server log
def getServerLogUrl(server,username,password, logListUrl):
    logListJson = getServerJson(logListUrl, username, password)
    for link in logListJson["links"]:
        if link["rel"] == "items.name":
            if not link["title"].startswith("JMSMessageLog") and \
               not link["title"].startswith("HTTPAccessLog"):
               server.addLog(WLLog(link["title"],link["uri"]))


#Go and find all server logs and read them, and take note of
#the error messages
def searchServerLogs(wlsDomain, username, password):
    for server in wlsDomain.serverList:
        #get the url to the list of logs for the given server
        logListUrl = getLogListUrl(server, username, password)

        #we can't get the log of a server that is not running
        if server.state != "running":
            continue

        #get the url for each server log of the given server
        getServerLogUrl(server,username,password, logListUrl)

        for log in server.logList:
            #we are not interested in the HTTPAccessLog
            if log.name != "HTTPAccessLog":
               if server.state != "running":
                   continue

               startTime = time.time()
               print("Reading " + server.name + " : " + log.name)

               serverLogJson = getServerJson(log.logUrl, username, password)
               for logEntry in serverLogJson["items"]:
                  if logEntry["severity"] == "Error":
                      log.addLogEntry(LogEnty(logEntry["severity"],logEntry["timeStamp"],logEntry["message"]))
                      server.incrementError()
               endTime = time.time()
               log.setDuration(formatTimeOutput(math.floor(endTime-startTime)))


#output the error statistics to the command line
def outputStatisticsConsole(wlsDomain):
    print("+----------------------+--------------------------+----------+--------+")
    printStatLine("Server", "State", "Health", "Errors")
    print("+----------------------+--------------------------+----------+--------+")
    for server in wlsDomain.serverList:
        printStatLine(server.name,server.state,server.health,server.errorCount)
    print("+----------------------+--------------------------+----------+--------+")

    print()
    print()
    print("+----------------------+-------------------------+-----------+--------+")
    print("| Server               | Log                     | Duration  | Errors |")
    print("+----------------------+-------------------------+-----------+--------+")
    for server in wlsDomain.serverList:
        for log in server.logList:
           print('| {:20} | {:23} | {:9} | {:>6} |'.format(server.name, log.name,log.duration, log.counter))
    print("+----------------------+-------------------------------------+--------+")


def printStatLine(server,state,health, count):
    print("| {:20} | {:24} | {:8} | {:>6} |".format(server,state,health, count))


#convert the number of seconds to hh:mm:ss format
def formatTimeOutput(seconds):
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return "{:02}:{:02}:{:02}".format(h,m,s)


def run():
    print()
    print()
    print("Please enter the WLS Server Details")
    print("-------------------------------------------")
    print()
    wlsServerUrl = input('Please enter the server and port e.g localhost:7001  ')
    username     = input("Please enter the weblogic user name: ")
    password     = getpass.getpass("Please enter the weblogic user password: ")
    print()

    wlsDomain = WLSDomain()

    getServers(wlsDomain,wlsServerUrl,username,password)
    searchServerLogs(wlsDomain,username,password)
    outputStatisticsConsole(wlsDomain)
    writeHTMLOutput(wlsDomain)

def writeHTMLOutput(wlsDomain):
    outfile = open(os.path.join(os.getcwd(), "errorReport.html"), 'w+')
    outputHTMLHeader(outfile)
    outputHTMLStats(outfile,wlsDomain)
    outputHTMLErrors(outfile, wlsDomain)
    outputHTMLTail(outfile)

def outputHTMLStats(outfile,wlsDomain):
    outfile.write("<div class='panel panel-primary'>\n\
            <div class='panel-heading'>\n\
              <h3 class='panel-title'>Server Log Statistics</h3>\n\
            </div>\n\
            <div class='panel-body'>\n")
    outfile.write("<div class='col-md-8'>\n\
	          <table class='table table-bordered'>\n\
	            <thead>\n\
	              <tr>\n\
	                <th>Server</th>\n\
	                <th>State</th>\n\
	                <th>Health</th>\n\
	                <th>Errors</th>\n\
	              </tr>\n\
	            </thead>\n\
	            <tbody>\n")
    for server in wlsDomain.serverList:
        if server.errorCount > 0:
            outfile.write("\
	              <tr class='warning'>\n\
	                <td><a href='"+server.name+"'>"+server.name+"</a></td>\n\
	                <td>"+server.state+"</td>\n\
	                <td>"+server.health+"</td>\n\
	                <td>"+str(server.errorCount)+"</td>\n\
	              </tr>\n")
        else:
            if server.state == 'running':
                trClass = 'success'
            else:
                trClass = 'danger'

            outfile.write("\
        	              <tr class='"+trClass+"'>\n\
        	                <td>" + server.name + "</td>\n\
        	                <td>" + server.state + "</td>\n\
        	                <td>" + server.health + "</td>\n\
        	                <td>" + str(server.errorCount) + "</td>\n\
        	              </tr>\n")
    outfile.write("\
               </tbody>\n\
             </table>\n\
           </div>\n")
    outfile.write("\
           <div class='col-md-8'>\n\
	          <table class='table table-bordered'>\n\
	            <thead>\n\
	              <tr>\n\
	                <th>Server</th>\n\
	                <th>Log</th>\n\
	                <th>Duration</th>\n\
	                <th>Errors</th>\n\
	              </tr>\n\
	            </thead>\n\
	            <tbody>\n")

    for server in wlsDomain.serverList:
        for log in server.logList:
            if log.counter > 0:
                outfile.write("\
                        <tr class='warning'>\n\
                           <td><a href='#"+server.name+"'>"+server.name+"</a></td>\n\
                           <td><a href='#"+server.name+log.name+"'>"+log.name+"</a></td>\n\
                           <td>"+log.duration+"</td>\n\
                           <td>"+str(log.counter)+"</td>\n\
                        </tr>\n")
            else:
                outfile.write("\
                        <tr class='success'>\n\
                           <td>"+server.name+"</td>\n\
                           <td>"+log.name+"</td>\n\
                           <td>"+log.duration+"</td>\n\
                           <td>"+str(log.counter)+"</td>\n\
                        </tr>\n")
    outfile.write("\
                </tbody>\n\
              </table>\n\
            </div>\n\
        </div>\n\
        </div>")

def outputHTMLHeader(outfile):
    outfile.write("<!DOCTYPE html>\n\
<html lang='en'>\n\
  <head>\n\
    <meta charset='utf-8'>\n\
    <title>WebLogic Server Log Errors</title>\n\
	<link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap.min.css' integrity='sha384-BVYiiSIFeK1dGmJRAkycuHAHRg32OmUcww7on3RYdg4Va+PmSTsz/K68vbdEjh4u' crossorigin='anonymous'>\n\
	<link rel='stylesheet' href='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/css/bootstrap-theme.min.css' integrity='sha384-rHyoN1iRsVXV4nD0JutlnGaslCJuC7uwjduW9SVrLvRYooPp2bWYgmgJQIXwl/Sp' crossorigin='anonymous'>\n\
	<script src='https://maxcdn.bootstrapcdn.com/bootstrap/3.3.7/js/bootstrap.min.js' integrity='sha384-Tc5IQib027qvyjSMfHjOMaLkfuWVxZxUPnCJA7l2mCWNIpG9mGCD8wGNIcPD7Txa' crossorigin='anonymous'></script>\n\
  </head>\n\
  <body>\n\
     <div class='container theme-showcase' role='main'>\n\
     &nbsp")

def outputHTMLTail(outfile):
    outfile.write("    <script src='https://ajax.googleapis.com/ajax/libs/jquery/1.12.4/jquery.min.js'></script>\n\
       </div>\n\
     </body>\n\
    </html>\n")

def outputHTMLErrors(outfile,wlsDomain):
    for server in wlsDomain.serverList:
        if server.errorCount > 0:
            outfile.write("<h1>" + server.name + "<a name='" + server.name + "'></a></h1>")
            for log in server.logList:
                outputCounter = 0
                if log.counter > 0:
                    outfile.write("<h2>"+log.name+"<a name='"+server.name+log.name+"'></a></h2>")
                    for error in log.logEntryList:
                        outputCounter = outputCounter + 1
                        outfile.write("<h5>#"+str(outputCounter)+"/"+str(log.counter)+" - "+server.name+" - "+log.name+"</h5>")
                        outfile.write("<pre>"+error.when+" "+error.severity+" "+error.message+"</pre><br/>")

class WLSDomain:
    def __init__(self):
        self.serverList= []

    def addServer(self, server):
        self.serverList.append(server)


class WLSServer:
    def __init__(self, name, serverUrl):
        self.logList = []
        self.name = name
        self.serverUrl = serverUrl
        self.health = ""
        self.state  = ""
        self.errorCount = 0

    def addLog(self, wlLog):
        self.logList.append(wlLog)

    def setHealth(self, health):
        self.health = health

    def setState(self, state):
        self.state = state
    def incrementError(self):
        self.errorCount = self.errorCount + 1

class WLLog:
    def __init__(self, name, logUrl):
        self.name = name
        self.logUrl = logUrl
        self.logEntryList = []
        self.counter      = 0;
        self.duration     = ""

    def addLogEntry(self, logEntry):
        self.logEntryList.append(logEntry)
        self.counter  = self.counter + 1

    def setDuration(self,duration):
        self.duration = duration

class LogEnty:
    def __init__(self, severity, when, message):
        self.severity = severity
        self.when     = when
        self.message  = message


if __name__ == '__main__':
    run()