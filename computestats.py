import pandas as pd
import numpy as np
import re
import xlrd
import sys, getopt
import json
from pathlib import Path


TRANSLATION = {
    1:
    {'G':'Goal by {0}.',
    'GD':'Goal on the drive by {0}.',
    'GS':'Goal on the shot by {0}.',
    'OG':'Own Goal.',
    'E': 'Error by {0}.',
    'ET': 'Turnover penalty on {0}.',
    'EB': 'Blue card on {0} forces turnover.',
    'EY': 'Yellow card on {0} forces turnover.',
    'ER':'Red card on {0} forces turnover.',
    'EM':'Missed shot by {0}. Turnover.',
    'EP':'Errant pass by {0}. Turnover.',
    'ED':'Drop by {0}. Turnover.',
    'RCA':'Snitch catch by {0} is GOOD.',
    'OCA':'Snitch catch by {0} is GOOD.',
    '2CA':'Snitch catch by {0} is GOOD.',
    'RCB':'Snitch catch by {0} is GOOD.',
    'OCB':'Snitch catch by {0} is GOOD.',
    '2CB':'Snitch catch by {0} is GOOD.',
    'B':'blue card on {0}',
    'R': 'reset forced by {0}',
    'Y': 'yellow card on {0}',
    '2Y': 'second yellow card on {0}, {0} is ejected from the game',
    '1R': 'red card on {0},{0} is ejected from the game',
    'SOP':'SNITCH ON PITCH begins'
    },
    2:{
    'BU':'BROOMS UP! Quaffle Possession by {0}, Bludger Control by {1}',
    'G':'Goal by {0}, assist by {1}',
    'GD':'Goal on the drive by {0}, assist by {1}',
    'GS':'Goal on the shot by {0}, assist by {1}',
    'OG':'Own Goal',
    'GP':'{1} passes to {0} at the hoops, GOAL.',
    'T' :'Turnover by {0}',
    'TB':'Beat by {0} on {1} forces a TURNOVER.',
    'TC':'Turnover forced by physical contact by {0} on {1}',
    'TL':'Shot by {1} blocked by {0}. Turnover.',
    'TD':'Pass between {1} defended by {0}. Turnover',
    'EP':'Errant pass from {0} to {1}. Turnover',
    'ED':'Pass by {1} dropped by {0}. Turnover'
    }
}

def get_info(fname):
    xl_workbook = xlrd.open_workbook(fname)
    data_sheet = xl_workbook.sheet_by_index(0)
    roster_sheet = xl_workbook.sheet_by_index(1)
    return data_sheet,roster_sheet

def get_roster(roster_sheet):
    datuu = [[s.value for s in r] for r in roster_sheet.get_rows()]
    coln = datuu.pop(0)
    df = pd.DataFrame(datuu,columns=coln)
    df[''] = df[''].apply(lambda x: int(x))
    return df.replace(r'^\s*$', np.NaN, regex=True).set_index('').to_dict()
def get_info_from_data(data_sheet):
    raw = [[s.value for s in r] for r in data_sheet.get_rows()]
    header = [[s for s in row if s] for row in raw[1:4]]
    data = raw[6:]
    return header,data

def get_teams_from_header(header):
    return {header[0][0]:header[0][1],header[2][0]:header[2][1]}

# Brooms Up
def get_brooms_up(header,roster,teams):
    vala,valb = ['-'.join([str(x) for x in h]) for h in header if h]
    qa = re.search(r'[Qq](\d+)',vala)
    qb = re.search(r'[Qq](\d+)',valb)
    ba = re.search(r'[Bb](\d+)',vala)
    bb = re.search(r'[Bb](\d+)',valb)
    q_params = (int(qa.groups()[0]),'A')if qa else (int(qb.groups()[0]),'B')
    b_params = (int(ba.groups()[0]),'A')if ba else (int(bb.groups()[0]),'B')
    extras,offense,time = [],'Brooms Up','0000'
    result = ['BU',get_name(roster,teams,*q_params),get_name(roster,teams,*b_params)]
    return {'extras':extras,'offense':offense,'time':time,'result':result}

