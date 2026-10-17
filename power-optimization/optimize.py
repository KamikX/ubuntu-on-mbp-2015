#!/usr/bin/env python3
"""Apply a backed-up, reversible CPU policy for this MacBook."""
import configparser
import glob
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

DEST = Path('/home/power-optimization')
SOURCE = Path(__file__).resolve().parent
SERVICES = ['auto-cpufreq', 'laptop-mode', 'powertop']
DROPIN = Path('/etc/systemd/system/auto-cpufreq.service.d/90-power-optimization.conf')
FILES = [Path('/etc/auto-cpufreq.conf'),
         Path('/etc/laptop-mode/conf.d/cpufreq.conf'),
         Path('/etc/laptop-mode/conf.d/intel_pstate.conf'), DROPIN,
         Path('/opt/auto-cpufreq/override.pickle'),
         Path('/opt/auto-cpufreq/turbo-override.pickle')]

def run(*args, check=True):
    return subprocess.run(args, text=True, capture_output=True, check=check)

def read(path):
    try:
        return Path(path).read_text().strip()
    except OSError:
        return None

def services():
    return {s: {'enabled': run('systemctl', 'is-enabled', s, check=False).stdout.strip(),
                'active': run('systemctl', 'is-active', s, check=False).stdout.strip()}
            for s in SERVICES}

def cpu_state():
    fields = ['scaling_governor', 'scaling_min_freq', 'scaling_max_freq',
              'scaling_cur_freq', 'energy_performance_preference']
    result = {str(p / f): read(p / f)
              for p in sorted(Path('/sys/devices/system/cpu/cpufreq').glob('policy*'))
              for f in fields if (p / f).exists()}
    p = '/sys/devices/system/cpu/intel_pstate/no_turbo'
    result[p] = read(p)
    return result

def benchmark():
    times, freqs = [], []
    for _ in range(2):
        start = time.monotonic()
        proc = subprocess.Popen([sys.executable, '-c',
                                 'sum(i*i for i in range(2000000))'])
        while proc.poll() is None:
            freqs.append([read(p) for p in sorted(glob.glob(
                '/sys/devices/system/cpu/cpufreq/policy*/scaling_cur_freq'))])
            time.sleep(0.05)
        if proc.returncode:
            raise RuntimeError('Výpočtový test zlyhal')
        times.append(round(time.monotonic() - start, 3))
    return {'seconds': times, 'frequency_samples_khz': freqs,
            'note': 'Krátky jednovláknový test; výdrž batérie nemeria.'}

def snapshot():
    return {'timestamp': time.strftime('%Y-%m-%d %H:%M:%S %z'),
            'cpu': cpu_state(), 'services': services(),
            'thermal': {str(p): read(p) for p in Path('/sys/class/thermal').glob('thermal_zone*/temp')},
            'battery': {str(p): read(p) for d in Path('/sys/class/power_supply').glob('*')
                        for p in [d / f for f in ['status', 'online', 'capacity', 'power_now', 'energy_now']]
                        if p.exists()}, 'benchmark': benchmark()}

