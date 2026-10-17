# Kontext projektu CS4208

Stav prevzatý 2026-10-08 zo zdieľanej konverzácie a miestnych README.
Zdroj: https://chatgpt.com/share/6ac6c415-df28-83eb-a827-1a52b06f234d

## Cieľ a prostredie

Odstrániť plechový zvuk vstavaných reproduktorov MacBook Pro 2015,
MacBookPro11,4, Cirrus Logic CS4208, SSID 0x106b8000.
V konverzácii bol hlásený kernel 7.0.0-38-generic (zdroje 7.0.0-38.38)
a PipeWire 1.6.2. Používateľ na začiatku uviedol Ubuntu 24;
presnú aktuálnu verziu distribúcie treba v prípade potreby overiť.

## Doterajší postup

- Pôvodné nastavenie používalo model=mbp11 a hda-jack-retask patch.
  Skúmalo sa stlmovanie Speaker/Bass Speaker a zásahy PipeWire do mixéra.
  Bez PipeWire sa ovládače dali stlmovať nezávisle, ale príčina farby zvuku
  tým nebola potvrdená. Skúšalo sa aj api.alsa.soft-mixer.
- Používateľ chcel preskúmať podporu ovládača a AppleHDA/PipeWire DSP.
  Základom extrakcie bol projekt MrHogun/imac-a2115-linux-audio.
  Jeho pôvodný generátor pre tento dataset hlásil chýbajúci
  DspGainStage instance 4.
- Sú dostupné layout128.xml.zlib a extrahovaný layout128-dsp.json.
  Výber layout128 variant 0 na tomto konkrétnom Macu nie je potvrdený.
- Štvor-kanálový HDA stream s formátom 0x13 bol tichý, stereo 0x11 hralo.
  Riešením testu je vlastný kernelový patch poskytujúci dva stereo PCM,
  každý s vlastným streamom a offsetom kanálov 0.

## Potvrdené používateľovým posluchom

- cs4208-split-test: primary-left/right a bass-left/right všetky hrali.
  Pri súčasnom teste boli počuteľné oba tóny a basový pokračoval po skončení
  primárneho. DAC 0x03 mal stream 5, DAC 0x04 stream 6.
  PCM hw:PCH,0 a hw:PCH,2; S16_LE, stereo, 48000 Hz.
- cs4208-pipewire-test: používateľ potvrdil, že všetko hralo podľa testu.
  Virtuálny cs4208.split4 smeruje FL/FR na primárny PCM a RL/RR na basový PCM.
  RL/RR sú označenia smerovania, nie fyzické zadné reproduktory.
- cs4208-layout128-eq: po ďalších tichých DSP pokusoch verzia cez bq_raw
  s explicitnými koeficientmi hrá na oboch stranách, ale potichu.

## Posledný stav konverzácie

DSP výstup: MacBook Speakers (layout128 EQ test), uzol cs4208.dsp.
DSP útlm je -12 dB. Používateľ zvýšil virtuálnu hlasitosť podľa pokynu na 100 %,
ale stále hlásil tiché prehrávanie. Následne nastavil hardvérový Master na 90 %:
Playback 114/127, -6.50 dB, zapnutý. Predtým bol Master na -20 dB.

Posledná nezodpovedaná otázka: je po tejto zmene hudba dostatočne hlasná
a znie plnšie/s basmi, alebo zostáva plechová? Zlepšenie kvality EQ zatiaľ
nie je potvrdené. Historické hodnoty nie sú aktuálne meranie živého systému.

## Miestne časti projektu

- cs4208-source: dodané kernelové zdroje a archívy.
- cs4208-split-test: experimentálny kernelový patch, build/inštalácia,
  testy dvoch PCM a rollback. Nie je DKMS; viazaný na konkrétny kernel.
- cs4208-pipewire-test: samostatný basový adapter a combine-stream.
- cs4208-layout128-eq: generátor, konfigurácia, dataset, validácia a DSP testy.
- imac-a2115-linux-audio: pôvodný projekt extrakcie AppleHDA a vstupné dáta.

## Otvorené technické otázky

Statická EQ obsahuje 73 biquad filtrov. Päť filtrov typu 6 je vynechaných.
Interpretácia typov filtrov a výber layoutu zostávajú predpokladmi portu.
MozartCompressor, Loudness, DualBandCompressor, BuzzKill a SplineLimiter
nie sú emulované; clamp vzorky nie je náhradou týchto algoritmov.
Fyzické priradenie vetiev k meničom a výslednú kvalitu treba ďalej posúdiť.
README niektorých balíkov ešte uvádzajú stav pred úspešnými posluchovými testami.
Zdieľaná stránka pri prílohách ukazuje iba označenie nahratia; ich pôvodný obsah
nebol zo zdieľania načítaný. Miestne súbory treba kontrolovať priamo.

## Ako nadviazať

Aktualizácia po ďalšom posluchu 2026-10-08: po pripojení/odpojení slúchadiel
boli Speaker aj Bass Speaker na 0 % a off. Obnovenie na 100 % unmute obnovilo
zvuk; Master zostal 90 %. Automatické prepínanie slúchadiel nie je opravené.
Bez EQ bol 200 Hz počuteľný výrazne na basovej vetve, na primárnej nie;
1000 Hz hralo na oboch. Pri tichom offline A/B teste basovej vetvy boli
200/400 Hz počuteľné, bypass trochu hlasnejší; 100 Hz nebolo počuť ani pri
bypasse so zachovaným útlmom -12 dB. Toto nepreukazuje akustický limit meničov.

Vypočítaná odozva nasadeného bq_raw profilu: basová vetva 100 Hz -25.9 dB,
200 Hz -10.94 dB vrátane headroom -12 dB. Vstupné HP 112/182 Hz sú aj v XML.
Vytvorený a nasadený samostatný profil cs4208.simple, drop-in
91-cs4208-simple.conf, súbory v cs4208-simple-crossover. Výhybka 3 kHz,
basová HP 150 Hz, headroom -18 dB, počiatočná hlasitosť 50 %. Je vybraný ako
predvolený výstup; pôvodný cs4208.dsp je zachovaný. Vznik oboch uzlov a linky
do split4 overené. Posluch hudby cez jednoduchý profil ešte používateľ nepotvrdil.
Prepínanie: bash ~/sound_driver/cs4208-simple-crossover/select.sh simple|original.
Po reštarte služieb trvala inicializácia približne 50 s kvôli RTKit DBus NoReply.
Používateľ následne hlásil, že jednoduchý profil je skoro rovnaký a basy veľmi
slabé; v macOS na tomto kuse bol zvuk výrazne lepší. Pri kontrole bol samostatný
cs4208.bass na wpctl 0.57 (channelVolumes 0.180686), ostatné následné uzly na 1.
Basový výstup bol nastavený na 1.0; overené, že Master zostal -6.5 dB a
Bass Speaker 100 % on. select.sh pre oba profily teraz normalizuje cs4208.bass
na 1.0/unmute. Posluch po odstránení tohto dodatočného útlmu ešte nie je potvrdený.
Používateľ potvrdil, že basy stále chýbajú aj po normalizácii basového sinku.
Živé digitálne meranie multisinusom cez cs4208.simple → split4 → monitor
cs4208.bass potvrdilo zhodu oboch kanálov s výpočtom: 100 Hz -25.83 dB,
200 Hz -19.19 dB, 400 Hz -18.09 dB, 1000 Hz -18.10 dB vzhľadom na vstup.
Výsledok v cs4208-simple-crossover/measurement-result.json. Mikrofón nebol použitý.
pw-record po presnom sample-count skončil kódom 1, ale zapísal očakávaných
288000 stereo f32 rámcov (2304000 bajtov), s konečnými nenulovými vzorkami.
Pripravený compare-branches.py na izoláciu basovej/primárnej/oboch vetiev
pri hudbe, po 10 sekundách, s obnovením pôvodných výstupných channelVolumes.
Používateľ pri izolácii potvrdil plnšiu/tlmenejšiu basovú vetvu, ale miestami
päťsekundové ticho počas podmazu, ktorý je počuť na inom zariadení.
Dočasne bol zmenený HP basovej vetvy zo 150 na 100 Hz cez živé bq_raw
koeficienty, bez zmeny ostatných filtrov či hlasitosti. Spätné čítanie oboch
kanálov z pw-dump zhodu potvrdilo. Nástroj bass-cutoff.py 100|150, zmena platí
do reštartu služieb (disková konfigurácia stále 150 Hz). Posluch po tejto zmene
ešte nepotvrdený. Vyžiadaná skladba a čas chýbajúceho podmazu.
Úsek: https://www.youtube.com/watch?v=D3iu5ff7gic, prvých 6 s. Po HP100 používateľ
stále podmaz nepočuje. Digitálne meranie intro-measurement.json ukázalo relatívne
v pásme 30–2000 Hz: 60–100 Hz 90.6 %, 30–60 Hz 6.4 %, 100–150 Hz 2.6 %,
150–300 Hz 0.4 %. Prenos basovej vetvy 60–100 Hz -25.5 dB vrátane -18 dB
vstupného útlmu. Celý 10s vstupný záznam peak -3.7 / RMS -17.5 dBFS,
basový peak -21.8 / RMS -42.9 dBFS. Nejde o akustické meranie.
Pripravený test-low-bass.sh: 80/100/150/200 Hz priamo cez split4 basový pár,
každý 2 s, peak -24 dBFS. Predchádzajúci bypass 100 Hz mal -36 dBFS, takže
jeho nepočuteľnosť sama osebe nedokazovala fyzický limit meničov.

