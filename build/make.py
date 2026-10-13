"""Generate the artifact page and the hosted page (repo index.html) from app.src.html."""
import re,shutil
B='/home/claude/build/'
s=open(B+'app.src.html').read();css=open(B+'leaflet.css').read();page=s.replace('/*LEAFLET_CSS*/',css)
open('/home/claude/app/index.html','w').write(page)
build=re.search(r"const BUILD='([^']+)'",s).group(1)
head=f'''<!doctype html>
<html lang="he" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="build" content="{build}">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<meta name="description" content="תוצאות הבחירות לכנסת ה-25 לפי שכונות: אחוז הצבעה, מפלגה מובילה ושיעורי מפלגות וגושים.">
<style>:root{{padding-top:env(safe-area-inset-top,0px);padding-bottom:env(safe-area-inset-bottom,0px)}}body{{margin:0}}img{{max-width:100%}}[hidden]{{display:none!important}}</style>
'''
i=page.index('<div id="app"');out=head+page[:i]+'</head>\n<body>\n'+page[i:]+'\n</body>\n</html>\n'
for d in ('/home/claude/netlify/israel-voting-map','/home/claude/israel-vote26'):
    open(d+'/index.html','w').write(out)
for f in ('app.src.html','build.py','match.py','match2.py','pseudo.py','base.py','leaflet.css','make.py'):
    shutil.copy(B+f,'/home/claude/israel-vote26/build/'+f)
print('build',build)
