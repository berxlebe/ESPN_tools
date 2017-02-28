#!/usr/bin/python

import os
import re
import sys
import urllib

# select preferred mysql library, also comment out appropriate line in write_sql function
import MySQLdb
#import mysql.connector

import time

#this list can be used to cross reference espn teamIDs with IDs in your database
ownerList = 0,7,8,1,11,5,10,3,4,9,2,12,6


def write_sql(records, points):
  
# comment out appropriate line based on library selected at the top of file  
#  replace USER, PASSWORD, host and DATABASE values with appropiate values
#  cnx = mysql.connector.connect(user='USER', password='PASSWORD', host='HOST', database='DATABASE')
  cnx = MySQLdb.connect("HOST","USER", "PASSWORD", "DATABASE")
  cursor = cnx.cursor()

#insert each record into database, replace TABLE_NAME,KEY,OWNER_ID_COLUMN,WIN_COLUMN,LOSS_COLUMN,TIE_COLUMN,POINTS_COLUMN
#with apprpropriate values for your table
  insert_owner = ("INSERT INTO TABLE_NAME (OWNER_ID_COLUMN, WIN_COLUMN, LOSS_COLUMN, TIE_COLUMN) VALUES (%s,%s,%s,%s)")
  update_points = ("UPDATE TABLE_NAME SET POINTS_COLUMN=%s, WHERE OWNER_ID_COLUMN=%s")
  i=1
  for record in records:
    teamid=ownerList[int(record[0])]
    wins=record[1]
    losses=record[2]
    ties=record[3]    
    cursor.execute(insert_owner % ( teamid,wins,losses,ties))

  for record in points:
    teamid=ownerList[int(record[0])]
    points=record[1]
    cursor.execute(update_points % ( points,i, teamid))   
    i=i+1


  cnx.commit()

  cursor.close()
  cnx.close()
  return


def download_espn_standings(dir, date):
  if not os.path.exists(dir):
    os.makedirs(os.path.abspath(dir))
  #Update url replacing LEAGUE_ID with your league ID and seasonId with current year
  url = 'http://games.espn.com/ffl/standings?leagueId=LEAGUE_ID&seasonId=2017'
  urllib.urlretrieve(url, os.path.join(os.path.abspath(dir), 'standings.html'))
  f = open(os.path.join(os.path.abspath(dir), 'standings.html'))
  
  #retrieve win/loss record for each team, again replace LEAGUE_ID
  records = re.findall(r'href="/ffl/clubhouse\?leagueId=LEAGUE_ID&amp;teamId=(\d+)&amp;seasonId=2017" target="_top">[\s\w\d\'\?\!]+</a></td><td align="right" >(\d+)</td><td align="right" >(\d+)</td><td align="right"  >(\d+)</td><td align="right" >', f.read())
  f.seek(0)
  #retrieve full season point totals for each team, replace LEAGUE_ID
  points = re.findall(r'href="/ffl/clubhouse\?LEAGUE_ID=436410&amp;teamId=(\d+)&amp;seasonId=2016" target="_top">[\s\w\d\'\?\!]+</a> \([\s\w\d\'\?\!\,\.]+\)</td><td align="right" class="sortablePF">(\d+)</td>', f.read())
  sorted_points = sorted(points, key=lambda tup: int(tup[1]), reverse=True)
  write_sql(records, sorted_points)

  f.close()
  os.remove(os.path.join(os.path.abspath(dir), 'standings.html'))
  return 

  


  
def main():
  args = sys.argv[1:]

  if not args:
    print 'usage: dir'
    sys.exit(1)
  #Calculate today's auctions
  today = time.strftime("%Y%m%d")
  download_espn_standings(args[0], str(today))



if __name__ == '__main__':
  main()
