#!/usr/bin/python

import os
import re
import sys
import urllib

# select preferred mysql library, also comment out appropriate line in write_sql function
import MySQLdb
#import mysql.connector

import time

#used to cross reference espn team ids with team IDs in database
ownerList = 0,7,8,1,11,5,10,3,4,9,2,12,6


def write_sql(adds):
  
# comment out appropriate line based on library selected at the top of file  
#  replace USER, PASSWORD, host and DATABASE values with appropiate values
#  cnx = mysql.connector.connect(user='USER', password='PASSWORD', host='HOST', database='DATABASE')
  cnx = MySQLdb.connect("HOST","USER", "PASSWORD", "DATABASE")
  cursor = cnx.cursor()

  for player in adds:
    teamid=ownerList[int(player[0])]
    playerid=player[1]
    playername=player[2]
    aucValue=player[3]    
    
    #find added player in your database, replace TABLE_NAME and ESPN_PLAYER_ID with names appropriate to your table
    get_player = ("SELECT * FROM TABLE_NAME WHERE ESPN_PLAYER_ID=\"%s\"")
    cursor.execute(get_player % ( playerid))
  
    #player already in database update info
    if cursor.rowcount == 1:
    #replace TABLE_NAME,TEAMID_COLUMN and ESPN_PLAYER_ID with names appropriate to your table
      update_player = ("UPDATE TABLE_NAME SET TEAMID_COLUMN=%s, COST_COLUMN=%s WHERE ESPN_PLAYER_ID=\"%s\"")
      cursor.execute(update_player % (teamid,aucValue,playerid)) 
    elif cursor.rowcount == 0:
    # check if player is in database under different ID
      #replace TABLE_NAME and NAME_COLUMN
      get_player = ("SELECT * FROM TABLE_NAME WHERE NAME_COLUMN=\"%s\"")
      cursor.execute(get_player % ( playername))
      if cursor.rowcount == 1:
      #player is found, update info including ID
      #replace TABLE_NAME, TEAMID_COLUMN, COST_COLUMN, ESPN_PLAYER_ID, NAME_COLUMN
        update_player = ("UPDATE TABLE_NAME SET TEAMID_COLUMN=%s, COST_COLUMN=%s, ESPN_PLAYER_ID=%s WHERE NAME_COLUMN=\"%s\"")
        cursor.execute(update_player % (teamid,aucValue,playerid,playername)) 
      elif cursor.rowcount==0:
      #player not found create new entry
      #replace TABLE_NAME, TEAMID_COLUMN, KEY,COST_COLUMN, ESPN_PLAYER_ID, NAME_COLUMN
        insert_player = ("INSERT INTO TABLE_NAME (KEY,NAME_COLUMN,TEAMID_COLUMN,ESPN_PLAYER_ID,COST_COLUMN) VALUES (%s,\"%s\",%s,%s,%s)")
        cursor.execute(insert_player % (playerid,playername,teamid,playerid,aucValue)) 
      else:
        print playername
        


  cnx.commit()

  cursor.close()
  cnx.close()
  return


def download_espn_pickups(dir, date):
  if not os.path.exists(dir):
    os.makedirs(os.path.abspath(dir))
  #replace LEAGUE_ID with your league id
  url = 'http://games.espn.go.com/ffl/waiverreport?leagueId=LEAGUE_ID&seasonId=2017&date=%s' % (date)
  urllib.urlretrieve(url, os.path.join(os.path.abspath(dir), 'auction_report.html'))
  f = open(os.path.join(os.path.abspath(dir), 'auction_report.html'))

  #pull teamID, playername, and auction cost from HTML page
  #replace LEAGUE_ID with your league id
  adds = re.findall(r'teamId=(\d+)&amp;seasonId=\d\d\d\d" target="_top">[\w\s\(\)\'\!\?]+</a></td>\n<td><a href="" class="flexpop" content="tabs#ppc" instance="_ppc" fpopHeight="357px" fpopWidth="490px" tab="null" leagueId="LEAGUE_ID" playerId="(\d+)" teamId="-2147483648" seasonId="\d+" cache="true">([\w\s\./\']+)</a>(?:, [\w\s/]+| D\/ST)</td>\n<td>\$(\d+)</td><td><strong>Added', f.read())
  write_sql(adds)

  f.close()
  os.remove(os.path.join(os.path.abspath(dir), 'auction_report.html'))
  return 

def write_sql_drops(drops):
  
# comment out appropriate line based on library selected at the top of file  
#  replace USER, PASSWORD, host and DATABASE values with appropiate values
#  cnx = mysql.connector.connect(user='USER', password='PASSWORD', host='HOST', database='DATABASE')
  cnx = MySQLdb.connect("HOST","USER", "PASSWORD", "DATABASE")
  cursor = cnx.cursor()
  cursor = cnx.cursor()

  for player in drops:
    teamid=ownerList[int(player[1])]
    playername=player[0]
    
    #Find dropped player in table
    #replace ESPN_PLAYER_ID, TABLE_NAME, NAME_COLUMN
    get_player = ("SELECT ESPN_PLAYER_ID FROM TABLE_NAME WHERE NAME_COLUMN=\"%s\"")
    cursor.execute(get_player % ( playername))
    if cursor.rowcount == 1:
    #player exists in database, set team info to NULL since he was dropped
    #replace TABLE_NAME, TEAMID_COLUMN and NAME_COLUMN
      update_player = ("UPDATE TABLE_NAME SET TEAMID_COLUMN=NULL WHERE NAME_COLUMN=\"%s\"")
      cursor.execute(update_player % (playername)) 
    else:
      print ("drop failed for %s")%(playername)
        


  cnx.commit()

  cursor.close()
  cnx.close()
  return
  
def download_espn_drops(dir, date):
  if not os.path.exists(dir):
    os.makedirs(os.path.abspath(dir))
  #update LEAGUE_ID with your league id
  url = 'http://games.espn.go.com/ffl/recentactivity?leagueId=436410&seasonId=2017&activityType=2&startDate=%s&endDate=%s&teamId=-1&tranType=3' % (date,date)
  urllib.urlretrieve(url, os.path.join(os.path.abspath(dir), 'drop_report.html'))
  f = open(os.path.join(os.path.abspath(dir), 'drop_report.html'))
  #extract player name and team id of every player dropped
  #update LEAGUE_ID with your league id
  drops = re.findall(r'<br>Drop</td><td valign="top">[\w\s\(\)\']+ dropped <b>([\w\s\(\)\']+)</b>, [\w\s\\]+ to Waivers(?:|[\w\$\s\d\<\>\/]+)</td><td valign="top"><a href="/ffl/clubhouse\?leagueId=LEAGUE_ID&teamId=(\d+)">', f.read())
  write_sql_drops(drops)
  f.close()
  os.remove(os.path.join(os.path.abspath(dir), 'drop_report.html'))
  return 
  


  
def main():
  args = sys.argv[1:]

  if not args:
    print 'usage: dir'
    sys.exit(1)
  #Calculate today's auctions
  today = time.strftime("%Y%m%d")
  download_espn_pickups(args[0], str(today))
  download_espn_drops(args[0], str(today))



if __name__ == '__main__':
  main()