Najprv zistiť používateľov výsledok hudby po Master 90 %.
Pred ďalšími úpravami skontrolovať aktuálne miestne aj nasadené konfigurácie,
pretože počas diagnostiky sa menili. Zachovať už potvrdenú funkčnú cestu
dva stereo PCM → PipeWire split4 → DSP. Nepoužívať nefunkčný hardvérový
profil Surround 4.0/2.1 ako náhradu za split PCM.

Inicializácia preverovaná 2026-10-08: výsledky v cs4208-investigation/README.md.
Po poslednom priamom teste používateľ počul150/200Hz, nepočul80/100Hz.
Aktuálny codec snapshot potvrdil DAC03/04 a piny12/13 D0 OUT, stream5/6,
obe úrovne0x72; GPIO0 enabled/output/high; modelname mbp11. Layout128
IntSpeaker MuteGPIO0 sa zhoduje s použitým GPIO. CodecConfig navyše obsahuje
AnalogueSupply5 a FET GPIO4/5, význam pre basy nepreukázaný. Split patch
nemení vendor inicializáciu. Priame čítanie vendor registrov blokuje potreba
sudo hesla; pripravený read-coefficients.py zachováva index, nezapisuje hodnoty.
Žiadna potvrdená chyba inicializácie ani overená oprava zatiaľ nenájdená.

Používateľ úspešne spustil čítanie registrov. linux-coefficients.json:
33=0001,34=1c01,processing=1 — zhodné s lokálnym Linux ovládačom.
Ostatné00=0,01=0,02=003a,03=fbaa,04=9f9f,1f=0400; bez referencie
z macOS na rovnakom modeli ich nepovažovať za dôkaz chyby. Porovnanie
v initialization-comparison.json. Nastavenia zvuku sa nemenili.

Používateľ dodal lemmyg/t2-apple-audio-dsp a nguyenngocanh94/AppleHDA10.11.5.
Preskúmané a stiahnuté iba do cs4208-investigation, bez inštalácie.
Zistenia reference-links-findings.md: T2 má Bankstown virtuálne basy,
kompresiu/limiter/loudness/model-specific FIR. Možná inšpirácia pre označený
A/B test, nie priamy profil11,4 ani dôkaz Apple algoritmu. AppleHDA archív
layout128 byte-identical existujúcemu; HardwareConfig jediný ConfigData
pre14f1510f layout3, Platforms chýba PathMap76. Preto tento balík nie je
úplná stock referencia pre128. Zatiaľ sa živé zvukové nastavenia nemenili.

Nasadený cs4208-virtual-bass/92-cs4208-virtualbass.conf, nový sink
cs4208.virtualbass (MacBook Speakers (virtual bass test)), teraz vybraný,
volume1.0, bypass0. Plugin Bankstown1.1.0-3build1 zo systémového apt repozitára
rozbalený lokálne a skopírovaný do ~/.lv2/bankstown.lv2, bez systémovej
inštalácie. Parametre floor50 ceil120 final_hp150 amt1 sat_second2 sat_third3
blend.5. Zapojený PRED -18dB headroom a pôvodnou výhybkou3k/HP150.
Profil simple aj original zachovaný; runtime simple HP100 sa pri reštarte
vrátil na diskových150Hz. Nie sú použité T2 FIR ani iné modelové zisky.
Skontrolovaný plugin offline a reálna PipeWire cesta monitorom basového sinku:
80Hz input -12dBFS, výstup off80=-41.3,160=-176.38,240=-121.67dBFS;
on80=-41.89,160=-50.86,240=-59.87dBFS. Harmonické teda dorazia na basový
výstup; nejde o akustický výsledok. Súbory plugin-check/routing-check.json.
select.sh on|off bypassuje iba Bankstown (rovnaký headroom/výhybka),
simple|original návrat. Skript nastaví volume1.0 a default; pactl tu chýba,
prípadný pripnutý playback treba znovu spustiť alebo vybrať výstup v appke.
Posluch hudby s profilom zatiaľ čaká na používateľa. Používateľ ponúkol získať
AppleHDA z bežiaceho macOS priamo na tomto Macu, ak test nepomôže.

Používateľ nepočul úvod ani s virtuálnymi basmi, ale všimol si výrazne
nižšiu hlasitosť MacBook Speakers profilov vs priamy bass. Kontrola našla
nový split4 channelVolumes0.487391 (~-6.24dB) plus virtualbass headroom-18dB.
Split4 teraz normalizovaný1.0; virtualbass headroom zmenený na-12dB v
živom grafe aj generátore/diskovom dropine. Netto zvýšenie12.24dB.
select.sh normalizuje aj split4. Master sa nemenil. Simple/original zisky
nezmenené, spoločný split im však tiež zvýši výstup. Čaká nový posluch.

Spresnenie: opakované digitálne meranie po zmene potvrdilo zvýšenie
iba6dB (harmonická160Hz z-50.86 na-44.86dBFS,240Hz z-59.87 na-53.87).
Vplyv split4 channelVolumes0.487 na skutočný signál teda nepotvrdený;
neprezentovať ho ako ďalší dokázaný útlm ani tvrdiť skutočné zvýšenie12dB.
Nový profil má stále zámerný-12dB headroom oproti priamemu bass sinku.

Ani po potvrdenom+6dB virtuálnom profile používateľ nepočuje intro.
Ďalej nezosilňovať naslepo. Pripravený cs4208-investigation/collect-macos-audio.sh
pre zber priamo na macOS tohto zariadenia: kompletný AppleHDA.kext, sw_vers,
system_profiler SPAudioDataType a ioreg IOService, ZIP na ploche. Nevyžaduje
sudo a nemení audio nastavenia. ioreg poskytne výber layoutu/variantov a
routing metadata, NIE automaticky runtime vendor coefficient dump.
Používateľ má pri posluchu v macOS znova porovnať rovnaké prvé6s skladby,
aby sme mali aktuálnu akustickú referenciu na rovnakom hardvéri.