def save(name, data):
    (DEST / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n')

def restore():
    manifest = json.loads((DEST / 'manifest.json').read_text())
    run('systemctl', 'stop', 'auto-cpufreq', check=False)
    for entry in manifest['files']:
        path = Path(entry['path'])
        if entry['exists']:
            path.parent.mkdir(parents=True, exist_ok=True)
            if path.is_symlink():
                path.unlink()
            shutil.copy2(DEST / entry['backup'], path, follow_symlinks=False)
        elif path.exists() or path.is_symlink():
            path.unlink()
    run('systemctl', 'daemon-reload')
    for service, state in manifest['services'].items():
        if state['enabled'] == 'enabled':
            run('systemctl', 'enable', service)
        elif state['enabled'] == 'disabled':
            run('systemctl', 'disable', service)
        if state['active'] == 'active':
            run('systemctl', 'restart', service)
        else:
            run('systemctl', 'stop', service, check=False)
    # Restore captured writable CPU knobs after service startup.
    for path, value in manifest['cpu'].items():
        if value is not None and not path.endswith('scaling_cur_freq'):
            try:
                Path(path).write_text(value + '\n')
            except OSError as exc:
                print(f'Upozornenie pri obnove {path}: {exc}')
    (DEST / 'result.txt').write_text('Pôvodné nastavenia obnovené.\n')

def apply():
    if (DEST / 'manifest.json').exists():
        raise RuntimeError('Záloha už existuje. Najprv skontroluj result.txt; zálohu neprepíšem.')
    if read('/sys/class/dmi/id/product_name') != 'MacBookPro11,4':
        raise RuntimeError('Tento postup je pripravený pre MacBookPro11,4.')
    governors = read('/sys/devices/system/cpu/cpufreq/policy0/scaling_available_governors') or ''
    if 'schedutil' not in governors.split():
        raise RuntimeError('Governor schedutil nie je dostupný.')
    if run('systemctl', 'is-active', 'auto-cpufreq', check=False).stdout.strip() != 'active':
        raise RuntimeError('auto-cpufreq nie je aktívne; očakávaný východiskový stav sa zmenil.')
    config = configparser.ConfigParser()
    config.read(SOURCE / 'auto-cpufreq.conf')
    assert config['battery']['governor'] == config['charger']['governor'] == 'schedutil'
    # Detect older main-file overrides before making changes.
    main = read('/etc/laptop-mode/laptop-mode.conf') or ''
    if re.search(r'^\s*(CONTROL_CPU_FREQUENCY|CONTROL_INTEL_PSTATE|BATT_CPU_GOVERNOR)\s*=', main, re.M):
        raise RuntimeError('Hlavná konfigurácia laptop-mode obsahuje CPU override; treba individuálnu kontrolu.')
    replacements = {}
    for path, key in [(FILES[1], 'CONTROL_CPU_FREQUENCY'), (FILES[2], 'CONTROL_INTEL_PSTATE')]:
        text = path.read_text()
        text, count = re.subn(r'^' + key + r'=.*$', key + '=0', text, flags=re.M)
        if count != 1:
            raise RuntimeError(f'Neočakávaný obsah {path}')
        replacements[path] = text
    DEST.mkdir(parents=True, exist_ok=True)
    for name in ['README.md', 'auto-cpufreq.conf', 'optimize.py']:
        if (SOURCE / name).resolve() != (DEST / name).resolve():
            shutil.copy2(SOURCE / name, DEST / name)
    backup = DEST / 'backups'
    backup.mkdir(mode=0o700)
    before = snapshot()
    save('before.json', before)
    manifest = {'files': [], 'services': before['services'], 'cpu': before['cpu']}
    for i, path in enumerate(FILES):
        exists = path.exists() or path.is_symlink()
        name = f'backups/{i}-{path.name}'
        if exists:
            shutil.copy2(path, DEST / name, follow_symlinks=False)
        manifest['files'].append({'path': str(path), 'exists': exists, 'backup': name})
    save('manifest.json', manifest)
    try:
        run('systemctl', 'stop', 'auto-cpufreq')
        for path, text in replacements.items():
            path.write_text(text)
        shutil.copy2(DEST / 'auto-cpufreq.conf', FILES[0])
        # Preserve the installed command and append an explicit config path.
        cmd = run('systemctl', 'show', 'auto-cpufreq', '-p', 'ExecStart', '--value').stdout
        match = re.search(r'argv\[\]=(.*?)(?:\s+;|\s*})', cmd)
        if not match or '--daemon' not in match.group(1) or '--config' in match.group(1):
            raise RuntimeError('Neočakávaný príkaz služby auto-cpufreq.')
        DROPIN.parent.mkdir(parents=True, exist_ok=True)
        DROPIN.write_text('[Service]\nExecStart=\nExecStart=' + match.group(1).strip() +
                          ' --config /etc/auto-cpufreq.conf\n')
        for path in FILES[4:]:
            if path.exists():
                path.unlink()
        run('systemctl', 'disable', '--now', 'powertop')
        run('systemctl', 'reset-failed', 'powertop', check=False)
        run('systemctl', 'daemon-reload')
        run('systemctl', 'start', 'auto-cpufreq')
        for _ in range(20):
            time.sleep(1)
            current = cpu_state()
            govs = [v for p, v in current.items() if p.endswith('scaling_governor')]
            mains = any(read(d / 'online') == '1' for d in Path('/sys/class/power_supply').glob('*')
                        if read(d / 'type') == 'Mains')
            if govs and all(g == 'schedutil' for g in govs) and (mains or current.get(
                    '/sys/devices/system/cpu/intel_pstate/no_turbo') == '1'):
                break
        else:
            raise RuntimeError('Služba nenastavila očakávaný governor/Turbo do 20 sekúnd.')
        after = snapshot()
        save('after.json', after)
        if after['services']['auto-cpufreq']['active'] != 'active' or any(
                v != 'schedutil' for p, v in after['cpu'].items() if p.endswith('scaling_governor')):
            raise RuntimeError('Záverečná kontrola služby alebo CPU zlyhala.')
        fastest = max(int(v) for sample in after['benchmark']['frequency_samples_khz']
                      for v in sample if v)
        if fastest <= 900000:
            raise RuntimeError('CPU počas krátkej záťaže nezrýchlil nad 900 MHz.')
        (DEST / 'result.txt').write_text(
            'Optimalizácia úspešne aplikovaná.\nVšetky CPU: schedutil.\n'
            f'Najvyššia frekvencia zachytená počas testu: {fastest / 1000:.0f} MHz.\n'
            'Pred/po: before.json a after.json. Adaptérový profil a dlhodobá výdrž vyžadujú samostatné overenie.\n')
        print((DEST / 'result.txt').read_text())
        print('Dokumentácia a zálohy:', DEST)
    except Exception:
        restore()
        raise

if __name__ == '__main__':
    if os.geteuid() != 0:
        sys.exit('Spusti cez sudo; administrátorské práva sú potrebné na zmenu systému.')
    try:
        if sys.argv[1:] == ['--rollback']:
            restore()
            print('Pôvodné nastavenia obnovené.')
        elif not sys.argv[1:]:
            apply()
        else:
            sys.exit('Použitie: optimize.py [--rollback]')
    except Exception as exc:
        sys.exit(f'Chyba: {exc}')
