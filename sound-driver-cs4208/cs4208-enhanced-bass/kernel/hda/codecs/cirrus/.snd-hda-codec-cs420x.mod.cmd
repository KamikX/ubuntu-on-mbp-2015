savedcmd_snd-hda-codec-cs420x.mod := printf '%s\n'   cs420x.o | awk '!x[$$0]++ { print("./"$$0) }' > snd-hda-codec-cs420x.mod
