import httpx
import urllib.parse
from bs4 import BeautifulSoup
import base64
import re
import time
import pickle
from random import randrange
from copy import copy 
from pathlib import Path

class tweet:
    def __init__(self, link, text, username, nquote, nlike, nretweet, nreply, father="", img=None, video=None):
        self.father = father
        self.link = link
        self.text = text
        self.username = username
        self.nquote = nquote
        self.nlike = nlike
        self.nretweet = nretweet
        self.nreply = nreply
        self.passed = False
        self.img = img
        self.video = video
        self.reply = []
        self.x = 0
        self.y = 0
    
    def print_tree(self, niveau=0):
        print("    " * niveau + self.text + " (" + str(niveau) + ")")
        for enfant in self.reply:
            enfant.print_tree(niveau + 1)
    
    def assign_positions(self, y=0, x_counter=[0]):
        global users
        if self.username not in users:
            users[self.username] = copy(users["color"])
            if users["color"][0] > 25:
                users["color"][0] -= 15
            elif users["color"][1] > 25:
                users["color"][1] -= 15
                users["color"][0] = 255
            else:
                users["color"][0] = 255
                users["color"][1] = 255
                users["color"][2] -= 15
        self.y = y  
        if self.reply == []:  # feuille
            self.x = x_counter[0]
            x_counter[0] += 1
        else:
            for child in self.reply:
                child.assign_positions(y + 1, x_counter)
            # Centrer le parent au milieu de ses enfants
            self.x = int(sum(child.x for child in self.reply) / len(self.reply))
        
def create_html(tweet_dict):
    global to_ret
    global users
    racine = build_tree_from_dict(tweet_dict)
    racine.assign_positions()
    maxx = 0
    maxy = 0
    for i in tweet_dict.keys():
        if tweet_dict[i].x != 0 or tweet_dict[i].y != 0:
            if maxx < tweet_dict[i].x*250:
                maxx = tweet_dict[i].x*250
            if maxy < tweet_dict[i].y*400:
                maxy = tweet_dict[i].y*400
            if tweet_dict[i].video != None:
                to_ret += '<div class="boite" data-x="' + str(tweet_dict[i].x*250) + '" data-y="'+str(tweet_dict[i].y*400)+'" data-color="#' + hex(users[tweet_dict[i].username][0])[2:] + hex(users[tweet_dict[i].username][1])[2:] + hex(users[tweet_dict[i].username][2])[2:] + '">'+ tweet_dict[i].username + " : " + tweet_dict[i].text + " - " + str(tweet_dict[i].nlike) + '<video poster="" controls="" style="width: 110px; height: 70px;">' + tweet_dict[i].video +'</video></div>\n'
            elif tweet_dict[i].img != None:
                to_ret += '<div class="boite" data-x="' + str(tweet_dict[i].x*250) + '" data-y="'+str(tweet_dict[i].y*400)+'" data-color="#' + hex(users[tweet_dict[i].username][0])[2:] + hex(users[tweet_dict[i].username][1])[2:] + hex(users[tweet_dict[i].username][2])[2:] + '">'+ tweet_dict[i].username + " : " + tweet_dict[i].text + " - " + str(tweet_dict[i].nlike) + '<a href="' + tweet_dict[i].img + '" target="_blank"> <img src="' + tweet_dict[i].img + '" alt="Aperçu" style="width: 40px; height: 40px;"> </a></div>\n'
            else:
                to_ret += '<div class="boite" data-x="' + str(tweet_dict[i].x*250) + '" data-y="'+str(tweet_dict[i].y*400)+'" data-color="#' + hex(users[tweet_dict[i].username][0])[2:] + hex(users[tweet_dict[i].username][1])[2:] + hex(users[tweet_dict[i].username][2])[2:] + '">'+ tweet_dict[i].username + " : " + tweet_dict[i].text + " - " + str(tweet_dict[i].nlike) + '</div>\n'             
        else:
            print("https://xcancel.com"+tweet_dict[i].link)
    to_ret += '<svg width="' + str(maxx) + '" height="' + str(maxy) + '" style="border:2px solid black;">'
    for i in tweet_dict.values():
        if i.father != i.link: 
            j = tweet_dict[i.father]
            to_ret += '<line x1="'+str(i.x*250+125)+'" y1="'+str(i.y*400)+'" x2="'+str(j.x*250+125)+'" y2="'+str(j.y*400+333)+'" stroke="blue" stroke-width="2" />\n'
    to_ret += '</svg>'


