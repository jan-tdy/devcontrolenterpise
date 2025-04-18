#!/bin/bash

echo "📦 Vitajte v programe na nastavenie desktop launcherov pre všetkých používateľov!"
echo "Zdroje sú z: /home/dpv/j44softapps-socketcontro/LAUNCHER-DESKTOP-JADIVDEVCONTRASTROFOT.desktop"
echo "Tento launcher bude nainštalovaný do /usr/share/applications a dostupný v systéme. 🖥️"
echo ""
read -p "Napíšte y na pokračovanie alebo n na ukončenie: " odpoved

if [[ "$odpoved" == "y" ]]; then
    echo "✅ Pokračujem v kopírovaní... (potrebné sudo práva)"

    # Pôvodný súbor
    SOURCE="/home/dpv/j44softapps-socketcontro/LAUNCHER-DESKTOP-JADIVDEVCONTRASTROFOT.desktop"

    # Cieľový adresár pre systém
    MENU_TARGET="/usr/share/applications"

    # Kopírovanie so sudo
    sudo cp "$SOURCE" "$MENU_TARGET/"

    # Nastavenie spustiteľnosti
    sudo chmod +x "$MENU_TARGET/LAUNCHER-DESKTOP-JADIVDEVCONTRASTROFOT.desktop"

    # Registrácia do systémového menu
    sudo xdg-desktop-menu install "$MENU_TARGET/LAUNCHER-DESKTOP-JADIVDEVCONTRASTROFOT.desktop"

    echo "🎉 Hotovo! Launcher je pridaný do systémového menu pre všetkých používateľov."

elif [[ "$odpoved" == "n" ]]; then
    echo "❌ Ukončujem program podľa vašej voľby."
    exit 0
else
    echo "⚠️ Neznáma odpoveď. Skúste znovu spustiť a napísať y alebo n."
    exit 1
fi
