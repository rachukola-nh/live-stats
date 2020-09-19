import json
import sys
import getopt
from pathlib import Path
def main(argv):
    outputfile = 'all_plays.json'
    inputpath = ''
    recursive = False
    try:
      opts, args = getopt.getopt(argv,"i:o:",['outputfile='])
    except getopt.GetoptError:
      sys.exit(2)
    for opt,arg in opts:
        if opt in ('-i'):
            inputpath = arg
        if opt in ('-o','--outputfile'):
            outputfile = arg
    js = []
    for path in Path(inputpath).rglob('*.json'):
        try:
            t,season,tournament,_ = str(path).split("\\")
        except:
            continue
        game_json = {}
        with open(str(path)) as f:
            game_json =json.load(f)
        for k,v in game_json.items():
            v['possession_number']=int(k)
            v['season']=season
            v['tournament']= tournament
            v['game']=str(path)
            js.append(v)
    sorted_plays = sorted(js,key=lambda x: (x['game'],x['possession_number']))
    with open(outputfile,'w+') as o:
        json.dump(sorted_plays,o,indent=2)



if __name__ == "__main__":
    main(sys.argv[1:])
