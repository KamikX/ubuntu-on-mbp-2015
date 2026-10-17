#!/usr/bin/python3
"""Event-driven CS4208 jack routing: direct headphones, enhanced speakers."""
import codecs
import json
import os
import subprocess
import sys

PRIMARY = 'alsa_output.pci-0000_00_1b.0.analog-stereo'
ENHANCED = 'cs4208.harmonics'
CARD = 'alsa_card.pci-0000_00_1b.0'
os.environ['PIPEWIRE_PROPS'] = '{ module.rt = false }'


def run(*args):
    subprocess.run(args, check=True, timeout=15, stdout=subprocess.DEVNULL)


class Router:
    def __init__(self):
        self.objects = {}
        self.mode = None
        self.headphone_props = {'volume': 1.0, 'mute': False, 'channelVolumes': [.35**3, .35**3]}

    def update(self, batch):
        for obj in batch:
            ident = obj['id']
            if obj.get('info', True) is None:
                self.objects.pop(ident, None)
            elif 'info' in obj:
                old = self.objects.setdefault(ident, {})
                old.update({k: v for k, v in obj.items() if k != 'info'})
                info = old.setdefault('info', {})
                for key, value in obj['info'].items():
                    if key in ('props', 'params'):
                        info.setdefault(key, {}).update(value)
                    else:
                        info[key] = value
        self.reconcile()

    def reconcile(self):
        nodes = {o['info']['props'].get('node.name'): o for o in self.objects.values()
                 if o.get('type') == 'PipeWire:Interface:Node'}
        card = next((o for o in self.objects.values()
                     if o.get('type') == 'PipeWire:Interface:Device'
                     and o['info']['props'].get('device.name') == CARD), None)
        if not card or PRIMARY not in nodes or ENHANCED not in nodes:
            return
        routes = card['info'].get('params', {}).get('EnumRoute', [])
        hp = next((r for r in routes if r.get('name') == 'analog-output-headphones'), None)
        if not hp or hp.get('available') not in ('yes', 'no'):
            return
        plugged = hp['available'] == 'yes'
        active = card['info'].get('params', {}).get('Route', [])
        expected_route = 'analog-output-headphones' if plugged else 'analog-output-speaker'
        if not any(r.get('name') == expected_route for r in active):
            return  # Let WirePlumber finish switching the hardware route first.
        mode = 'headphones' if plugged else 'speakers'
        if mode == self.mode:
            return
        if self.mode == 'headphones':
            for p in nodes[PRIMARY]['info'].get('params', {}).get('Props', []):
                if 'channelVolumes' in p:
                    self.headphone_props = {k: p[k] for k in ('volume', 'mute', 'channelVolumes') if k in p}
                    break
        if plugged:
            run('amixer', '-c', 'PCH', '--', 'sset', 'Headphone', '0dB', 'unmute')
            run('amixer', '-c', 'PCH', 'sset', 'Speaker', 'mute')
            run('amixer', '-c', 'PCH', 'sset', 'Bass Speaker', 'mute')
            props = self.headphone_props
            target = PRIMARY
        else:
            run('amixer', '-c', 'PCH', 'sset', 'Headphone', 'mute')
            run('amixer', '-c', 'PCH', 'sset', 'Speaker', '100%', 'unmute')
            run('amixer', '-c', 'PCH', 'sset', 'Bass Speaker', '100%', 'unmute')
            props = {'volume': 1.0, 'mute': False, 'channelVolumes': [1.0, 1.0]}
            target = ENHANCED
        run('pw-cli', 'set-param', str(nodes[PRIMARY]['id']), 'Props', json.dumps(props))
        run('wpctl', 'set-default', str(nodes[target]['id']))
        # Move existing application streams as well as new playback.
        for obj in nodes.values():
            p = obj['info']['props']
            if p.get('media.class') != 'Stream/Output/Audio' or p.get('node.name', '').startswith(('cs4208.', 'output.cs4208.')):
                continue
            destination = p.get('target.object')
            if destination is not None and str(destination) not in (PRIMARY, ENHANCED, str(nodes[PRIMARY]['id']), str(nodes[ENHANCED]['id']), str(nodes[PRIMARY]['info']['props'].get('object.serial')), str(nodes[ENHANCED]['info']['props'].get('object.serial'))):
                continue
            run('pw-metadata', '-n', 'default', str(obj['id']), 'target.object', target, 'Spa:String')
        self.mode = mode
        print('CS4208 route: ' + mode, flush=True)


def main():
    decoder = json.JSONDecoder()
    router = Router()
    buffer = ''
    utf8 = codecs.getincrementaldecoder('utf-8')()
    with subprocess.Popen(['pw-dump', '--monitor'], stdout=subprocess.PIPE) as proc:
        while True:
            chunk = proc.stdout.read1(65536)
            if not chunk:
                raise RuntimeError('PipeWire monitor disconnected')
            buffer += utf8.decode(chunk)
            while buffer.strip():
                buffer = buffer.lstrip()
                try:
                    batch, end = decoder.raw_decode(buffer)
                except json.JSONDecodeError:
                    break
                buffer = buffer[end:]
                router.update(batch)


if __name__ == '__main__':
    try:
        main()
    except (RuntimeError, OSError, subprocess.SubprocessError) as exc:
        print('Jack routing error: ' + str(exc), file=sys.stderr)
        sys.exit(1)