tweet_dict = {}
users = {"color": [250,250,250]}

def build_tree_from_dict(tweet_dict):
    racine = None

    a = 0
    for noeud in tweet_dict.values():
        a += 1
        if noeud.father == noeud.link:
            racine = noeud
        else:
            parent = tweet_dict.get(noeud.father)
            if parent:
                parent.reply.append(noeud)
            else:
                raise ValueError(f"Parent avec ID {noeud.father} non trouvé.")
    return racine


def find_not_passed():
    global tweet_dict
    for i in tweet_dict.keys():
        if tweet_dict[i].passed == False and tweet_dict[i].nreply > 0:
            return tweet_dict[i]
    return None

def escape(input_string):
    # Convertit chaque caractère non-ASCII en sa représentation %xx
    return urllib.parse.quote(input_string, safe='')

def decodeURIComponent(encoded_string):
    # Décoder une chaîne encodée en pourcentage
    return urllib.parse.unquote(encoded_string)

    # Décoder la chaîne base64
def atob(base64_string):
    decoded_bytes = base64.b64decode(base64_string)
    # Convertir les octets décodés en une chaîne de caractères
    return decoded_bytes.decode('utf-8')

def decode(str):
    return decodeURIComponent(escape(atob(str)))

def check_load_more(html):
    for line in html:
        if "Load more" in line:
            print("load more")
            debut_1 = line.find('<a href="?cursor=')
            fin_1 = line.find('">', debut_1)
            return "?cursor=" + line[debut_1+17:fin_1]
    return None


def gethtml(url, client, referer=None):
    if referer !=  None and referer[-2] == "#":
        referer=referer[0:-2]
    print(url)
    #transport = httpx.HTTPTransport(http2=True,proxy="http://172.188.122.92:80", verify=False)
    
    headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br, zstd",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
            "Sec-Fetch-User": "?1",
            "Priority": "u=0, i",
            "Te": "trailers",
            "Content-Length": "0"}
    
    if referer != None:
        headers["referer"] = referer
    response = client.get(url, headers=headers)
    if response.status_code == 200:
        return response.text
    elif response.status_code == 429:
        print(response.status_code, "to many request")
        a = 10 /0 
        return False
    else:
        print("security")
        soup = BeautifulSoup(response.text, 'html.parser')
        script_tag = soup.find('script', {'type': 'text/javascript', 'data-cfasync': 'false'})
        #Extraire le contenu JavaScript (blablabla)
        if not script_tag:
            return ""
        pattern = r"(var|let|const)\s+(\w+)\s*=\s*([^\s;]+)"
        matches = re.findall(pattern, script_tag.string.strip())
        variables = {}
        for _, var_name, value in matches:
            variables[var_name] = value    
        pattern_line = r"eval\(decodeURIComponent\(escape\(window\.atob\(([^)]+)\)\)\)"
        
        index_begin = script_tag.string.strip().find("window.atob")
        index_end = script_tag.string.strip().find("))));")
        #print(script_tag.string.strip()[index_begin:index_end+1])
        a = ""
        for i in script_tag.string.strip()[index_begin+12:index_end].split(" + "):
            a += variables[i]   
        script_string = decodeURIComponent(escape(atob(a)))
        
        cookie_pattern = r"document\.cookie\s*=\s*'([^=]+)=([^';]+)"
        match = re.search(cookie_pattern, script_string)

        if not match:
            return ""

        headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0", "Content-Length":"22"}
        if referer != None:
            headers["referer"] = referer
        cookie_name = match.group(1)  # Le nom du cookie
        cookie_value = match.group(2)  # La valeur du cookie
        client.cookies.update({cookie_name: cookie_value})
        for line in script_string.splitlines():
            if "var" in line and "parseInt" in line:
                numbers = re.findall(r'\d+', line)
            if "xhttp.setRequestHeader" in line:
                if "_" in line and "syALTIYGwA69YtzUv1FTJftjm4" not in line:
                    debut_1 = line.find("'") + 1  # Le premier guillemet simple après 'setRequestHeader('
                    fin_1 = line.find("'", debut_1)  # Le deuxième guillemet simple après 'X-Requested-TimeStamp'
                    fin_2 = line.find(")", debut_1)  # Le deuxième guillemet simple après 'X-Requested-TimeStamp'
                    headers[line[debut_1:fin_1]] = str(int(numbers[-4]) + int(numbers[-2]))
                elif "'" in line:
                    debut_1 = line.find("'") + 1  # Le premier guillemet simple après 'setRequestHeader('
                    fin_1 = line.find("'", debut_1)  # Le deuxième guillemet simple après 'X-Requested-TimeStamp'
                    debut_2 = line.find("'", fin_1 + 1) + 1  # Le guillemet simple après la virgule
                    fin_2 = line.find("'", debut_2)  # Le deuxième guillemet simple après ''
                    headers[line[debut_1:fin_1]] = line[debut_2:fin_2]
                elif '"' in line :
                    debut_1 = line.find('"') + 1  # Le premier guillemet simple après 'setRequestHeader('
                    fin_1 = line.find('"', debut_1)  # Le deuxième guillemet simple après 'X-Requested-TimeStamp'
                    debut_2 = line.find('"', fin_1 + 1) + 1  # Le guillemet simple après la virgule
                    fin_2 = line.find('"', debut_2)  # Le deuxième guillemet simple après ''
                    headers[line[debut_1:fin_1]] = line[debut_2:fin_2]
        data = {
        "name1": "Henry",
        "name2": "Ford"}
        response = client.post(url, headers=headers, data=data)
        headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:138.0) Gecko/20100101 Firefox/138.0",
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                    "Accept-Language": "en-US,en;q=0.5",
                    "Accept-Encoding": "gzip, deflate, br, zstd",
                    "Upgrade-Insecure-Requests": "1",
                    "Sec-Fetch-Dest": "document",
                    "Sec-Fetch-Mode": "navigate",
                    "Sec-Fetch-Site": "none",
                    "Sec-Fetch-User": "?1",
                    "Priority": "u=0, i",
                    "Te": "trailers",
                    "Content-Length": "0"}
        if referer != None:
            headers["referer"] = referer
        response = client.get(url, headers=headers)
        return response.text
    