# Can take two forms of player_number, team
# E.g to look up A-34
# Either player_number = 'A34', team = None or
# player_number = 34, team = 'A'
# Can take a list of player_numbers (of one format only)
def get_name(roster,teams,player_number,team=None):

    if player_number is None:    #Nonexistent player
        return None
    if type(player_number)==list:
        return ' and '.join([get_name(roster,teams,num,team) for num in player_number])

    #Convert
    team,number = (team,player_number) if team else (player_number[0],player_number[1:])
    team_name = teams[team]
    team_roster = roster[team]
    if number =='?':
        return '{}-UNK'.format(team_name)
    else:
        n = int(float(number))
    if n in team_roster:
        if team_roster[n]!=team_roster[n]: #check for np.nan
            return '{}-{}'.format(team_name,n) #insert TEAM-# if not in roster or TEAM-NAME if in roster
        else:
            return '{}-{}'.format(team_name,team_roster[n])
    return '{}-UNK'.format(team_name) #if number is not known, use TEAM-UNK

def get_possessions(data_rows):
    possessions = []
    for j in np.arange(0,len(data_rows)-2,3):
        head = data_rows[j]
        vals = data_rows[j+1]
        for i in np.arange(0,len(vals)-2,3):
            extras = head[i]
            team = head[i+1]
            time = head[i+2]
            result = vals[i]
            if vals[i+1]!='':
                primary = [x for x in vals[i+1].split(',')] if type(vals[i+1])==str  else vals[i+1]
            else:
                primary = None
            if vals[i+2]!='':
                secondary = [x for x in vals[i+2].split(',')] if type(vals[i+2])==str else vals[i+2]
            else:
                secondary = None
            pos = (extras,team,time,result,primary,secondary)
            if len([x for x in pos if x])>1:
                possessions.append(pos)
    return possessions
def get_extras(extra):
    return [(x[:2],x[2:]) if x[0].isdigit() else (x[0],x[1:] if len(x)>1 else None) for x in extra.split(',')  ] if extra else []
def process_extra(ex, roster,teams,offense,defense):
    etype,eplayer = ex
    if etype == 'S':
        return ('SOP',1)
    elif etype =='R':
        return ('R',get_name(roster,teams,eplayer,defense))
    elif etype =='B' or etype =='Y' or etype=='1R' or etype=='2Y':
        return (etype,get_name(roster,teams,eplayer))
    return None
def interpret(pos,roster,teams):
    ex,team,time,result,primary,secondary = pos
    offense = team
    defense = 'A' if team=='B' else 'B'
    primary_team = ''
    if result=='RCA':
        primary_team = 'A'
    elif result == 'RCB':
        primary_team = 'B'
    elif result[0]=='T':
        primary_team = defense
    else:
        primary_team = offense
    secondary_team = team
    primary_name = get_name(roster,teams,primary,primary_team)
    secondary_name = get_name(roster,teams,secondary,secondary_team)
    extras = [process_extra(extra,roster,teams,offense,defense) for extra in get_extras(ex)]
    params = [result]+[x for x in [primary_name,secondary_name] if x]
    return {'extras':extras,'offense':teams[offense], 'defense':teams[defense],'time':time, 'result':params}

