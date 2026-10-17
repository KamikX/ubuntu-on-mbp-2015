#!/usr/bin/env python3
"""Restore the archived, user-confirmed levels on the same CS4208 Mac."""
import argparse,json,math,os,subprocess
from pathlib import Path
from manage_user_import import load_manager
ROOT=Path(__file__).resolve().parent
os.environ['PIPEWIRE_PROPS']='{ module.rt = false }'
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--dry-run',action='store_true');args=p.parse_args()
m=load_manager();m.preflight()
levels=json.loads((ROOT/'current-machine/pipewire-levels.json').read_text())
for props in levels.values():
 assert math.isfinite(props['volume']) and props['volume']>=0
 assert all(math.isfinite(v) and v>=0 for v in props['channelVolumes'])
if args.dry_run:
 print(json.dumps(levels,indent=2));print('ALSActl restore from current-machine/alsa-mixer.state; no changes.');raise SystemExit(0)
ids=m.node_ids()
if not all(name in ids for name in levels):raise SystemExit('Install and start the profile first.')
subprocess.run(['alsactl','-f',str(ROOT/'current-machine/alsa-mixer.state'),'restore','PCH'],check=True)
for name,props in levels.items():subprocess.run(['pw-cli','set-param',str(ids[name]),'Props',json.dumps(props)],check=True)
subprocess.run(['wpctl','set-default',str(ids['cs4208.harmonics'])],check=True)
print('Restored volume levels saved on 2026-10-10; the mixer was not saved to the system ALSA state.')
