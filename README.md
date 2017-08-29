
# Weblgoic Server Log Error Finder

This python script uses the WebLogic Server REST Administration API to 
1. find all of the server logs in a domain
2. read through the logs and capture any messages with the severity of "Error"
3. output the high level statistics to the command line
4. output the findings to errorReport.html. This contains the high level statistics, as well the all of the error messages

# Running the script

`python logInspect.py`

For example

```
python logInspect.py

Pleas enter the WLS Server Details
-------------------------------------------

Please enter the server and port e.g localhost:7001  54.70.166.152:7001
Please enter the weblogic user name: weblogic
Please enter your weblogic user passowrd:

Reading AdminServer : DataSourceLog
Reading AdminServer : DomainLog
Reading AdminServer : ServerLog
Reading osb_server1 : DataSourceLog
Reading osb_server1 : ServerLog
Reading wsm_server1 : DataSourceLog
Reading wsm_server1 : ServerLog
+----------------------+--------------------------+----------+--------+
| Server               | State                    | Health   | Errors |
+----------------------+--------------------------+----------+--------+
| AdminServer          | running                  | ok       |   1008 |
| osb_server1          | running                  | ok       |      0 |
| wsm_server1          | running                  | ok       |      0 |
+----------------------+--------------------------+----------+--------+


+----------------------+-------------------------+-----------+--------+
| Server               | Log                     | Duration  | Errors |
+----------------------+-------------------------+-----------+--------+
| AdminServer          | DataSourceLog           | 00:00:00  |      0 |
| AdminServer          | DomainLog               | 00:00:06  |   1006 |
| AdminServer          | ServerLog               | 00:00:07  |      2 |
| osb_server1          | DataSourceLog           | 00:00:00  |      0 |
| osb_server1          | ServerLog               | 00:00:08  |      0 |
| wsm_server1          | DataSourceLog           | 00:00:00  |      0 |
| wsm_server1          | ServerLog               | 00:00:04  |      0 |
+----------------------+-------------------------------------+--------+
```