def gen_pbp(interpreted):
    params = interpreted['result']
    time = interpreted['time']
    offense = interpreted['offense']
    extras = interpreted['extras']
    result = params[0]
    p = params[1:]
    l = len(p)
    time_str = '({0:02d}:{1:02d})'.format(int(time)//100,int(time)%100) if time else ''
    base = '{}{} possession: {}'.format(time_str,offense, TRANSLATION[l][result].format(*p))
    if extras:
        base +=' During the play, '
        base +=','.join([TRANSLATION[1][extra[0]].format(extra[1]) for extra in extras])
    return base

def ind_stats(interpreted_list):
    stats = {}
    stats['Goals'] = {}
    stats['Assists'] = {}
    stats['Errors'] = {}
    stats['Ball Turnovers Forced'] = {}
    stats['Contact Turnovers Forced'] = {}
    stats['Beat Turnovers Forced'] = {}
    stats['Resets Forced'] = {}
    stats['ISR Snitch Catches'] = {}
    stats['OSR Snitch Catches'] = {}
    stats['Blue Cards'] = {}
    stats['Yellow Cards'] = {}
    stats['Second Yellow Cards'] = {}
    stats['Straight Red Cards'] = {}
    qpd = 0
    t1 = None
    for pos in interpreted_list:
        res = pos['result']
        if res[0]=='TB':
            if res[1] in stats['Beat Turnovers Forced']:
                stats['Beat Turnovers Forced'][res[1]]+=1
            else:
                stats['Beat Turnovers Forced'][res[1]]=1
        elif res[0] in ('TD','TL'):
            if res[1] in stats['Ball Turnovers Forced']:
                stats['Ball Turnovers Forced'][res[1]]+=1
            else:
                stats['Ball Turnovers Forced'][res[1]]=1
        elif res[0]=='TC':
            if res[1] in stats['Contact Turnovers Forced']:
                stats['Contact Turnovers Forced'][res[1]]+=1
            else:
                stats['Contact Turnovers Forced'][res[1]]=1
        elif res[0][0]=='G':
            if not t1:
                t1= pos['offense']
                qpd = 10
            elif t1==pos['offense']:
                qpd+=10
            else:
                qpd-=10
            if res[1] in stats['Goals']:
                stats['Goals'][res[1]]+=1
            else:
                stats['Goals'][res[1]]=1
            if len(res)>2 and res[2]:
                if res[2] in stats['Assists']:
                    stats['Assists'][res[2]]+=1
                else:
                    stats['Assists'][res[2]]=1
        elif res[0][0]=='E':
            if res[1] in stats['Errors']:
                stats['Errors'][res[1]]+=1
            else:
                stats['Errors'][res[1]]=1
        elif res[0] in ['RCA','RCB','OCA','OCB','2CA','2CB']:
            if abs(qpd)<=30:
                if res[1] in stats['ISR Snitch Catches']:
                    stats['ISR Snitch Catches'][res[1]]+=1
                else:
                    stats['ISR Snitch Catches'][res[1]]=1
            else:
                if res[1] in stats['OSR Snitch Catches']:
                    stats['OSR Snitch Catches'][res[1]]+=1
                else:
                    stats['OSR Snitch Catches'][res[1]]=1

            qpd= qpd+30 if res[1].split('-')[0]==t1 else qpd-30
        for extra in pos['extras']:
            extra_type, extra_player = extra
            if extra_type == 'B':
                if extra_player in stats['Blue Cards']:
                    stats['Blue Cards'][extra_player]+=1
                else:
                    stats['Blue Cards'][extra_player]=1
            elif extra_type == 'Y':
                if extra_player in stats['Yellow Cards']:
                    stats['Yellow Cards'][extra_player]+=1
                else:
                    stats['Yellow Cards'][extra_player]=1
            elif extra_type == '2Y':
                if extra_player in stats['Second Yellow Cards']:
                    stats['Second Yellow Cards'][extra_player]+=1
                else:
                    stats['Second Yellow Cards'][extra_player]=1
            if extra_type == '1R':
                if extra_player in stats['Straight Red Cards']:
                    stats['Straight Red Cards'][extra_player]+=1
                else:
                    stats['Straight Red Cards'][extra_player]=1
            if extra_type == 'R':
                if extra_player in stats['Resets Forced']:
                    stats['Resets Forced'][extra_player]+=1
                else:
                    stats['Resets Forced'][extra_player]=1
    df = pd.DataFrame(stats).dropna(how='all').fillna(0).astype(int).sort_values(by=['Goals','Assists','Errors'],ascending=[False,False,True])
    return df

def process_file(ifile):
    stem = ifile.split('.xls')[0]
    pbp_output_file = stem+'_pbp.txt'
    stats_output_file = stem+'_stats.csv'
    json_output_file = stem+'_data.json'
    dat, ros = get_info(ifile)
    roster = get_roster(ros)
    header,data = get_info_from_data(dat)
    teams = get_teams_from_header(header)
    get_brooms_up(header,roster,teams)
    possessions = get_possessions(data)
    interpreted = [get_brooms_up(header,roster,teams)]+[interpret(pos,roster,teams) for pos in possessions]
    with open(json_output_file,'w+') as f:
        json.dump({i:v for i,v in enumerate(interpreted)},f,indent=2)
    play_by_play = [gen_pbp(i)+'\n' for i in interpreted]
    with open(pbp_output_file,'w+') as f:
        f.writelines(play_by_play)
    stats = ind_stats(interpreted)
    stats.to_csv(stats_output_file)


def main(argv):
    inputfile = ''
    recursive = False
    try:
      opts, args = getopt.getopt(argv,"ai:",['all','inputfile='])
    except getopt.GetoptError:
      sys.exit(2)
    for opt,arg in opts:
        if opt in ('-i','--inputfile'):
            inputfile = arg
        if opt in ('-a','--all'):
            recursive = True
    if recursive:
        for path in Path('').rglob('*.xlsx'):
            process_file(str(path))
    elif not inputfile:
        print('Please include an inputfile')
    else:
        process_file(inputfile)



if __name__ == "__main__":
    main(sys.argv[1:])