Používateľ dodal mac_data triZIP priamo z macOS. Extrahované mac_data/extracted.
Podrobný výsledok cs4208-investigation/macos-reference/FINDINGS.md.
Potvrdené macOS10.15.6/AppleHDA283.15, layout128, DeviceEqID786432→variant0;
IntSpeaker DSP v novomlayout128 totožný s pôvodným (ibaMicNumOfIntMics rozdiel).
PlnáPathMap76 potvrdzuje DAC03→pin12 kanály1/2, DAC04→pin13 kanály5/6;
primárny hlasitosť publishes, bass nie (NEZNAMENÁ dôkaz bass gain0dB).
Výpisy volume25/50/75 published126? skutočne64/90/110; bass lenmute.
Z binárky AppleHDA staticky dokázané initForNodeID CS4208 kroky coef03&0fff,
coef01&fc00,coef00|4; vtable slot5c8read/5d0write potvrdený symbolmi.
StarýLinux00=0/03=fbaa sa od tohto initkódu líši (očakávané po týchto
maskách00=4/03=0baa), nejde o konečný runtime snapshot macOS ani dôkaz basy.
Pripravený try-init-bits.py --apply: sudo,10sA→20sB(two masks)→restoreA,
záloha predzmenou, readback,finally rollback+INT/TERM. Zatiaľ NEBOL reálne
spustený. Test masiek a simulovaného mid-write failure rollback PASS bez HW.
Workaround protected40/50 seq nájdený ale neaplikovať bez overenia.
DspFuncEQ typ0/1 zbinárky low/high;type6 highshelf konštrukcia pevnýslope,
vynechané6 sú2.79–6.35k takže nejde o priame chýbajúce60–100Hz zosilnenie.
Položená async otázka, či používateľ teraz v macOS overil úvod tejistej skladby.
Používateľ potvrdil aktuálnym posluchom, že prvých6s rovnakej skladby
je v macOS na tomto Macu počuteľných. Nejde teda len o historickú spomienku.

Používateľ po maskedinitA/B hlási „neobjavil sa“ (podmaz). Nezavádzať
00|4/03&fff do trvaléhoovládača ako opravu. Dveinitbackup potvrdzujú
štartovacie00=0,01=0,03=fbaa ale nie finálny runtime state.
Ďalej statickyoverené Loudness46096 volágetMasterGain3937c a20log10;
zosilnenie je závislé na mastergain, nemožno bezpresnejpropagácie hlasitosti
nasadiť nový guessedEQ. Žiadne nové živé nastavenia vtomtoťahu.
Asyncotázka čaká: počuť úvod6s pri priamo zvolenom CS4208 Bass Stereo(test)?
To ešte nebolo výslovnepotvrdené: používateľ iba hlásil že tento výstupje
hlasnejší nežMacBookSpeakersprofily. Výsledok odlíši DSPproblém od analogpath.

Používateľ nemal CS4208 Bass Stereo(test) v UI. Aktuálna kontrola potvrdila
cs4208.bass chýba, hardvérový PCM2 však existuje/free/closed. Journal pri
štarte09:09:42: Cannot get card index for PCH, hw:PCH,2 playback open failed
No such device. Manual nofail adapter bol preskočený pred registráciou ALSA
karty; vyššie DSPprofily žili aj bez basovejvetvy. Preto posledné posluchové
testy bez potvrdenej basovejvetvy NIE SÚ spoľahlivé negatívne výsledky
(vrátane maskedinitA/B ztohtobootu). Predchádzajúce
merania virtualbass routing-check boli zpredchádzajúceho behu a mali bass.
Oprava: wait-for-cs4208.py (bounded30s exactDMI/codecid/SSID/PCMname) ako
userpipewire.service.d/20-cs4208-wait.conf ExecStartPre; daemonreload+
restartaudio. Pripravený select-bass-direct.sh výberpriamobass75% default.
Návratvirtualbass/select.sh on normalizuje bass a split1.0. Čakáoverenie
basovéhoadaptéra/linkov po pomalom štarteRTKit, potom priamy posluchúvodu.
Po obnove overené cs4208.bass36 a dvaactive combine→basslinky.
restored-bass-check.json uložený. Terazpredvolený priamy cs4208.bass75%,
beznašichDSP; používateľ máznovaspustiťúvodskladby. Výsledokčaká.
Po obnovepriamehobasssink75% používateľ stále nepočuje6súvod.
Nedokazuje tosaméhardvérovúchybu (úroveň, routovanieprehliadača).
Pripravený cs4208-bass-phase-test/test.sh:200Hzkontrola(-24dBFS), potom6s
originálneho lokálnehointroinputaudio left/right/both/inverted-right.
Žiadnyboost aniHWnastavenie,explicitpw-play targetcs4208.bass, teda nezávisí
odbrowserpinnedroute. Zdrojsamplesfade5ms16bit,stereocorrelation.8429,
source-check.json. Basovýnode36hw:PCH,2existujevolume75%/unmute.
AnalyzovanýrequestCPset4000:volanievsetPowerStateje obmedzené pinDefault
DeviceType0lineout/2headphone. Naše12/13 sútype1speaker, takže žiadny dôvod
aplikovať4000napájacíbit. Takýtest anioprava neboli urobené.

Nový posluch phase-test: podmaz počuteľný potichu pri left/right/both aj
inverted, inverted znel horšie. Nepovažovať za potvrdenú chybu polarity;
polaritu nemeníme. Explicitný lokálny playback teda podmaz prenesie.
Aktuálna live kontrola bass36 volume1/channelVolumes[1,1],muteFalse;
split45 tiež1. Predošlý údaj75% je neaktuálny. Virtualbass bypass0,
headroom.251189(-12dB), bassHP150Hz; DSP tiežheadroom-12dB.
Pripravený cs4208-bass-phase-test/compare-profiles.py: rovnaký both.wav
explicitne A bass/B dsp/C virtualbass, bez zmien nastavení. Súčasne
8s bassmonitor pri každom6s playbacku, uložíprofiles-levels.json a f32.
Zatiaľ nespustené; čaká používateľov posluch A/B/C.
Prvý pokuscompare-profiles skončilpoA: pw-record vtejtoverzii pri
sample-count normálnevracia1 bezstderr ajpri úplnomzázname. Reprodukcia
krátkymtichým4800frame záznamom:exit1,38400bytespresne. A obsahuje768000
finitefloatvzorieka peak.642914,tedaplný8s záznam. Skriptopravenýakceptuje
ibaexit1bezstderr,potomvždyvalidujeúplnúdĺžkuafinite;inéchybyzastaví.

Používateľ počulnajlepšieA. Úspešnécompare-profiles meranie bassmonitor:
A RMS-18.31/peak-3.84; B layout128 RMS-48.56/peak-19.90;
C virtualbass RMS-41.73/peak-16.83 dBFS. VeľkýútlmDSPpotvrdený.
Pripravenýcs4208-balanced-test: draft93conf zo simple,headroom-6dB,
bassHP60Hz,3kHz4thordercrossover/clampsponechané. NENAINŠTALOVANÉ.
prepare.py offlinepresnevyrenderuje4chintroFLFRRLRR,predikuje bass
RMS-8.281dB oprotidirect,peak.35777 bezclippingu. test.sh explicit
A directbass/B4chrender→split4, beznastavení. Čakáposluch.

Používateľ novýbalancedB počuje trochu zreteľnejšie, žiada viac a nevie
posúdiťvyššiuhlasitosť. Balancedupravenýbass+3dB:primary-6/bass-3dB,
HP60/LP3k. prepare.py pridáva bass_gainza forkpredHP,offline renderrovnaký.
RMSoproti direct-5.281dB,peak.50537. Config93nainštalovanýuserpipewire;
audioservicesrestart. Pripravenýselect.sh a README. Čakáoverenieživého
profile/default/linkov,potomplnáhudbaposluch. Registry nemeníme.

Balanced56liveoverený/defaultcs4208.balanced,headroom.501187,
bass_gain1.412538,bassHPb0.994462. Bass37a split46unity/unmute,
2active linkydobass,4activebalanced→split. Live-check.jsonuložený.
RTKitNoReply50sajdiagnostickýmklientom;scopedPIPEWIRE_PROPS={module.rt=false}
obchádzapríčinučakania diagnostikybezúpravyservera. Profilužzvolený.
Používateľmábežnúhudbuznovuspustiťavybraťbalancedvappakbrowserostane
napôvodnomroute;začaťnižšieapostupnezvýšiťaposúdiťpodmazajcelúskladbu.

