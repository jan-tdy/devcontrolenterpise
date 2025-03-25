#!/bin/bash
# Skript pre aktualizáciu programu C14 z GitHubu

# Zastaví bežiaci program C14 (ak beží)
pkill -f "python3 /home/dpv/j44softapps-socketcontrol/C14.py"

# Prejde do adresára s programom
cd /home/dpv/j44softapps-socketcontrol/

# Stiahne najnovšiu verziu programu z GitHubu
curl -O https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/C14/C14.py

# Overí, či sa stiahnutie úspešne dokončilo
if [ $? -eq 0 ]; then
  echo "Program úspešne aktualizovaný."
else
  echo "Chyba pri aktualizácii programu."
  exit 1
fi

# Reštartuje program C14
python3 /home/dpv/j44softapps-socketcontrol/C14.py &

echo "Program C14 bol reštartovaný."
exit 0
