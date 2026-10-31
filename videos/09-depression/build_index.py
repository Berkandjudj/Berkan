# Baut die Szenen-Hosts und Tonspuren in index.html (Projekt-spezifisch, LEGENDE-Modus: kein HUD).
import re, subprocess, sys, json
def dur(f): return float(subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",f],capture_output=True,text=True).stdout)
cfg=json.load(open("scenes.json"))
scenes=cfg["scenes"]; total=cfg["total"]
hosts="\n".join(f'''      <div id="{i}" data-composition-id="{i}" data-composition-src="compositions/{i}.html"
        data-start="{s}" data-duration="{d}" data-track-index="1" data-track-kind="graphics"
        data-width="1080" data-height="1920" style="z-index: 1"></div>''' for i,s,d in scenes)
P={"whoosh":0.16,"whoosh-short":0.16,"impact-bass-1":0.07,"impact-bass-2":0.07,"pop":0.12,"glitch-1":0.82,"glitch-3":0.2,"error":0.745,"riser":3.47,"click-soft":0.07,"notification":0.1,"whoosh-cinematic":4.5}
lines=[]; tracks={}
for sid,f,t,v in cfg.get("sfx",[]):
    path=f"assets/sfx/{f}.mp3"; d=dur(path); st=round(max(0,t-P[f]),3)
    if f=="riser": d=3.6
    d=round(min(d,total-st),2); tr=12
    while any(not(st>=e or st+d<=s) for s,e in tracks.get(tr,[])): tr+=1
    tracks.setdefault(tr,[]).append((st,st+d))
    extra=' data-fade-in="1.5"' if f=="riser" else ''
    lines.append(f'      <audio id="{sid}" class="clip" src="{path}" data-start="{st}" data-duration="{d}" data-track-index="{tr}" data-volume="{v}"{extra}></audio>')
s=open("index.html").read()
a=s.index("      <!-- Szenen -->"); b=s.index("      <!-- Overlays -->")
s=s[:a]+"      <!-- Szenen -->\n"+hosts+"\n\n"+s[b:]
s=re.sub(r'\s*<div id="hud" data-composition-id="hud"[^>]*></div>','',s,flags=re.S)
s=re.sub(r'(<div\s+id="root"[^>]*?data-duration=")[\d.]+(")', rf'\g<1>{total}\2', s, flags=re.S)
s=re.sub(r'(id="(?:captions|vignette|grain|ambience)"[^>]*?data-duration=")[\d.]+(")', rf'\g<1>{total}\2', s, flags=re.S)
a=s.index("      <!-- Ton -->"); b=s.index("    </div>\n    <script>")
ton=f'''      <!-- Ton -->
      <audio id="voice" class="clip" src="assets/voice.wav" data-start="0" data-duration="{dur("assets/voice.wav"):.2f}" data-track-index="10" data-volume="1"></audio>
      <audio id="ambience" class="clip" src="assets/ambience.wav" data-start="0" data-duration="{total}" data-track-index="11" data-volume="0.9"></audio>
'''+"\n".join(lines)+"\n"
s=s[:a]+ton+s[b:]
open("index.html","w").write(s)
print("Szenen",len(scenes),"SFX",len(lines),"Länge",total)
