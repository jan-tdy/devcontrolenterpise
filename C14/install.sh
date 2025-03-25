#!/bin/bash
# Tento skript nainštaluje potrebné závislosti pre spustenie aplikácie c14_gtk_app.

# Aktualizácia zoznamu balíkov
sudo apt update

# Inštalácia Python 3
sudo apt install -y python3

# Inštalácia GTK+ 3 a knižnice gi
sudo apt install -y libgtk-3-0 python3-gi

# Inštalácia knižnice wakeonlan
sudo pip3 install wakeonlan

echo "Všetky potrebné závislosti pre c14_gtk_app boli úspešne nainštalované."
