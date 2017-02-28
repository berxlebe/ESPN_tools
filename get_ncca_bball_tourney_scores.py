#!/usr/bin/python

#This File is designed to pull stats for the NCAA Mens Basketball tournament from the ESPN game pages.  As written it 
# pulls the points, rebounds and assists of each player who played in the game, as well as stores the margin of victory
#or defeat of each team in each game.


import os
import re
import sys
import urllib
# select preferred mysql library, also comment out appropriate line in write_sql function
import MySQLdb
#import mysql.connector
import time

round = 0
final = 0
#these values represent column names in database for storing player stats, update with values for your table
playerDict = {1:"GAME_1_COLUMNS",
              2:"GAME_2_COLUMNS",
              3:"GAME_3_COLUMNS",
              4:"GAME_4_COLUMNS",
              5:"GAME_5_COLUMNS",
              6:"GAME_6_COLUMNS"}


def download_espn_games_page(dir, date):
  global round
  round = 0
  
  #create path to save HTML page
  if not os.path.exists(dir):
    os.makedirs(os.path.abspath(dir))
    
  #url for ESPNs college basketball scoreboard for specified day.  Needs to be updated from time to time
  url = 'http://scores.espn.go.com/ncb/scoreboard?date=%s' % (date)
  
  #download page and save to directory
  urllib.urlretrieve(url, os.path.join(os.path.abspath(dir), 'espn_scoreboard.html'))
  f = open(os.path.join(os.path.abspath(dir), 'espn_scoreboard.html'))
  
  #get gameId for each game played on specified date and use to recreate boxscore url
  boxscores = re.findall(r'boxscore\?gameId=(\d+)",', f.read())
  boxscore_url = []
  for boxscore in boxscores:
    boxscore_url.append('http://espn.com/mens-college-basketball/boxscore?gameId=%s' % (boxscore))
  
  #My usage of this data is specific to the round of the tournament search for specific strings to 
  # identify which round the days games were a part of.  These strings may need to be updated from
  # time to time as the site is tweeked 
  f.seek(0)
  roundStr = re.search(r'S BASKETBALL CHAMPIONSHIP - ([\w\s-]+)","type', f.read())
  if roundStr :
    if roundStr.group(1) == "NATIONAL CHAMPIONSHIP":
      round = 6
    elif roundStr.group(1) == "FINAL FOUR":
      round = 5
    else:
      roundStr2 = re.search(r'REGION - ([\w\s]+)', roundStr.group(1))
      if roundStr2.group(1) == "ELITE 8":
        round = 4
      elif roundStr2.group(1) == "SWEET 16":
        round = 3
      elif roundStr2.group(1) == "2ND ROUND":
        round = 2
      elif roundStr2.group(1) == "1ST ROUND":
        round = 1
  else:
  # If no strings are found then games are not tournament games and can be ignored.
    round = 0
  f.close()
  os.remove(os.path.join(os.path.abspath(dir), 'espn_scoreboard.html'))
  
  #return list of urls for specific games
  return boxscore_url

#Extract the score of each team in boxscore represented by url
def get_team_scores(url, dir):
  global final
  final = 0

  #Download boxscore html
  urllib.urlretrieve(url, os.path.join(os.path.abspath(dir), 'espn_boxscore.html'))
  f = open(os.path.join(os.path.abspath(dir), 'espn_boxscore.html'), 'r')
  
  #Extract the two team IDs from HTML page.  Your database can reference teams by this same ID to make things simpler
  teamids = re.findall(r'class="team-name" href="/mens-college-basketball/team/_/id/(\d+)">', f.read())
  
  #Get the score for each team
  f.seek(0)
  teamscores = re.findall(r'<td class="final-score">(\d+)</td>',f.read())
  teams = zip(teamids,teamscores)
  
  f.close()
  os.remove(os.path.join(os.path.abspath(dir), 'espn_boxscore.html'))  
  
  #return the id, score pairing for both teams
  return teams