Používateľbalanced pri nízkejhlasitosť vôbecnepočujeúvod,pri maxlentrochu.
Latest-live.json:balanced56running, bass37/split46unity,Firefoxidle
(tedaprávepozastavený), GNOMEnastaveniacapturesink. HardwareMaster116
-5.5dB; Speaker/BassSpeaker1270dB usercontrols, skutočnéDAC03/04amp74
(-5.5dB,masteraplikovaný);D0 správnestream6/5channel0. Bezmutácií.
Ďalšítestmaskedinitopodstatnenýlebo minulébootbasschýbal. Novýwrapper
cs4208-balanced-test/test-codec-init.sh: bezsudo, guardbass+balanced,
sudo-v,play-loop explicitbalancedlokálny6sintro,pôvodnýtry-init-bits.py
cezsudo-n(10sA/20sB/finallyrestore),8srestoredA,trapstopplayback.
Syntaxoverená,HWnespustený. Čakáposluch;žiadneďalšiegainzmeny.

Používateľretestmaskedinitsoverenožijúcimbass: Bnebolo výraznejšie.
Nezaviesťinitmaskyakoopravu. Najnovšíbackup075824orig0/0/fbaa.
Priamyreadbacksudo-nnebolmožný(žiadaauth);scriptfinallyrollbacknenahrádza
nezávislépotvrdenie. BezďalšíchHWmutácií. Ďalšíofflineharmonictest:
prepare-harmonics.py používaactualBankstownLV2 rovnaképaram1/50/120/150/2/3/.5,
extrahujewet=output-input,dodatočný2xHP150Hzodstránifundamentalresidual,
pridávatoibadobassbalancedbranch(-3dB,HP60,LP3k). Pôvodnýsignálgain
rovnaký,primarynezmenený. Skúšaamount1/2/4 a vyberápeak<=.75;vybraný4
peak.65175,bassRMS+0.46dB oprotibalanced. NiejeemuláciaAppleDSP.
intro-harmonics.wav pripravený, test-harmonics.sh A balanced/B harmonics
explicit4chsplit4, žiadnenastavenia/HWzmeny,strednáhlasitosť. Čakáposluch.
StarývirtualbasspriA/Bmal-23dBcelkovýútlm,tentoraznevhodnýútlmnepridávame.

Používateľpotvrdil: Bznieurčitelepšie(harmonics). Pripravený
generate-harmonics-profile.py,nový94confcs4208.harmonics(description
MacBookSpeakers(enhancedbass)). Exactgraph: raw→balancedheadroomdry,
raw→LV2Bankstown;wet=LV2out-raw(mixernegativegain),2xHP150,
mixwetwithdryatfork,wetgain4*.501187,potomexistingbass_gain1.4125,
HP60/LP3k/clamp. Primarynezmenená. Fileinstalledaudiorestarted,select
spustenýčakáRTKit. Pripravenýverify-harmonics-live.py:záznam8s
monitorbass,6sintroexplicitnovýprofil,porovnaniealignedtoofflineB
RMSerror<.005,guardunity/noplayingapp. Pendingexecution/selectionverify.

Dôležitáopravaživéhographu:installedmixerclampsnegativeGain2→0!
PrvýliveverifyfailedRMSerror.822/peak.8 vsB.6517;livewetGain2=0confirmed.
Napriekinstalledupmixtemplatekonfigurácii-.707 nemožnopoužiťmixernegativegain.
Opravenégenerate-harmonics-profile.py:linearinvertMult-1predmixerGain2+1.
Conf94reinstalled,restart+select+liveverifyprocess22917beží.

FinálnyliveverifyPASS:RMSerror.000206769(0.0207%),peak.6517126
vsB.6517334; profilpresnezodpovedáúspešnémuB. Defaultcs4208.harmonics
selected;enhanced-live.jsonsnapshot. PriamylinearMult-1funguje.
NeclaimovaťplnémacOSbasysplnené; používateľmáposúdiťcelúhudbupotichu
ajbežne,vybraťenhancedbassvbrowserakrouteostanepinned.

Používateľžiadaodložiťaktuálnystavnareinstallfreshsystempredďalšou
analýzoumac_data. Hotovýsamostatnýfrozenbalík saved-setup/
cs4208-enhanced-bass-2026-10-08 +tar.gz+sha256. Readme.mdSlovak,
source+presnánainštalovanáKO(sha01bda990...),kernelpatch/build/install/rollback,
configs80/93/94,WPsoftmixer+48k,LV2+licenses,bootwaitcopydo.config
bezpôvodnejworkspacecesty. manage-user.py backedupinstall/remove/select/check,
--dry-run,--staging-root(pretestbezslužieb),ovládačviazaný7.0.0-38-generic.
SourcesrebuildPASSgcc15→srcversion51E4CD1B66481DA40ABC644. Stagingfresh
aexistingbackuprestorePASS,guardchangedfilePASS,pathswithspacesPASS,
relocatedtarinstall/removePASS,SHA256SUMSverified. LiveconfigsaudioNEMENENÉ.
Needitovaťfrozenbalíkpriďalších experimentoch;pracovaťmimoneho.

Používateľschválil3krokyDspLoudness zmac_data. Hotovýofflineexperiment
cs4208-macos-loudness/{model.py,trace_reference.py,analyze.py,Readme.md,
evidence.json,results.json,response.csv,test-ab.sh,intro-A/B.wav}.
Živéprofily/HW/hlasitostiNEMENENÉ;frozenpackageSHA256SUMSPASS.
ParammappingXMLkey10lowfreq1805.71655/11high1800,12/13slopes.4/.4,
14offset-14.7629204,15stop-33.6923065,16stopGain-13.3142290,
17pass-3.26923227. Settery/registráciazbinárkyoverené.
Volumeadjustn=ln((10^(G/-10)-1)/(10^.01-1))/(2ln(S/P))=1.4527228808;
B=S/(10^(G/-10)-1)^(1/(2n))=-11.923842929. Prvýalgebraickýprepis
malchybupodielulogaritmov;nezávislýinstructiontracejuzachytilopravené.
GainD=20log10(master),akD<offset,gL/gH=(offset-D)*slope/
sqrt(1+(D/B)^(2n));inaknula. SSEfloat32koefs low+highshelfS1.
41tracetestov3sampleRates+bounds+syntheticnongeneratecasesPASS,
maxcoefdiff4.768e-7,gainerror0;listingbytesmatchedApplebinari.
Gainmastergetmaxb0/b4/b8,exactruntimepropagáciaGUINEPOTVRDENÁ.
Sweepexplicitmaster-120..0(241),20Hz..20k(401),48k:shapeafter1kmatch
max.00383793dB,unmatchedboostmax1.7488dB;samotnýDspLoudnessvtejto
konfiguráciinevysvetľujebassloss. D=-31.5→common1.586dB,
-18.5→.698dB,-8.5→0;nieoznačovaťakopolohysystemslider.
PripravenýizolovanýABbezBankstownbalancedbase4ch;Bexplicitmaster-31.5
Loudness,mids1kmatched-.1.5876dB;signalRMSdiff.01853%,peakA.50537/B.50528.
Test-ab.sh explicitcs4208.split4nastaveniabezzmeny,neočakávaťvýraznýefekt.
ProfilakoopravuNEnasadený. ĎalšíhypotetickýkandidátMacOSMozart/DualBand
makeupgain/compresion+poradiefiltrov,zatiaľnerekonštruovaný.

Používateľ:test-abničnevykonáva. Aktuálnyboot22:21PCHcard1/HDMIcard0,
/proc PCM1-2exists splitY,alePWbassabsent:journalCannotgetcardindexPCH.
Starýbootwaitiba/procpredčasnehlásilready; novýwaitoveríajRW/dev/snd
controlC{n}/pcmC{n}D2paamixer-cPCHinfo(1s),dynamickéčísloPCH.
Test-ab.shpreflightterazokamžitýtext,jedenpw-dump8stimeout,explicit
missingnodeerror;scopedPIPEWIRE_PROPSmodule.rt=false,playbacktimeout12s.
FrozensavedpackageNEMENENÝ(známebootwaitobmedzeniestarejverzie).
Restart+verifyrunningprocess49893. Sandboxprobe93095môžetimeoutovať
prepermission; reálnyescalatedprobePASSuserspaceALSAready.

