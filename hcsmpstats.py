# Written by diafygi: diafygi<at symbol>gmail<dot>com
# Released under the GPLv2: http://www.gnu.org/licenses/gpl-2.0.html
#
# This script downloads the HardcoreSMP death list and parses it to create stats for the month.

import urllib2
import re
from datetime import datetime, timedelta
from flask import Flask, render_template

app = Flask(__name__)

if not app.debug:
    import logging
    from logging import FileHandler
    file_handler = FileHandler("/var/log/flask/error.log")
    file_handler.setLevel(logging.WARNING)
    app.logger.addHandler(file_handler)


@app.route('/')
def hcsmp_data():
    #grab hcsmp death log
    req = urllib2.Request("http://hcsmp.com/players/deaths")
    full_page = "".join(urllib2.urlopen(req).readlines())

    #parse death log
    #[<rebirth>, <cause>, <user>, <join_time>, <death_time>, <total_time>, <summary>, <killer>, <witness>, <last_words>]
    deaths_raw = re.findall('<tr class="(.*?)"><td><i class="(.+?)"></i>(.+?)</td><td>(.+?)</td><td>(.+?)</td><td>(.+?)</td><td>(.+?)</td><td>(.+?)</td><td>(.+?)</td><td><pre class="lastWords">(.*?)</pre></td></tr>', full_page)
    deaths = []
    for d in deaths_raw:
    	deaths.append({
    		"rebirth": "revived" if d[0] else "final" if d[0] else None,
    	    "cause": d[1],
    	    "user": d[2],
    	    "join_time": datetime.strptime(d[3] + " 2012", "%b %d, %I:%M %p %Y"),
    	    "death_time": datetime.strptime(d[4] + " 2012", "%b %d, %I:%M %p %Y"),
    	    "total_time": timedelta(hours=int(d[5].split(" ")[0])) if "hour" in d[5] \
    	        else timedelta(minutes=int(d[5].split(" ")[0])) if "minute" in d[5] \
    	        else timedelta(seconds=int(d[5].split(" ")[0])),
            "summary": "Slain By Player" if "Killed By" in d[6] else d[6].strip(),
            "killer": d[7] if d[7] != "-" else re.findall("Killed By (.+)", d[6])[0].strip() if re.findall("Killed By (.+)", d[6]) else None,
            "witness": d[8] if d[8] != "-" else None,
            "last_words": d[9],
        })

    #define stats
    ways_to_die = {
        "overall": {},
       	"0-2 hours": {},
    	"2-30 hours": {},
    	"30+ hours": {},
    }
    killers_dict = {}
    witnesses_dict = {}

    #calculate stats
    for d in deaths:
    	#overall
        ways_to_die['overall'][d['summary']] = ways_to_die['overall'].get(d['summary'], 0) + 1
        #noobs
        if d['total_time'] < timedelta(hours=2):
            ways_to_die['0-2 hours'][d['summary']] = ways_to_die['0-2 hours'].get(d['summary'], 0) + 1
        #moderates
        elif d['total_time'] < timedelta(hours=30):
            ways_to_die['2-30 hours'][d['summary']] = ways_to_die['2-30 hours'].get(d['summary'], 0) + 1
        #experienced
        else:
            ways_to_die['30+ hours'][d['summary']] = ways_to_die['30+ hours'].get(d['summary'], 0) + 1
        #killers
        if d['killer']:
        	killers_dict[d['killer']] = killers_dict.get(d['killer'], 0) + 1
        #witnesses
        if d['witness']:
        	witnesses_dict[d['witness']] = witnesses_dict.get(d['witness'], 0) + 1

    killers = sorted([{"user":u, "killed":k} for u, k in killers_dict.items()], key=lambda u: u['killed'], reverse=True)
    witnesses = sorted([{"user":u, "witnessed":k} for u, k in witnesses_dict.items()], key=lambda u: u['witnessed'], reverse=True)

    #format for html charts and tables
    ways_to_die_tuple = {}
    for w in ways_to_die.keys():
        ways_to_die_tuple[w] = sorted([(d, c) for d, c in ways_to_die[w].items()], key=lambda u: u[1], reverse=True)

    ways_to_die_html = {
        "overall": {
            "labels": "|".join(["{} ({})".format(i[0], i[1]) for i in ways_to_die_tuple['overall']]),
            "numbers": ",".join([str(i[1]) for i in ways_to_die_tuple['overall']]),
        },
        "noob": {
            "labels": "|".join(["{} ({})".format(i[0], i[1]) for i in ways_to_die_tuple['0-2 hours']]),
            "numbers": ",".join([str(i[1]) for i in ways_to_die_tuple['0-2 hours']]),
        },
        "moderates": {
            "labels": "|".join(["{} ({})".format(i[0], i[1]) for i in ways_to_die_tuple['2-30 hours']]),
            "numbers": ",".join([str(i[1]) for i in ways_to_die_tuple['2-30 hours']]),
        },
        "experienced": {
            "labels": "|".join(["{} ({})".format(i[0], i[1]) for i in ways_to_die_tuple['30+ hours']]),
            "numbers": ",".join([str(i[1]) for i in ways_to_die_tuple['30+ hours']]),
        },
    }

    #generate html page
    return render_template("hcsmpstats.html", killers=killers[0:10], witnesses=witnesses[0:10], ways_to_die_html=ways_to_die_html) 

if __name__ == '__main__':
    app.run()
