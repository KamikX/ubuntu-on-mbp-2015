#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-2.0-or-later
"""Portable, backed-up user audio configuration installation and removal."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def run(*args):
    subprocess.run(args, check=True, timeout=120)

def locations(stage=None):
    if stage:
        home=stage/'home';config=home/'.config';data=home/'.local/share'
    else:
        home=Path.home();config=Path(os.environ.get('XDG_CONFIG_HOME',home/'.config'))
        data=Path(os.environ.get('XDG_DATA_HOME',home/'.local/share'))
    return home,config,data/'cs4208-enhanced-bass-snapshot'

def payload(home,config):
    items=[]
    for folder,subpath in [('pipewire','pipewire/pipewire.conf.d'),('wireplumber','wireplumber/wireplumber.conf.d')]:
        for source in sorted((ROOT/folder).glob('*.conf')):
            items.append((source,config/subpath/source.name))
    for source in sorted((ROOT/'vendor/bankstown.lv2').iterdir()):
        if source.is_file():items.append((source,home/'.lv2/bankstown.lv2'/source.name))
    for name in ['wait-for-cs4208.py','jack-route.py']:
        items.append((ROOT/'support'/name,config/'cs4208-snapshot'/name))
    return items

def preflight():
    if os.geteuid()==0:raise RuntimeError('Run without sudo.')
    if Path('/sys/class/dmi/id/product_name').read_text().strip()!='MacBookPro11,4':
        raise RuntimeError('This package is only for MacBookPro11,4.')
    if os.uname().machine!='x86_64':raise RuntimeError('The bundled Bankstown plugin is only for amd64.')
    flag=Path('/sys/module/snd_hda_codec_cs420x/parameters/split_speakers')
    if not flag.exists() or flag.read_text().strip()!='Y':
        raise RuntimeError('Install the driver as described in Readme.md and reboot first.')
    codec=Path('/proc/asound/card0/codec#0').read_text()
    if 'Vendor Id: 0x10134208' not in codec or 'Subsystem Id: 0x106b8000' not in codec:
        raise RuntimeError('Unexpected codec or sound card order.')
    info=Path('/proc/asound/card0/pcm2p/info')
    if not info.exists() or 'CS4208 Bass Stereo' not in info.read_text():
        raise RuntimeError('The expected bass PCM hw:PCH,2 is missing.')
    for name in ['pw-dump','pw-cli','pw-metadata','wpctl','systemctl','amixer']:
        if not shutil.which(name):raise RuntimeError(f'Missing tool {name}; see Readme.md.')

def planned(home,config):
    files={str(dst):src.read_bytes() for src,dst in payload(home,config)}
    wait=config/'cs4208-snapshot/wait-for-cs4208.py'
    # systemd specifiers and quoting, independent of the archive's location.
    escaped=str(wait).replace('%','%%').replace('\\','\\\\').replace('"','\\"')
    files[str(config/'systemd/user/pipewire.service.d/20-cs4208-wait.conf')]=(
        '[Service]\nExecStartPre=/usr/bin/python3 "'+escaped+'"\n').encode()
    route=config/'cs4208-snapshot/jack-route.py'
    escaped_route=str(route).replace('%','%%').replace('\\','\\\\').replace('"','\\"')
    files[str(config/'systemd/user/cs4208-jack-route.service')]=(
        '[Unit]\nDescription=CS4208 headphone and speaker routing\n'
        'After=pipewire.service wireplumber.service\n'
        '[Service]\nExecStart=/usr/bin/python3 "'+escaped_route+'"\n'
        'Restart=on-failure\nRestartSec=3\n'
        '[Install]\nWantedBy=default.target\n').encode()
    return files

def install(files,state):
    if state.exists():
        manifest=state/'manifest.json'
        expected={name:hashlib.sha256(content).hexdigest() for name,content in files.items()}
        if not manifest.is_file():raise RuntimeError(f'Missing manifest: {state}; keep the backup and resolve this manually.')
        records=json.loads(manifest.read_text())
        if len(records)!=len(expected) or {r['path']:r['sha256'] for r in records}!=expected:
            raise RuntimeError('The existing installation has different package contents; the backup was preserved.')
        for record in records:
            p=Path(record['path'])
            if p.is_symlink() or not p.is_file() or digest(p)!=record['sha256']:
                raise RuntimeError(f'An installed file was modified or is missing: {p}; the backup was preserved.')
            if record['backup'] is not None and not (state/'backups'/record['backup']).is_file():
                raise RuntimeError('The original backup is missing; nothing was changed.')
        print('Files are already installed; completing activation with the original backup.')
        return
    # Validate all destinations before writing anything.
    for name in files:
        p=Path(name)
        if p.is_symlink() or (p.exists() and not p.is_file()):
            raise RuntimeError(f'Not a regular file: {p}')
    (state/'backups').mkdir(parents=True)
    records=[]
    for i,(name,content) in enumerate(files.items()):
        p=Path(name);backup=None
        if p.exists():
            backup=str(i);shutil.copy2(p,state/'backups'/backup)
        records.append({'path':name,'backup':backup,'sha256':hashlib.sha256(content).hexdigest()})
    (state/'manifest.json').write_text(json.dumps(records,indent=2)+'\n')
    try:
        for name,content in files.items():
            p=Path(name);p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(content);p.chmod(0o644)
    except BaseException:
        # Restore immediately, even if interrupted during a partial install.
        restore(records,state)
        raise

def restore(records,state):
    for record in reversed(records):
        p=Path(record['path'])
        if record['backup'] is not None:
            p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(state/'backups'/record['backup'],p)
        else:p.unlink(missing_ok=True)
    shutil.rmtree(state)

def remove(state):
    manifest=state/'manifest.json'
    if not manifest.exists():raise RuntimeError('The installation record is missing; nothing was removed.')
    records=json.loads(manifest.read_text())
    for record in records:
        p=Path(record['path'])
        if p.exists() and (p.is_symlink() or not p.is_file() or digest(p)!=record['sha256']):
            raise RuntimeError(f'A file was modified after installation; back it up and resolve this manually first: {p}')
    restore(records,state)

def node_ids():
    objects=json.loads(subprocess.check_output(['pw-dump'],timeout=15))
    return {o['info']['props'].get('node.name'):o['id'] for o in objects
            if o.get('type')=='PipeWire:Interface:Node'}

def activate(initialize=False):
    required={'cs4208.bass','cs4208.split4','cs4208.harmonics','alsa_output.pci-0000_00_1b.0.analog-stereo'}
    deadline=time.monotonic()+120
    while time.monotonic()<deadline:
        try:
            ids=node_ids()
            if required<=ids.keys():break
        except subprocess.SubprocessError:pass
        time.sleep(.25)
    else:raise RuntimeError('Audio outputs did not start after the restart; check the PipeWire/WirePlumber journal.')
    for name in ['cs4208.bass','cs4208.split4','cs4208.harmonics','alsa_output.pci-0000_00_1b.0.analog-stereo']:
        if name not in ids:raise RuntimeError(f'Missing output {name}; check journalctl --user -u pipewire -n 50.')
        if initialize:
            run('wpctl','set-volume',str(ids[name]),'.75' if name=='cs4208.harmonics' else '1.0')
            run('wpctl','set-mute',str(ids[name]),'0')
    if initialize:
        run('pw-cli','set-param',str(ids['cs4208.bass']),'Props',json.dumps({'volume':1.,'channelVolumes':[1.405254,1.405254]}))
    run('wpctl','set-default',str(ids['cs4208.harmonics']))

def restart():
    run('systemctl','--user','daemon-reload')
    run('bash',str(ROOT/'support/restart-audio.sh'))

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['install','remove','select','check'])
    parser.add_argument('--dry-run',action='store_true')
    parser.add_argument('--initial',action='store_true',help='For select only: initial levels, profile 75 %%, bass 1.405254.')
    parser.add_argument('--staging-root',type=Path,help='Test files in a separate directory without services or devices.')
    args=parser.parse_args()
    os.environ['PIPEWIRE_PROPS']='{ module.rt = false }'  # Control clients only; server unchanged.
    home,config,state=locations(args.staging_root)
    files=planned(home,config)
    if args.action=='install':
        if not args.staging_root:preflight()
        if args.dry_run:
            print('\n'.join(files));print('Dry run only; nothing was changed.');return
        install(files,state)
        if not args.staging_root:
            # Set the hardware Master to 0 dB; the original mixer state is backed up separately.
            if not (state/'mixer-before.txt').exists():
                with (state/'mixer-before.txt').open('w') as out:
                    subprocess.run(['amixer','-c','PCH','contents'],stdout=out,check=True)
            run('amixer','-c','PCH','--','sset','Master','0dB','unmute')
            run('amixer','-c','PCH','sset','Speaker','100%','unmute')
            run('amixer','-c','PCH','sset','Bass Speaker','100%','unmute')
            restart();activate(initialize=True)
            run('systemctl','--user','enable','--now','cs4208-jack-route.service')
        print('Installed. Profile: MB Speakers (enhanced bass).')
    elif args.action=='remove':
        if args.dry_run:print(f'Would restore files using {state}/manifest.json');return
        if not args.staging_root and os.geteuid()==0:raise RuntimeError('Run without sudo.')
        if not args.staging_root:
            run('systemctl','--user','disable','--now','cs4208-jack-route.service')
        remove(state)
        if not args.staging_root:restart()
        print('User files restored; the driver remains installed. Adjust the volume manually.')
    elif args.action=='select':
        if args.staging_root or args.dry_run:raise RuntimeError('Profile selection is not a file-only test.')
        preflight();activate(initialize=args.initial);print('Enhanced bass profile selected. Resume playback.')
    else:
        if args.staging_root:raise RuntimeError('This check requires a running audio system.')
        preflight();ids=node_ids()
        for name in ['cs4208.bass','cs4208.split4','cs4208.harmonics','alsa_output.pci-0000_00_1b.0.analog-stereo']:
            if name not in ids:raise RuntimeError(f'Missing {name}')
            print(name,ids[name])

if __name__=='__main__':
    try:main()
    except (RuntimeError,OSError,subprocess.SubprocessError) as exc:
        print(f'Error: {exc}',file=sys.stderr);sys.exit(1)