Dokončenie opravy testu: po reštarte zvukových služieb overené cs4208.bass
(id38), cs4208.split4(id47) a obe basové spojenia. PipeWire/WirePlumber active.
RTKit pri štarte spôsobil dva 25s DBus timeouty; scoped module.rt=false
platí iba pre testovacie klienty. Opravený test-ab.sh spustený session3729:
vypísal A, B aj Hotovo, exit0. Akustický výsledok musí potvrdiť používateľ.

2026-10-08 Mozart/DualBand investigation completed (offline scope):
cs4208-macos-mozart/Readme.md + evidence.json, static-targets.csv,
trace_curve.py scalar fail-closed instruction trace, independent curve_model.py,
analyze.py extractor+validation; frozen_response.py and frozen-response.json.
Source mac_data AppleHDA283.15 layout128. Patchbay confirms inputEQ ->
Mozart -> Loudness -> DualBand -> splitter -> per-branchEQ/BuzzKill/limiters.
Wrapper-setter mappings extracted from symbols+asm, bool fields decoded as
bool NOT bitcast float. Mono defaults e2954; dual defaults e2a38 (not e2df0,
which is maxima). Dual subblocks5:58 and58:111, 53values each.
Mozart key13->lib0 input+8dB verified expf->vDSP_vsmul. Static gain targets
(initial adaptive state = configured threshold): detector -80/+6.1712,
-60/+11.4657,-50/+12.9101,-40/+11.6486,-30/+7.6966,-20/+2.6648,-10/0.
These detector coordinates are NOT music dBFS nor GUI volume. Cannot simply
sum input8+curve12.9 as measured song gain; detector and smoothing still missing.
Dual freq800Hz; orderkey3 7.65639 rounds8. Low static target -4dB (curve flag
key18=0), high+2dB for weak signals (flagkey19=1), high targets diverge for
stronger levels. Globalkey20=1. Not a conventional sum of two audio bands:
low/high detectors give gain modulators; m=1-(gLow/gHigh)^(1/N), highmodgain
applied to fullsignal, then N cascades signal - m*LP(signal). Inferred frozen
weak-state response80Hz -3.9353dB,1k -0.2184dB, DC-4/Nyquist+2; not full
emulation. Relocs verified log10f803b0, expf803d8, vDSP_vmul804a3,
vDSP_vsub804fb; input expf7ce7d/vsmul7dc13.
Validation PASS:2883static cases, maxcoef4.26448e-6,maxgain2.95949e-6dB;
2 synthetic adaptive states with9gain cases each also PASS. Extracted asm
bytes checked against actual supplied binary. Initial algebra transcription
bugs corrected by independent trace + nondegenerate adaptive cases.
No new audio playback, PipeWire/hardware edits or frozenbundle changes.
Conclusion: Mozart quiet-signal gain is plausible missing component but NOT
proven bass fix. Need detector/gating/attackRelease/feedback/resampling before
faithful full-music A/B; do not label static model a complete Apple DSP port.

## Časový krok Mozart / DualBand – 2026-10-08

Pripravený `cs4208-macos-mozart/offline-reference/`: natívny matematický kód
z dodaného DspFuncLib v samostatnom Linux procese, bez zavádzania kextu;
scalar vDSP/libm náhrady, nie potvrdená bitová zhoda s macOS. Native parameters
53/119 floats, Dual defaults e2a38, wrapper mapping z evidence.json.
Opravené usporiadanie biquad koeficientov: section/channel/5 contiguous.
Pred opravou NaN; po oprave celé mono/dual prešli 144384 sample level-step testom,
stereo symmetry, fresh-instance determinism a ticho. AttackRelease native vs
float32 recurrence 128 samples presne. Natívny adaptívny počiatočný stav sa
líši od staršej syntetickej statickej inicializácie; nezamieňať tieto výsledky.
Latencie natívne getLatency: mono 174, dual 0 samples pri 48 kHz.

WAV A/B/C: rovnaký stage0 RBJ input EQ, potom A bypass/B Mozart/C Mozart+Dual,
rovnaký balanced crossover; nie úplná Apple output chain. 6s both.wav.
B integrated output RMS vs A +14.304 dB, bass pair +14.297 dB;
C vs A +14.487 dB. Z toho nevyplýva selektívna obnova basov.
Spoločný raw útlm -7.118 dB, peak<=.65. Predvolený test používa integrated-RMS
matched varianty a spoločné zosilnenie s peak<=.65; --raw zachová gain rozdiely.
Príkaz bash ~/sound_driver/cs4208-macos-mozart/offline-reference/test-abc.sh.
Oba live výstupy cs4208.bass/split4 read-only overené dostupné. Hudba sa počas
prípravy nepúšťala. Posluch používateľa nového A/B/C ešte čaká.
Saved-setup aj live profil nezmenené; bez Loudness/master-volume propagation,
BuzzKill/SplineLimiter/original branch EQ. build.sh opakuje kontroly a render.

## Posluch a požiadavka na 15 s

Používateľ: šesťsekundové Mozart A/B/C s vyrovnanou hlasitosťou znie približne
rovnako. Nehlási potvrdené zlepšenie basov. compare-rendered.py (len WAV, bez
native code/playback) -> comparison-analysis.json: matched B/A correlation
.999258, C/A .996443; relative RMSdifference3.85%/8.43%, nie metrika počuteľnosti.
Vstupný stage0 podľa použitého RBJ:60Hz -30.14dB,80Hz -20.62,100Hz -13.83,
150Hz -3.83,200Hz+1.40,1kHz -9.56. Nie sú to hodnoty celej macOS cesty.

Používateľ požiadal o dlhší úsek napr.15s. Zdroj intro-input.f32 má len10s,
both.wav6s; nový hudobný záznam zatiaľ NEMÁME. Pripravený capture15.py:
userEnter+spustenie tejistejskladby0:00 cez enhancedbass, 25s digitálny input
sinkmonitor cs4208.harmonics (nie mikrofón), nájde onset2%peak, vyberie15s,
5msfade, uloží15s/source-15s.wav +capture-info.json a spustírender.
render.py teraz má --source/--output-dir, pôvodné default6s nezmenené.
15s/test-abc.sh pripravený; prehrávací timeout dynamickýceil(duration)+6,
predvolenýmatched, --rawvoliteľný. User musí pozastaviť skladbu predtestom.
DefaultPWsinkread-only overený cs4208.harmonics; profil/config/hardware nemeníme.
Capture a skutočný 15s posluch zatiaľ čakajú na používateľa.

## Oprava capture15 – reálny 25s záznam

User report RuntimeError Záznam zlyhal(1). capture.f32 však mal presne9600000
bytes=25s48k stereo f32, všetky hodnoty konečné, peak.674874; onset2.06933s,
zostáva22.93s hudby. Nezávislý 1s digitálny monitorový test na cs4208.harmonics
reprodukoval exit1, nulový stderr a presne384000bytes. capture15.py opravený:
exit1 toleruje iba pri exact requested bytes +empty stderr; ostatné kódy/
stderr/incomplete expliciterror, potomfinite/peak/onset validation ostáva.
Pridané --use-existing bez nového záznamu/preflightu. Použitý skutočný uložený
usercapture, source-15s.wav vznikol a render15s beží; rawcapture zachovaný.
Nezaznamenávať znova, ak sú 15s A/B/C hotové. Služby/profil/HW nezmenené.
Render zo skutočného záznamu úspešne dokončený, exit0. Všetkých6WAV v15s/
overeno720000frames/48k/4ch/S16, peak<=.65; pripravené na posluch používateľa.

## Posluch 15s – výsledok

