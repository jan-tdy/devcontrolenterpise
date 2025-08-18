#!/bin/bash
# do not delete - script to startup jadiv devcontrol enterpise - do net change any part - if you ignore this warnig startup can stop working
(
for i in {1..100}; do
  echo $i
  sleep 0.014
done
) | zenity --progress \
  --title="DEVCONTROL - aktualizácia" \
  --text="Štartujem najnovšiu verziu programu... Prosím čakajte..." \
  --percentage=0 \
  --auto-close &


# Zastaví bežiaci program C14 (ak beží)
pkill -f "python3 /home/dpv/j44softapps-socketcontrol/Astrofoto.py"

# Prejde do adresára s programom
cd /home/dpv/j44softapps-socketcontrol/

# Stiahne najnovšiu verziu programu z GitHubu
curl -O https://raw.githubusercontent.com/jan-tdy/devcontrolenterpise/main/Astrofoto/Astrofoto.py

# Overí, či sa stiahnutie úspešne dokončilo
if [ $? -eq 0 ]; then
  echo "Program úspešne aktualizovaný a na3tartovan9."
else
  echo "Chyba pri aktualizácii programu alebo/a 3tarte programu."
  exit 1
fi

# Reštartuje program C14
python3 /home/dpv/j44softapps-socketcontrol/Astrofoto.py &

exit 0
