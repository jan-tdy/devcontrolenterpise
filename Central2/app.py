<!DOCTYPE html>
<html lang="sk">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Ovládanie Hvezdárne - Central2</title>
  <script src="https://unpkg.com/@tailwindcss/browser@4"></script>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
  <style>
    body {
      font-family: 'Inter', sans-serif;
    }
    .led-green {
      background-color: green;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      display: inline-block;
    }
    .led-red {
      background-color: red;
      width: 16px;
      height: 16px;
      border-radius: 50%;
      display: inline-block;
    }
    .on-button {
      background-color: #4CAF50;
      color: white;
    }
    .on-button:hover {
      background-color: #45a049;
    }
    .off-button {
      background-color: #f44336;
      color: white;
    }
    .off-button:hover {
      background-color: #da190b;
    }
    .disabled-button {
      background-color: #cccccc;
      color: #666666;
      cursor: not-allowed;
    }
    .disabled-button:hover {
      background-color: #cccccc;
    }
    .camera-feed {
      width: 100%;
      max-width: 640px;
      height: auto;
      border: 1px solid #ccc;
      border-radius: 8px;
      cursor: pointer;
      margin-bottom: 1rem;
    }
  </style>
</head>
<body class="bg-gray-100 p-4">
  <div class="container mx-auto">
    <h1 class="text-3xl font-semibold text-center text-gray-800 mb-6">Ovládanie Hvezdárne - Central2</h1>
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Ovládanie C14 -->
      <div class="bg-white shadow-md rounded-lg p-6">
        <h2 class="text-xl font-semibold text-gray-700 mb-4">Ovládanie C14</h2>
        <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-4">
          <div>
            <label class="block text-gray-600 text-sm font-bold mb-2">NOUT</label>
            <div class="flex flex-col items-start space-y-2">
              <button id="NOUT-button" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded on-button" onclick="toggleZasuvkaC14(4, 'NOUT')">Zapnúť</button>
              <div id="NOUT-led" class="led-red"></div>
            </div>
          </div>
          <div>
            <label class="block text-gray-600 text-sm font-bold mb-2">C14</label>
            <div class="flex flex-col items-start space-y-2">
              <button id="C14-button" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded on-button" onclick="toggleZasuvkaC14(3, 'C14')">Zapnúť</button>
              <div id="C14-led" class="led-red"></div>
            </div>
          </div>
          <div>
            <label class="block text-gray-600 text-sm font-bold mb-2">RC16</label>
            <div class="flex flex-col items-start space-y-2">
              <button id="RC16-button" class="bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded on-button" onclick="toggleZasuvkaC14(2, 'RC16')">Zapnúť</button>
              <div id="RC16-led" class="led-red"></div>
            </div>
          </div>
        </div>
        <div class="mb-4">
          <button class="bg-green-500 hover:bg-green-700 text-white font-bold py-2 px-4 rounded w-full" onclick="spustiIndistarterC14()">Spustiť INDISTARTER na C14/UVEX</button>
        </div>
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label class="block text-gray-600 text-sm font-bold mb-2">Strecha Sever</label>
            <button class="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded w-full" onclick="ovladajStrechuC14('sever')">Sever</button>
          </div>
          <div>
            <label class="block text-gray-600 text-sm font-bold mb-2">Strecha Juh</label>
            <button class="bg-purple-500 hover:bg-purple-700 text-white font-bold py-2 px-4 rounded w-full" onclick="ovladajStrechuC14('juh')">Juh</button>
          </div>
        </div>
      </div>
      <!-- WAKE-ON-LAN & Kamery -->
      <div class="bg-white shadow-md rounded-lg p-6">
        <h2 class="text-xl font-semibold text-gray-700 mb-4">WAKE-ON-LAN & Kamery</h2>
        <div class="space-y-4">
          <button class="bg-indigo-500 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded w-full" onclick="wakeOnLan('00:c0:08:a9:c2:32')">Zapni AZ2000</button>
          <button class="bg-indigo-500 hover:bg-indigo-700 text-white font-bold py-2 px-4 rounded w-full" onclick="wakeOnLan('00:c0:08:aa:35:12')">Zapni GM3000</button>
        </div>
        <h2 class="text-xl font-semibold text-gray-700 mt-6 mb-4">ONVIF Kamery</h2>
        <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <label class="block text-gray-600 text-sm font-bold mb-2">Kamera Atacama</label>
            <img id="kamera-atacama-feed" src="" alt="Kamera Atacama" class="camera-feed" onclick="openCamera('atacama')">
          </div>
          <div>
            <label class="block text-gray-600 text-sm font-bold mb-2">Kamera Astrofoto</label>
            <img id="kamera-astrofoto-feed" src="" alt="Kamera Astrofoto" class="camera-feed" onclick="openCamera('astrofoto')">
          </div>
        </div>
        <h2 class="text-xl font-semibold text-gray-700 mt-6 mb-4">OTA Aktualizácie</h2>
        <button class="bg-yellow-500 hover:bg-yellow-700 text-white font-bold py-2 px-4 rounded w-full" onclick="aktualizujProgram()">Aktualizovať program</button>
      </div>
    </div>
    <footer class="mt-8 text-center text-gray-500 text-sm">
      Made by JaPySoft Tramtary & Gemini AI
    </footer>
  </div>
  <script>
    // Základná URL pre server
    const SERVER_URL = "http://172.20.20.133:5000";
    
    // Definícia kamier – každá má svoje prístupové údaje, port a cestu
    const cameras = {
      "atacama": {
        ip: "172.20.20.134",
        username: "admin", // Zmeň na správne meno
        password: "qwerty", // Zmeň na správne heslo
        port: 554,                 // RTSP port
        path: ""
      },
      "astrofoto": {
        ip: "172.20.20.131",
        username: "dpv-hard", // Zmeň na správne meno
        password: "lefton44", // Zmeň na správne heslo
        port: 2020,                // ONVIF port
        path: ""
      }
    };

    // Funkcia na zostavenie URL pre kameru
    function getCameraUrl(cameraKey) {
      const cam = cameras[cameraKey];
      return `http://${cam.username}:${cam.password}@${cam.ip}:${cam.port}${cam.path}`;
    }
    
    // Inicializácia kamerových feedov
    document.getElementById('kamera-atacama-feed').src = getCameraUrl('atacama');
    document.getElementById('kamera-astrofoto-feed').src = getCameraUrl('astrofoto');
    
    // Automatická aktualizácia feedu každých 5 sekúnd (pridáva časovú značku pre vyhnutie sa cache)
    setInterval(() => {
      const timestamp = new Date().getTime();
      document.getElementById('kamera-atacama-feed').src = getCameraUrl('atacama') + "?t=" + timestamp;
      document.getElementById('kamera-astrofoto-feed').src = getCameraUrl('astrofoto') + "?t=" + timestamp;
    }, 5000);
    
    // Zobrazenie toast notifikácie
    function showToast(message, type = 'success') {
      const toast = document.createElement('div');
      toast.className = `fixed bottom-4 right-4 bg-${type === 'success' ? 'green' : 'red'}-500 text-white py-2 px-4 rounded shadow-lg`;
      toast.textContent = message;
      document.body.appendChild(toast);
      setTimeout(() => toast.remove(), 3000);
    }
    
    // Odoslanie GET požiadavky s query parametrami
    async function sendRequest(endpoint, data = {}) {
      const queryString = new URLSearchParams(data).toString();
      const url = SERVER_URL + endpoint + "?" + queryString;
      try {
        const response = await fetch(url, { method: 'GET' });
        if (!response.ok) {
          throw new Error(`HTTP error! status: ${response.status}`);
        }
        const responseData = await response.json();
        return responseData;
      } catch (error) {
        console.error('Chyba:', error);
        showToast(`Chyba: ${error.message}`, 'error');
        throw error;
      }
    }
    
    // Aktualizácia LED stavu
    function updateLed(labelName, color) {
      const ledElement = document.getElementById(labelName + "-led");
      if (ledElement) {
        ledElement.className = color === 'green' ? 'led-green' : 'led-red';
      }
    }
    
    // Aktualizácia stavu tlačidla
    function updateButtonState(buttonId, isEnabled) {
      const button = document.getElementById(buttonId);
      if (button) {
        button.disabled = !isEnabled;
        button.className = isEnabled
          ? 'bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded on-button'
          : 'bg-gray-400 text-white font-bold py-2 px-4 rounded disabled-button';
      }
    }
    
    // Ovládanie zásuvky C14
    async function toggleZasuvkaC14(cislo_zasuvky, labelName) {
      const buttonId = `${labelName}-button`;
      const currentState = window.zasuvkyState ? window.zasuvkyState[labelName] : false;
      const zapnut = !currentState;
      updateButtonState(buttonId, false);
      const data = { cislo_zasuvky, zapnut, label_name: labelName };
      try {
        const responseData = await sendRequest('/ovladaj_zasuvku_c14', data);
        showToast(responseData.message);
        updateLed(labelName, zapnut ? 'green' : 'red');
        window.zasuvkyState = window.zasuvkyState || {};
        window.zasuvkyState[labelName] = zapnut;
        updateButtonState(buttonId, true);
        if (zapnut) {
          document.getElementById(buttonId).textContent = "Vypnúť";
          document.getElementById(buttonId).className = "bg-red-500 hover:bg-red-700 text-white font-bold py-2 px-4 rounded off-button";
        } else {
          document.getElementById(buttonId).textContent = "Zapnúť";
          document.getElementById(buttonId).className = "bg-blue-500 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded on-button";
        }
      } catch (error) {
        console.error("Chyba pri ovládaní zásuvky:", error);
        updateButtonState(buttonId, true);
      }
    }
    
    // Spustenie INDISTARTER na C14/UVEX
    async function spustiIndistarterC14() {
      try {
        const responseData = await sendRequest('/spusti_indistarter_c14');
        showToast(responseData.message);
      } catch (error) {
        console.error("Chyba pri spúšťaní indistarter:", error);
      }
    }
    
    // Ovládanie strechy C14
    async function ovladajStrechuC14(strana) {
      const data = { strana };
      try {
        const responseData = await sendRequest('/ovladaj_strechu_c14', data);
        showToast(responseData.message);
      } catch (error) {
        console.error("Chyba pri ovládaní strechy:", error);
      }
    }
    
    // Odoslanie Wake-on-LAN požiadavky
    async function wakeOnLan(mac_adresa) {
      const data = { mac_adresa };
      try {
        const responseData = await sendRequest('/wake_on_lan', data);
        showToast(responseData.message);
      } catch (error) {
        console.error("Chyba pri Wake-on-LAN:", error);
      }
    }
    
    // Aktualizácia programu
    async function aktualizujProgram() {
      try {
        const responseData = await sendRequest('/aktualizuj_program');
        showToast(responseData.message);
      } catch (error) {
        console.error("Chyba pri aktualizácii:", error);
      }
    }
    
    // Otvorenie kamery – prečíta URL z definovanej konfigurácie
    function openCamera(cameraKey) {
      const url = getCameraUrl(cameraKey);
      window.open(url, '_blank');
    }
  </script>
</body>
</html>