def extract_tweets_from_html(html_code, url):
    global tweet_dict
    i = 0
    cnt = 0
    after = 0
    while i < len(html_code):
        cond = html_code[i].find('<div class="reply thread thread-line')
        if cond == -1:
            cond = html_code[i].find('<div id="m" class="main-tweet"')
        if cond != -1:
            cnt = html_code[i].count('<div', cond)
            cnt -= html_code[i].count('</div', cond)
            text = ""
            username = ""
            tweetlink = ""
            nreply = -1
            nlike = -1
            nretweet = -1
            nquote = -1
            links = []
            img = None
            video = None
            i += 1
            while cnt > 0:
                cnt += html_code[i].count('<div')
                cnt -= html_code[i].count('</div>')
                if username == "" and "username" in html_code[i] and "title" in html_code[i]:
                    debut = html_code[i].find("@")
                    fin = html_code[i].find('"', debut)
                    username = html_code[i][debut:fin]
                if text == "" and "tweet-content media-body" in html_code[i]:
                    debut = html_code[i].find('"auto">') + 7
                    fin = html_code[i].find('</div>', debut)
                    if fin == -1:
                        while fin == -1:
                            text += html_code[i][debut:]
                            debut = 0
                            i += 1
                            cnt += html_code[i].count('<div')
                            cnt -= html_code[i].count('</div>')
                            fin = html_code[i].find('</div>', debut)
                        text += html_code[i][0:fin]
                    else:
                        text += html_code[i][debut:fin]
                if tweetlink == "" and "tweet-date" in html_code[i]:
                    debut = html_code[i].find('href="') + 6
                    fin = html_code[i].find('"', debut)
                    tweetlink = html_code[i][debut:fin]
                    if url.split(".com")[1] == tweetlink:
                        after = 1
                if nreply == -1 and "icon-comment" in html_code[i]:
                    debut = html_code[i].find('</span>') + 7
                    fin = html_code[i].find('</div></span>', debut)
                    nreply = html_code[i][debut:fin]
                    if nreply == "":
                        nreply = 0
                    else:
                        nreply = int(nreply)
                if nretweet == -1 and "icon-retweet" in html_code[i]:
                    debut = html_code[i].find('</span>') + 7
                    fin = html_code[i].find('</div></span>', debut)
                    nretweet = html_code[i][debut:fin]
                    if nretweet == "":
                        nretweet = 0
                if nquote == -1 and "icon-quote" in html_code[i]:
                    debut = html_code[i].find('</span>') + 7
                    fin = html_code[i].find('</div></span>', debut)
                    nquote = html_code[i][debut:fin]
                    if nquote == "":
                        nquote = 0
                if '<div class="attachment image">' in html_code[i]:
                    debut = html_code[i].find('href="') + 6
                    fin = html_code[i].find('"', debut)
                    img = html_code[i][debut:fin]
                if '<div class="attachment video-container">' in html_code[i]:
                    debut = html_code[i].find('<source src=')
                    fin = html_code[i].find('</video>', debut)
                    video = html_code[i][debut:fin]
                if nlike == -1 and "icon-heart" in html_code[i]:
                    debut = html_code[i].find('</span>') + 7
                    fin = html_code[i].find('</div></span>', debut)
                    nlike = html_code[i][debut:fin]
                    if nlike == "":
                        nlike = 0
                i += 1
            if tweetlink != "":
                #print(tweetlink, text,  url.split(".com")[1])
                if tweetlink not in tweet_dict:
                    tweet_dict[tweetlink] = tweet(tweetlink, text, username, nquote, nlike, nretweet, nreply, url.split(".com")[1], img, video)
                    if len(tweet_dict) == 1:
                        tweet_dict[tweetlink].passed = True
                elif after == 2:
                    tweet_dict[tweetlink].father = url.split(".com")[1]
                if after == 1:
                    after = 2
        else:
            i += 1

