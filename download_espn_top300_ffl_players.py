import os
import re
import sys
import urllib

# select preferred mysql library, also comment out appropriate line in write_sql function
import MySQLdb
#import mysql.connector
import time


def download_espn_300_page(dir):
  if not os.path.exists(dir):
    os.makedirs(os.path.abspath(dir))
#URL for espn's top 300 will change from year to year
  url = 'http://espn.go.com/fantasy/football/story/_/id/12866396/top-300-rankings-2016'
  urllib.urlretrieve(url, os.path.join(os.path.abspath(dir), 'espn_300.html'))
  return os.path.join(os.path.abspath(dir), 'espn_300.html')


def write_sql(players, nocost):
# comment out appropriate line based on library selected at the top of file  
#  replace USER, PASSWORD, host and DATABASE values with appropiate values
#  cnx = mysql.connector.connect(user='USER', password='PASSWORD', host='HOST', database='DATABASE')
  cnx = MySQLdb.connect("HOST","USER", "PASSWORD", "DATABASE")
  cursor = cnx.cursor()

  #Clear all rankings in table
  #replace TABLE_NAME, RANK_COLUMN with appropriate values for your table
  update_player_stats = ("UPDATE TABLE_NAME SET RANK_COLUMN=NULL")
  cursor.execute(update_player_stats) 

  for player in players:
    playername=player[2]
    playerrank=player[0]
    position=player[3]
    playerid=player[1]    

    #check if player is already in database
    #replace TABLE_NAME and ESPNID_COLUMN
    get_player = ("SELECT * FROM TABLE_NAME WHERE ESPNID_COLUMN=\"%s\"")
    cursor.execute(get_player % (playerid))

    if cursor.rowcount !=1:
      #check for player by name incase ESPN ID was changed
      #replace TABLE_NAME and NAME_COLUMN;
      get_player = ("SELECT * FROM TABLE_NAME WHERE NAME_COLUMN=\"%s\"")
      cursor.execute(get_player % ( playername))
      #
      if cursor.rowcount == 0:
      #player is new to database
      #replace column and table names
        insert_player = ("INSERT INTO TABLENAME (KEY,NAME_COLUMN,POSITION_COLUMN,RANK_COLUMN,ESPNID_COLUMN) VALUES (%s,\"%s\",\"%s\",%s,%s)")
        cursor.execute(insert_player % (playerid,playername,position,playerrank,playerid)) 
      else:
      #id was changed
      #replace column and table names
        update_player_stats = ("UPDATE TABLE_NAME SET ESPNID_COLUMN=%s, RANK_COLUMN=%s WHERE NAME_COLUMN=\"%s\"")
        cursor.execute(update_player_stats % (playerid,playerrank,playername)) 
      continue
      #replace column and table names
    update_player_stats = ("UPDATE TABLE_NAME SET RANK_COLUMN=%s WHERE ESPNID_COLUMN=\"%s\"")
    cursor.execute(update_player_stats % (playerrank,playerid)) 
    
  cnx.commit()

  cursor.close()
  cnx.close()
  return


def get_player_list(dir):
  file = open(os.path.join(os.path.abspath(dir), 'espn_300.html'), 'r') 
  #pull player name, espn ranking, espn id and position from file
  e300list = re.findall(r'<td>(\d+). <a href="(?:http://espn.go.com/nfl/player/_/id/(\d+)/[\w\s\'-.]+|/nfl/team/_/name/\w+/[\w-]+)">([\w\s\'-.]+)</a>, (\w+)</td><td>\w+</td><td>[\w-]+</td><td>[\w\d]+</td><td>(?:\$(\d+)|--)</td>', file.read())
  write_sql(e300list,0)
  return


  
def main():
  args = sys.argv[1:]

  if not args:
    print 'usage: dir '
    sys.exit(1)


  team_file = download_espn_300_page(args[0])
  get_player_list(args[0])
  os.remove(team_file)

if __name__ == '__main__':
  main()
