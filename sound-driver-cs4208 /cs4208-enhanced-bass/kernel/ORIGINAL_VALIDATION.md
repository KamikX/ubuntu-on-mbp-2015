# Overenie balíka

- Vstup: používateľom dodaný Ubuntu HDA zdroj, linux-source 7.0.0-38.38.
- SHA-256 pôvodného `sound/hda/codecs/cirrus/cs420x.c`:
  `44b7f25a946e0e7352e2200f8195adf7ceae0969597f7c5738f96a6a6843dcd0`.
- Stiahnuté oficiálne Ubuntu hlavičky:
  `linux-headers-7.0.0-38_7.0.0-38.38_all.deb` a
  `linux-headers-7.0.0-38-generic_7.0.0-38.38_amd64.deb`.
- Kompilácia upraveného zdroja, MODPOST aj konečné linkovanie `.ko` úspešné.
- MODPOST nehlásil neexportované alebo chýbajúce symboly.
- Výsledný vermagic: `7.0.0-38-generic SMP preempt mod_unload modversions`.
- Parameter modulu `split_speakers` prítomný, typu bool.

Lokálne bol dostupný GCC 13.3, zatiaľ čo Ubuntu kernel bol zostavený GCC 15.2.
Iba v lokálnej kópii build prostredia bol pre overenie nahradený nepodporovaný
optimalizačný prepínač `-fmin-function-alignment=16` prepínačom
`-falign-functions=16`. Starší kompilátor hlásil ignorovaný atribút `counted_by`
v kernelových hlavičkách. BTF bolo preskočené, lebo chýbal vmlinux.

Táto úprava hlavičiek **nie je súčasťou balíka**. Dodaný build.sh používa GCC 15
a pôvodné hlavičky používateľovho kernelu. Balík neobsahuje lokálne zostavené
binárne moduly; modul sa musí zostaviť na cieľovom Ubuntu.

Skripty prešli `bash -n`. Generátor WAV bol spustený; formát, kanály, dĺžka,
vrcholová amplitúda a izolácia kanálov boli skontrolované.
Patch bol spätne aplikovaný na nezmenený vstup a porovnaný s upraveným zdrojom.

Hardvérové prehrávanie, súčasná funkcia oboch DAC-ov, automatické stlmenie pri
zapojení slúchadiel, suspend/resume a PipeWire správanie zatiaľ overené nie sú.
Inštalátor ani rollback neboli spustené na používateľovom Macu.

Oprava testovacieho skriptu po hlásení `Job ... canceled`: sockety a služby sa
zastavujú jednotlivo, konečný ActiveState sa kontroluje pred prehrávaním a
obnovujú sa v poradí závislostí. Simulovaný systemctl overil zrušený stop job
so skutočne neaktívnymi jednotkami, poradie obnovenia a odmietnutie testu,
ak jednotka zostala aktívna. Táto simulácia nenahrádza test používateľovho systemd.