Používateľ: A/B/C veľmi podobné, B/C trochu tichší začiatok, basy počuteľné.
Na výslovné spresnenie odpovedal: basy aj v A, približne rovnako. Zatiaľ žiadny
potvrdený kvalitatívny/basový prínos Mozart/DualBand v tomto teste.
15s/listening-analysis.json: v globally matched WAV prvých6s B vsA -1.340dB,
C -1.447dB celkovo; basová dvojica -1.341/-1.451dB. Zvyšok6–15s B/C celkovo
+.301/+.321dB. Ide o digitálne RMS hodnoty úsekov, nie akustické meranie;
vyrovnanie bolo cez celý15súsek, nie každýčasovýúsek. Zodpovedá userposluchu.
Nevylučuje inú časovú odozvu pri inejúrovni/skladbe ani nepreukazuje plnúzhodu
s macOS. Neprezentovať kompresiu ako vyriešenie pôvodných chýbajúcich basov.
Live profil/frozenpackage nezmenené. Ďalší zmysluplný smer: pôvodné výstupné
EQ a správne zosilnenie/smerovanie basovej vetvy podľa mac_data, keďže test
používa balanced output a nie kompletnú macOS cestu.

## Celá macOS DSP cesta a checkpoint – 2026-10-08

User žiada ukončiť ladenie basov, odložiť posledný stav a skúsiť 1:1 podľa macOS podkladov. Checkpoint saved-setup/checkpoint-before-macos-chain-2026-10-08-2335/ +tar.gz+sha256 hotový: 315 súborov overených manifestom, konfigurácie so symlinkmi, workspace experimenty s reálnou 15s vzorkou, frozen installer, Readme obnova. mac_data ostáva pôvodné. Živý systém nezmenený.

Nový samostatný cs4208-macos-chain/: celé poradie layout128 variant0: EQ0→Mozart→Loudness→DualBand→split; primary EQ5→EQ8→Buzz9→Spline11; bass EQ6→Buzz7→Spline10; 4ch FL/FR/RL/RR. Native matematické rutiny AppleDspFuncLib z mac_data v userspace, lokálne skalárne vDSP/FFT náhrady, žiadny kext load. Native výpočet EQ objavil alpha=sin(w)*sinh(1/(2Q)) pri typoch0/1/4, odlišný od starého RBJ. Všetky zdrojové filtre vrátane typu6 zahrnuté.

Pevný software master0dB, unity outputgain/delay0/phase normal/muteoff. Reálna macOS volumepropagation a runtimevariant NEPOTVRDENÉ. CPU optimizedSplinepath nereprodukovaný (native scalarpath), vDSP arithmetic nebitexact, hardvérové ovládanie stáleLinux. Preto neprezentovať ako potvrdenú1:1 akustickú ani bitovúzhodu.

check.py/validation.json PASS: FFTvsDFT/roundtrip/stride, nativeEQvsrovnice9cases,256filtrov poles max.995776, Loudness3gain, wholechain49152framesfinite/repeat/silence. render.py spracoval skutočnýsource15s: latencyMozart174+Buzz240=414samples spoločné odstránenie, pôvodný peak1.0, jednotná exportattenuation−3.741733dB na peak.65. macos-chain-15s.wav 48k4chS16 720000frames; rawf32predexportomzachovaný. render-results.json obsahuje zdrojové SHA,parametre,graph,koeficienty,limity.

test-macos.sh kontrolujehash a PWoutputs, timeout21s, dontremix, targetcs4208.split4. Bez autoplay a bez zmienliveprofilu. Používateľ má pozastaviťhudbu a spustiťscript; zatiaľ novýposluchNEVYKONANÝ. Readme.md vysvetľuje experiment a predpoklady. Frozen cs4208-enhanced-bass balík a checkpoint nemeniť.

## Živý macOS profil – 2026-10-08 23:54

User úspešnáfullchain15svzorka "vyzerá dobre" žiada zapojiť ako novýprofil. Implementovaný cs4208-macos-chain/live.py: Chain(1.0) bezďalšiehoEQ, 512frames48k, pw-recordnullsinkmonitor→DSP→pw-play4chsplit4, outputgain.65rovnakýakoWAV. Samostatný sink cs4208.macos-chain, description MacBook Speakers (macOS DSP experiment). PostDSPvolume actuallinearProps.channelVolumes+mute 200mspoll, 512frameramp; monitor.channel-volumes=false. Nezamieňať wpctlgetvolumeperceptual75% so skutečnýmlineárnym.421875. Výstup začal75%, DSPmasterfixed0dB.

Používateľskáunit ~/.config/systemd/user/cs4208-macos-chain.service nainštalovaná, enabled+running. Ownpw-cli clientcreatesnonlingeradapter,sinkdisappearsonstop. Capture+playback+nullsink node.group=cs4208-macos-chain-clock, nullsinknode.driver=false; overené všetkydriverid88 (ALSAprimary) =jednotnéčasovanie. Node.dont-fallback iba output; pri capture+stream.capture.sink na tejto WP verzii spôsobuje defined target not found; explicitný capture target overiť cez graph. 100msbuffer vstupajvýstup, latencyhighernotmeasuredanalog.

select-profile.py vybral default novýsink, FirefoxPulseactiveautomatickypresmerovaný. Uloženýlive-previous-default.json originalcs4208.harmonics+volume; --restore vráti olddefault. install-live.sh preopakovanýinstallnormaluser,potrebujeexistingdriver/splitnodes. Readme updated. Frozen balík acheckpointunchanged. Steady30saudio vs30.08elapsed, DSPcpu18.27s (~61%core) a celáservice~60–75%core,0automaticrestarts. Je to neoptimalizovanýprototyp, službyprocesujúajsilence. Žiadne tvrdeniebitexact/akustická1:1.

Finalbridgefix: pw-playunbufferedstdin writeall cezmemoryview (partialwrites handled), initial4800frames4chzeros=.1sreservebeforeworkerloop. Predrezervououtput ERR8 prištarte/BQ.78, poopravepwtop2snapshotsERR0/BQ~0.00; existinghwERR14nezmenené. Capture node.dont-fallback incompatiblewWPmonitor, removed; targetnamegraphverified. UsercurrentlyFirefoxpaused, noactive-linkassertwhenidle. Finalknown15sinput playbackthroughlivesinkperformedforverification.

Finalverification23:58:33: live-validation.json PASS: sink206/capture180/output189 sharedDriver88; monitor2/output4activelinks; Firefox2linksnewprofile (idlecurrent); defaultnewprofile; volume.421875both/muteoff. Known15ssourceplayedthroughnewlivesink exit0. outputERR0 aftertest, NRestarts0, serviceactive. Latest29.9947saudio/30.00selapsed/DSPCPU16.69s. Finalprofileenabledandselected;checkpoint+frozeninstalleruntouched.

## Login recovery + CPU fix – 2026-10-09

User logoutprofilemissing asksCPU. Actualjournal00:00:51service+PWstopped; PWstarted00:01:07 butprofileinactiveSuccess. usermanagerdefault.target remainedactive22:21:20; oldWantedBydefaulttargetnotretriggered. FixedunitWantedBypipewire.service,BindsTo+PartOfpipewire.service; removedolddefaulttargetsymlink; installedenabledpipewire.service.wants. livewaits90srequired bass/split4/primary readiness. RealPWrestart verifiedautomaticprofilelaunch+defaultselection, preservingWPvolume.375723, links2/4,driver89,outputandprimaryERR0,NRestarts0. login-recovery-validation.json; actuallogoutnotrepeated.

CPU longoriginalservicejournal contradictedshorttest:150saudio/176selapsedbeforelogout. Newlive_processor.py removesonly exactidentityEQ sharedbothchannels; native/live-perf.c .so enablesFTZDAZmainDSPthread, noofflinechain/shimchanges. Source-drivenallactiveEQstagesremain13/12/10/7sections. Performancecheck6smusic+9ssilence old13.135s/new6.355s speedup2.067x,maxdiff5.5325881e-38, live-performance-validation.json. build.sh+install-live.sh compileperfhelper; install migratesunitenableandexplicitrestart. Currentlive.pyimports live_chain. StillnotbitexactmacOS,CPUstillhigherthanoldsimplefilters,silencealwaysprocessed. READMEupdatedwithfailureandlimits. Checkpoint/frozeninstallerunchanged.