#open boxscore to extract the player ID, points, rebounds and assists for every player in game
def get_player_stats(url, dir):
  urllib.urlretrieve(url, os.path.join(os.path.abspath(dir), 'espn_boxscore.html'))
  f = open(os.path.join(os.path.abspath(dir), 'espn_boxscore.html'), 'r')
  players = re.findall(r'/player/_/id/(\d+)">[\w\s\'.-]+</a><span class="position">[\w]+</span></td><td class="min">[\d-]+</td><td class="fg">[\d-]+</td><td class="3pt">[\d-]+</td><td class="ft">[\d-]+</td><td class="oreb">[\d-]+</td><td class="dreb">[\d-]+</td><td class="reb">(\d+)</td><td class="ast">(\d+)</td><td class="stl">[\d-]+</td><td class="blk">[\d-]+</td><td class="to">[\d-]+</td><td class="pf">[\d-]+</td><td class="pts">(\d+)</td>', f.read())
  f.close()
  os.remove(os.path.join(os.path.abspath(dir), 'espn_boxscore.html'))  

  #return all players
  return players

def write_sql(teams, players):
# comment out appropriate line based on library selected at the top of file  
#  replace USER, PASSWORD, host and DATABASE values with appropiate values
#  cnx = mysql.connector.connect(user='USER', password='PASSWORD', host='HOST', database='DATABASE')
  cnx = MySQLdb.connect("HOST","USER", "PASSWORD", "DATABASE")
  cursor = cnx.cursor()

#enter team info
  teamid1 = teams[0][0]
  teamscore1 = teams[0][1]
  teamid2 = teams[1][0]
  teamscore2 = teams[1][1]
  
  #calculate margin of victory or defeat
  adjScore1 = int(teamscore1)-int(teamscore2)
  adjScore2 = int(teamscore2)-int(teamscore1)
  
 #column name where game margin is scored replace with appropriate value for your Database 
  gameStr = "GM_MARGIN_COLUM"

  #update SQL query to reflect your data base.  Modify TEAM_TABLE and TEAM_ID_COLUMN
  add_team_stats = ("Update TEAM_TABLE SET %s=%s WHERE TEAM_ID_COLUMN=%s AND Year=2017")
  cursor.execute(add_team_stats % (gameStr, adjScore1, teamid1))
  cursor.execute(add_team_stats % (gameStr, adjScore2, teamid2))

  #enter player info, column names are combination of Dict values above and extensions for each stat
  #update as appropriate to fit your table
  pointStr = playerDict[round] + "points"
  reboundStr = playerDict[round] + "rebounds"
  assistStr = playerDict[round] + "assists"
  
  #replace PLAYER_TABLE, PLAYERID_COLUMN
  update_player_stats = ("UPDATE PLAYER_TABLE SET %s=%s, %s=%s, %s=%s WHERE PLAYERID_COLUMN=%s AND YEAR=2017")
  
  for player in players:
    cursor.execute(update_player_stats % (reboundStr, player[1], assistStr, player[2], pointStr, player[3], player[0])) 



 
  cnx.commit()

  cursor.close()
  cnx.close()
  return

  
def main():
  args = sys.argv[1:]

  if not args:
    print 'usage: dir'
    sys.exit(1)
  today = time.strftime("%Y%m%d")
  yesterdayD = int(today) -1
  yesterday = str(yesterdayD)
  
  #Calculate today's scores, run on todays scores to get latest data
  today_urls = download_espn_games_page(args[0], today)
  if round>0:
    for url in today_urls:
      team_scores = get_team_scores(url, args[0])
      player_stats = get_player_stats(url, args[0])
      write_sql(team_scores, player_stats)
 # else:
 #   print "No Tourney Games on this Date"

  #Calculate yesterday's scores, run on yesterdays scores to cover scenario of data updating between last run and day change
  today_urls = download_espn_games_page(args[0], yesterday)
  if round>0:
    for url in today_urls:
      team_scores = get_team_scores(url, args[0])
      player_stats = get_player_stats(url, args[0])
      write_sql(team_scores, player_stats)
#  else:
#    print "No Tourney Games on this Date"
#  os.remove(team_file)

if __name__ == '__main__':
  main()
