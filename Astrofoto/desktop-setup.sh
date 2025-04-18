#!/bin/bash

echo "📦 Vitajte v programe na nastavenie desktop launcherov!"
echo "Zdroje sú z: /home/dpv/j44softapps-socketcontro/LAUNCHER-DESKTOP-JADIVDEVCONTRASTROFOT.desktop"
echo "Spustite len raz – potom to už máte nastavené. 😉"
echo ""
read -p "Napíšte y na pokračovanie alebo n na ukončenie: " odpoved

if [[ "$odpoved" == "y" ]]; then
    echo "✅ Pokračujem v kopírovaní..."

    # Pôvodný súbor
    SOURCE="/home/dpv/j44softapps-socketcontro/LAUNCHER-DESKTOP-JADIVDEVCONTRASTROFOT.desktop"

    # Cieľové adresáre
    DESKTOP_TARGET="$HOME/Desktop"
    MENU_TARGET="$HOME/.local/share/applications"

    # Vytvorenie priečinkov ak neexistujú
    mkdir -p "$DESKTOP_TARGET"
    mkdir -p "$MENU_TARGET"

    # Kopírovanie
    cp "$SOURCE" "$DESKTOP_TARGET/"
    cp "$SOURCE" "$MENU_TARGET/"

    # Nastavenie spustiteľnosti
    chmod +x "$DESKTOP_TARGET/LAUNCHER-DESKTOP-JADIVDEVCONTRASTROFOT.desktop"
    chmod +x "$MENU_TARGET/LAUNCHER-DESKTOP-JADIVDEVCONTRASTROFOT.desktop"

    # Registrácia do menu a na plochu
    xdg-desktop-menu install --mode user "$MENU_TARGET/LAUNCHER-DESKTOP-JADIVDEVCONTRASTROFOT.desktop"
    xdg-desktop-icon install --mode user "$MENU_TARGET/LAUNCHER-DESKTOP-JADIVDEVCONTRASTROFOT.desktop"

    echo "🎉 Hotovo! Launcher je pridaný na plochu aj do menu."

elif [[ "$odpoved" == "n" ]]; then
    echo "❌ Ukončujem program podľa vašej voľby."
    exit 0
else
    echo "⚠️ Neznáma odpoveď. Skúste znovu spustiť a napísať y alebo n."
    exit 1
fi