## Audit vlastných chýb – 2026-10-09 00:29

User žiada skontrolovaťďalšiechyby. Nájdenéopravy: select-profile.py užneresetujevolume75/mute, existingbackupneprepisuje; args--volume/--unmuteexplicit. install-live.sh overuje6activelinks+channels+driver namiesto3names a čaká120s; compile-native.py atomickytmp+os.replace obeDLLs namiestotruncatemappedlib. Build/install používajúcompilehelper.

Oldservicejournaloutputdefinedtargetnotfound00:10:11 +28outputxruns, roottriggernezachytený. Terazcapture/output target0 node.autoconnect=false, explicitpw-link2monitorstereo+4FLFRRLRRsplit4, node.groupcommonclock. live_support.py route_statusguardchecks6exactchannelpreservingactivepairs,noextraoncaptureinput/output,physicaldriver,volumevalidity/mute/map. Supervisionfocusedpw-dumpnode 200ms/fullgraph1s, childhealth/stall10s. nodeobjectserialguard.

Novýnative/live-perf.c Cblockwrapper sameoriginalnativefn+objects+parameters+scalarbiquad pointers fromlive_chain. AllplanarDSPcalls+interleave+finitevalidation+volume rampsinoneCcall. LiveProcessor.process_block512frames/rawfloat32; check-live-block256blocks/131072framesasymmetrictoneslevelsreleaseL/Rramps exactly0maxdiff vsoldoptimizedChain, badNaNinputreject;1.22866s→.17486stest. Originalchain.py/native/shims.c/offlineWAVunchanged. check.py extra5nativehighshelfendpointsPASS. ExistingFFT/EQ/Loudness/chainchecksPASS. puretestsroutewrongchannel/wrongclock/extralink/NaNvolume/mute+selectbackupvolume-preserving/restorePASS fromsavedtests/route-fixture.json.

Priimplementovaníexplicitnýchlinksstartupdeadlockedpw-cat blockingI/O beforeformatnegotiation; fixedconcurrentstartupzero-prefillwriter untilallroutesactive +lifetimecapture-readerthreadQueue64. StartupqueueclearedatREADY; neverdropliveblocks, queueoverrunfatal/restart. Mainworkerreadqueuetimeout1sec, handlespartialoutputwrites; finallykillschildren.

Runtimeverifiedswitcholddefault&return samePID links volume/mute unchanged. Realpipewirerestartautomaticallyrestorednewprofile/default/6links/physicaldriver90,WPvolume.157271bothpreserved. Known15ssourceplayedthroughnewprofile; aftertestoutput+primaryERR0, NRestarts0. Latest119.9787saudio/119.96selapsed/DSP10.79sCPU, wholeunitCPU46.7s includingstartup/helpers (do notconflateDSPCPUandtotal). AtomicrecompilewhileactivepreservedPID46241+routes. FilesAudit-2026-10-09.md,audit-results-2026-10-09.json detailfindingslimits. saved-setup/live-audit-backup-2026-10-09/ oldliveservice/select/install sourcebackup; originalcheckpoint/frozeninstallerunchanged. Newauditedbrancharchiveonlyneedsoriginalmacdata/investigation/drivertorun, notstandalonefreshinstaller.

Audit finalclockguard: usephysicalnode.driver-id ifpresent elsephysical.id (outputmayfollowanotherdriver). Addedpositivefollowergraphfixturetest+negativewrongclocktestPASS; service reloaded. Beforefinalreload269.952saudio/269.92selapsedDSP23.93s, NRestarts0.

## Hybrid enhanced bass + macOS DSP – 2026-10-10

User označil enhanced bass za najlepší a žiada jeho prvky preniesť do DSP experimentu. Nový samostatný cs4208-macos-enhanced/, node cs4208.macos-enhanced, description MacBook Speakers (DSP + enhanced bass). Original profily/checkpoint/frozeninstaller bez zmien. Hybrid Mozart→Loudness→DualBand→enhancedsource graph→primary Buzz9/Spline11 & bass Buzz7/Spline10. Pôvodné EQ0/5/6/8 bypass, aby sa nezdvojovalo EQ. Exact94configcopy enhanced-source.json, nativeBankstownsamebinaryhash, −6dBheadroom/+3dBbass/wetgain2.0047489345, 7biquad/ch exact48kcoeffs. Sourceclamp±.8 +finalclamp±.8, unitypostDSPgain max1 miesto old.65. Dynamika z mac_data layout128variant0; hybrid NIEakustická1:1macOS. Copied auditedsupervisedlivebridge uniqueclock/support/nodeprefix/newunit; install preberá enhancedvolume/mute len firsttime, olddefaultbackup preserved. Numerics validation.json enhanced-only vs prior6sWAV relativeRMS.000198354; full15smusic+3ssilence finite peak.76584053 compute3.364s/18.0053saudio;NaNreject. README dependencies explicit, notstandalonefreshinstaller.

Prvý hybrid runtime mal pribúdajúce pw-play xruns (capture2/output14 po cca180s), hoci compute37.56s/179.968saudio. Novývariant zvýšil iba playbacklatency100→200ms a initialprefill4800→14400frames=.3s; capture100ms unchanged. Pôvodnýmacchain má vlastné existujúce capture16/output200xruns pri tomto boote; nemeniťho v tomto requeste. Buffer-validation.json zachytí nové before/after counts po2×15smusic.

Final buffer-validation PASS: beforecapture0/output0 after2×15smusic capture0/output0; no newxruns/NRestarts0; active6linksdriver88; profiledefaultnew+enabled. Freshnewnodeafterrestart hasPWrestoredunityvol. Fixedbuffersteady29.9947saudio/29.91elapsed/4.62sDSPCPU. Finalprofileaktívny, useracousticqualitypending. Stalepw-dumpresourcewarningsatstartup duringnodechurn, routesafterREADYvalid.

## Hybrid rezerva po chrčaní – 2026-10-10

User hybridcelkovohlasnejší/basypočuteľné,niekedyreprochrastia. ActualPWProps bassgain1.405254 both, primary1.0, hybrid1.0. Previousmax.8×1.405254=1.1242 potentialdownstreamdigitalclipping; mechanicaloverdriveunconfirmed. Savedpreviousnewhybridonly saved-setup/cs4208-macos-enhanced-before-headroom-2026-10-10/ (unchangedolderprofiles). tuning.json bass_pre_gain_db−3/output_gain_db−3 appliedonlydynamicsTrue, source94jsonuntouched andbaselineenhanced-onlycomparisonstillpassrelativeRMS.000198354. Basspre cancelsoriginal+3dBbeforeclamp/dynamics; postgainoverall.707945. Profilvolume/mute preserved, hardwaregainsoldprofilesuntouched. check.py full15s+3ssilence finitepeak.4929449/compute3.62374s, outputbound.5663566, aftermeasuredbassgainbound.7958749<1. NaNreject, gainargsfinite0..1validatebeforeDSPmutation. This doesNOTproveacousticrattleresolved,userlistenneeded.

## Návrat enhanced bass + spotreba – 2026-10-10

Uservolíoriginal MacBook Speakers (enhanced bass)ako najlepší, pýtaoptimalizáciuspotreby. wpctlsetdefaultcs4208.harmonics done; disable--now obemacos-chain/macos-enhancedservices, enabledsymlinksremoved. Nastavenia tónu/gainacceptedprofileunchanged. VerifiedFirefoxrunning/profileharmonicsrunning+default;otherfilterprofilesDSP/simple/virtual/balancedcaptures suspended outputsidle. PWMainPID3sCPUdelta8%onecore priFirefoxplayback (wholePWnotprofileisolation;notwattmeasurement). Basssession.suspend-timeout-seconds0, idlepowernotfullyoptimized/tested. reset-failed clearedoldmacchain; combinedreset-failedreturned1 for enhancedunitnotloadedafteralreadydisabled, noimpactactualstop. Experimental sources/backupsretained; notautostartanymore.

