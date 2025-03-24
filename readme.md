Central2 - Umiestnenie súborov a spustenie
Kód pre Central2 sa skladá z dvoch častí:

HTML súbor (webová stránka): Tento súbor obsahuje HTML, CSS a JavaScript kód, ktorý definuje používateľské rozhranie (tlačidlá, rozloženie atď.) pre ovládanie zariadení.

Názov súboru: index.html (alebo central2.html, záleží na tvojom preferovanom pomenovaní)

Umiestnenie: Tento súbor by mal byť umiestnený v adresári, z ktorého bude webový server (Flask) obsluhovať statické súbory. V jednoduchom prípade to môže byť rovnaký adresár, kde je uložený aj skript Flask (app.py).

Python skript (Flask server): Tento skript definuje backendovú logiku aplikácie. Prijíma príkazy z webovej stránky (HTML) a odosiela ich na C14 cez SSH.

Názov súboru: app.py (alebo server.py, opäť záleží na tvojom preferovanom pomenovaní)

Umiestnenie: Tento súbor môže byť umiestnený v ľubovoľnom adresári, ale pre jednoduchosť ho odporúčam umiestniť do rovnakého adresára ako HTML súbor.

Príklad štruktúry adresárov:

hvezdaren/
├── app.py      # Flask server
└── index.html    # HTML stránka

Spustenie aplikácie Central2:

Uisti sa, že máš nainštalovaný Python a Flask:

sudo apt update
sudo apt install python3 python3-pip
pip3 install Flask
pip3 install paramiko  # Pre SSH komunikáciu

Spusti Flask server:

cd hvezdaren  # Prejdi do adresára s aplikáciou
python3 app.py  # Spusti Flask server

Otvorte webový prehliadač:

Prejdite na adresu http://<IP_adresa_Central2>:5000 (napr. http://172.20.20.133:5000).

Server pre C14
Pre C14, ako bolo spomenuté, je server už integrovaný priamo v kóde C14.py. Tento kód spúšťa socket server v samostatnom vlákne, ktorý počúva na prichádzajúce príkazy. Preto nie je potrebný žiadny ďalší server.

Spustenie aplikácie C14:

Uisti sa, že máš nainštalovaný Python a PyQt5:

sudo apt update
sudo apt install python3 python3-pip
pip3 install PyQt5
sudo apt install libcanberra-gtk* #fix звук на debian

Spusti skript C14.py:

python3 C14.py