#except:
    #if you want use a proxy
    #transport = httpx.HTTPTransport(http2=True,proxy="http://localhost:8080", verify=False) 
    #with httpx.Client(transport=transport, http2=True, timeout=10) as client:

with httpx.Client(http2=True, timeout=10) as client:

    url = input ("url:")
    if "x.com" in url:
        x = url.find("x.com")
        newurl = url[:x+1] + "cancel" + url[x+1:]
        url = newurl
    html_code = gethtml(url, client).splitlines()
    extract_tweets_from_html(html_code, url)
    print(len(tweet_dict))

    lm = check_load_more(html_code)
    while lm != None:
        html_code = gethtml(url[0:-2]+lm, client, url[0:2]+"?").splitlines()
        extract_tweets_from_html(html_code, url)
        lm = check_load_more(html_code)

    tw = find_not_passed()
    while tw != None:
        tw.passed = True
        newurl = "https://xcancel.com" + tw.link
        try:
            html_code = gethtml(newurl, client).splitlines()
        except:
            print("fail sleep 300")
            time.sleep(300)
            print("resume")
            tw.passed = False
        else:
            #num_before = len(tweet_dict)
            extract_tweets_from_html(html_code, newurl)
            #num_after = len(tweet_dict)
            #if num_after - num_before < tw.nreply:
                #print("AHHHHHHHHHHHHHHHHH")
                #tw.passed = False
            print(len(tweet_dict))
            lm = check_load_more(html_code)
            while lm != None:
                try:
                    html_code = gethtml(url[0:-2]+lm, client,newurl[0:-2]+"?").splitlines()
                except:
                    print("fail sleep 300")
                    time.sleep(300)
                    print("resume")
                else:
                    extract_tweets_from_html(html_code, url)
                    print(len(tweet_dict))
                    lm = check_load_more(html_code)
        tw = find_not_passed()        


print(len(tweet_dict))

# Chargement
    

to_ret = '''<!DOCTYPE html>
<html lang="fr">
<head>
  <meta charset="UTF-8">
  <title>tweet to tree</title>
  <style>
    .boite {
      position: absolute;
      width: 220px;
      height: 333px;
      background-color: #d1f0d1;
      border: 1px solid #555;
      padding: 10px;
      box-shadow: 2px 2px 6px rgba(0,0,0,0.2);
      font-family: sans-serif;
    }
  </style>
</head>
<body>'''

create_html(tweet_dict)
to_ret += """<script>
    document.querySelectorAll('.boite').forEach(function(boite) {
      const x = boite.getAttribute('data-x');
      const y = boite.getAttribute('data-y');
      const color = boite.getAttribute('data-color');
      boite.style.backgroundColor = color;
      boite.style.left = x + 'px';
      boite.style.top = y + 'px';
    });
  </script>

</body>
</html>"""

#for i in tweet_dict.values():
#    print("[", i.text, i.link, i.father, "]")
    

script_dir = Path( __file__ ).parent.absolute()
path = str(script_dir) + "\\ret.html"
with open(path , "w", encoding="utf-8", errors="replace") as file:
    for line in to_ret:
        file.write(line)