## Audit možností optimalizácie enhanced bass – 2026-10-10

Useržiada preveriťmožnosti. Activeconfigunchanged, candidateonly in cs4208-balanced-test/optimization-audit/. Userpausedmusic+closedGNOMEsoundsettings. Baselineidle8sPWCPU0tick→belowtimerresolution; profile/split/primary/mic suspended, bassidlePCM2SETUPstillopen; PCIcontrolleractive CS4208D0. Combineoutputruntimealready node.passive=true despiteconfigunset; clarifiedinitialassumption. Kernelpower_save2/controllerY/PCIauto. Known15ssourceplayedthroughharmonics, steady8swholePWCPU4.75%onecore, exit0. Earlier8%includedGNOMEmicmeter, cannotattributeprofile. 33nodes(14bq6linear4copy4clamp4mixer1LV2), unusedprofilesinactive. Preparedoriginal80backup+candidateonly timeout0→5, NOTinstalled/tested. Readme prioritizesidlesuspend thenquantum2048, graphgain/copymerge, mmapcompatibility; no projectedwattpromise. OfficialPWprops+kernelpowersavechecked.

## Uspávanie bass nasadené – 2026-10-10

Userexplicitnevybralmožnosť1. ModifiedONLYactive80cs4208-split4 basstimeout0→5; backupcurrent80-before-install +installedcopy inoptimization-audit. RestartPW/PWpulse/WP, restoredcurrentprofiledefaultcs4208.harmonics andactualvolumes(master1,basschannel1.405254,profilechannel.170891,primary1,muteoff) frombefore-suspend-test.json; requiredbecause94state.restore-propsfalse. Scriptcheck-suspend.py two15swake/idlecycles PASS: initial+postbothidlechecks10swait basssuspendedPCM2closedPCIruntime_statussuspended; playbackbothprimaryPCM0/bassPCM2RUNNINGcontrolleractive. All5snapshots volumes exactlybefore. Optimizedconfigurationleftactive; nativefilters/plugins/ratesunchanged. Frozenoldinstallerunchanged (freshsystemoldsetupstilltimeout0needsnewpatch). Acousticpop/headphones/relogin/batterywattsnotverified.

## Samostatný enhanced bass balík aktualizovaný – 2026-10-10

Userpotvrdilnoacousticpop/lostintro ažiada presnýmanualinstall/uninstall+filesbackup, chce sámtestovaťrootdriverreinstall. Createdsaved-setup/cs4208-enhanced-bass-2026-10-10/ copiedoldimmutable20261008. Newpayloadonly80split4currenttimeout5 +94harmonicscurrent +WP2rules +sameLV2 +sameKO. 93movedreference; 90..93inreference/currentbackupnotinstalled. Currentmachine snapshotsPWvol(allunityexceptbass1.405254),ALSAmixerstate,rootalsa-base+splitconf,olduserconfigs/unitfiles forbackupNOTautoallrestore. Currentroot alsa-base containsmbp11 index0+msi1separatelegacyrows; manualReadmeA removesonlyexact2rows+guard+projectconfigs/plugins+module,depmod/initramfs/reboot. B manualrootinstallko+combinedownmodprobeallflags, reboot, usercopyexplicitfiles+portable%hguard, saferHWMaster−20db/virtual75%,basslinear1.405254. Optionalrestore-current-levels.py preflight +dryrun +ALSA/PWexactlevels, noautostore; sudoalsactlstoreexplicitafterverification. Updatedmanage-userselectpreservesvolumeunless--initial; installinitialize+wait30snodeavailability. Automatedinstall/removemanifest vs currentmanualnom anifest distinguished. Tests syntax+staging install/remove/restoredoldfile/reinstalldeny/mutationrefusalPASS, sourcecompile/tmpverifiedsrcversion51E4...; actualKO/profile/LV2hashmatchcurrent, livepreflight/dryrunPASS. No liveuninstall/installoccurred. READMEopenedqueued. Archive+checksumname cs4208-enhanced-bass-2026-10-10.tar.gz(.sha256), source/extracthasheschecked. Oldfrozen20261008untouched. Onlykernel7.0.0-38-generic Ubuntu7.0.0-38.38amd64, noDKMS orOSdependencydeb bundle.


## 2026-10-11 — oprava alternatívy D
Automatická používateľská inštalácia kopírovala súbory, ale skončila pred reštartom: amixer považoval -20dB za voľby. Opravené na amixer -c PCH -- sset Master -20dB unmute v skripte aj ručnom návode. Opakovanie install teraz overí identitu manifestu a všetkých súborov, zachová pôvodné zálohy vrátane mixer-before a dokončí aktiváciu; zmenené súbory odmietne. Čakanie na výstupy predĺžené na 120s kvôli pozorovaným dvom 25s RTKit timeoutom. Živá prerušená inštalácia úspešne dokončená, všetky štyri výstupy prítomné, predvolený cs4208.harmonics, hlasitosť 75 %, ALSA Master -20dB. Staging retry/backup/modified-file guard/uninstall PASS. Oct10 balík, Readme, VALIDATION, SHA256SUMS a tar.gz+sha256 aktualizované a extrakcia overená. Oct8 balík nezmenený.

2026-10-11: Na žiadosť používateľa skrátené zobrazované názvy aktívnych výstupov na CS4208 Bass Stereo, MB Speakers 4ch a MB Speakers (enhanced bass). Interné node.name a DSP nezmenené (porovnanie JSON bez node.description PASS). Upravené živé konfigurácie a SHA v inštalačnom manifeste so zachovaním pôvodných záloh, balík Oct10/Readme/archív/súčty aktualizované. Historické referencie a snapshot current-machine ostali pôvodné.

2026-10-11: Všetky texty a hlásenia .py/.sh skriptov aktuálneho Oct10 balíka preložené do EN. Predvolený ALSA Master v install je 0dB (amixer -c PCH -- sset Master 0dB unmute); softvérová inicializácia profilu ostáva 75 %. Readme upravený, explicitná obnova archivovaných hlasitostí naďalej obnovuje pôvodný ALSA snapshot. Aktuálne živé hlasitosti sa nemenili. Syntax Python/bash, ASCII text všetkých skriptov, staging install/retry/remove, izolované overenie príkazu Master a CLI help PASS. Archív/súčty/VALIDATION aktualizované, extrakcia a súčty PASS.

## 2026-10-11 — jack routing and missing bass startup fix
User reported headphones silent and speakers broken after jack use. Live diagnostics: jack EnumRoute yes and headphone route selected, but ALSA Headphone 0/off under api.alsa.soft-mixer=true; enhanced speaker DSP still selected. Independently bass node absent since boot, journal hw:PCH,2 Cannot get card index for PCH although old guard saw /proc PCM (race). Manual direct primary sink + Headphone 0dB/unmute, speakers/bass muted, low headphone volume made headphones play (user confirmed). New event-driven support/jack-route.py + enabled user cs4208-jack-route.service: pw-dump --monitor, waits for active ACP hardware route, routes headphones direct without DSP, hardware mixer restoration, defaults/active app stream metadata; disconnect restores enhanced plus speaker/bass 100% and primary unity. Keeps headphone soft volume in service memory; initial35%. No periodic polling. Guard now uses libasound snd_pcm_open hw:PCH,2 nonblock+close to prove actual availability. Installed managed new payload preserving original backups and manifest; restarted services, restored enhanced/split previous levels, bass channel gains1.405254. Live bass restored, automatic headphone selected, unplug event selected enhanced and restored both hardware switches. Synthetic insert/remove/route-delay/no-repeat test and staging install/retry/remove PASS. Oct10 Readme manual/automatic install/uninstall updated and archive+sums verified. Awaiting user acoustic confirmation after unplug. No kernel code modified.

2026-10-11: Používateľ potvrdil „ano funguje to korektne“ po automatickom odpojení jacku a návrate na MB Speakers. Akustické overenie slúchadiel aj reproduktorov PASS. VALIDATION a Readme Oct10 balíka aktualizované, archív+súčty regenerované a overené.
