#!/bin/bash
# Skript pre aktualizáciu programu Astrofoto z GitHubu

# Zastaví bežiaci program C14 (ak beží)
pkill -f "python3 /home/dpv/j44softapps-socketcontrol/astrofoto.py"

# Prejde do adresára s programom
cd /home/dpv/j44softapps-socketcontrol/

# Stiahne najnovšiu verziu programu z GitHubu
curl -O https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/Astrofoto/Astrofoto.py

# Overí, či sa stiahnutie úspešne dokončilo
if [ $? -eq 0 ]; then
  echo "Program úspešne aktualizovaný."
else
  echo "Chyba pri aktualizácii programu."
  exit 1
fi

# Reštartuje program Astrofoto
python3 /home/dpv/j44softapps-socketcontrol/Astrofoto.py &

echo "Program Astrofoto bol reštartovaný."
exit 0
