console.log("JS carregado!");

// Objeto que vai para o MQTT
let dadosMovimento = {
  modo: 0,
  direcao: "",
  velocidade: 0
};

// Armazenam as velocidades configuradas nos sliders
let velocidadeRodasConfigurada = 0;
let velocidadeGarfoConfigurada = 0;

// Evita milhares de comandos se segurar a tecla
let teclaPressionada = null;

// Referências
const modeToggle = document.getElementById('modeToggle');
const modeToggleAction = document.getElementById('modeToggleAction');
const speedInput = document.getElementById('speed');
const speedValue = document.getElementById('speedValue');
const forkSpeedInput = document.getElementById('forkSpeed');
const forkSpeedValue = document.getElementById('forkSpeedValue');

// Separa os botões para podermos travar/destravar independentemente
const wheelButtons = document.querySelectorAll('.dpad > .dbtn');
const forkButtons = document.querySelectorAll('.fork-buttons .dbtn');
const allButtons = document.querySelectorAll('.dbtn'); // Usado para escutar os cliques

// ---------- CONTROLE DE MODOS ----------
function setMode(newMode) {
  dadosMovimento.modo = newMode;
  modeToggle.dataset.mode = newMode;

  if (newMode === 0) { // MANUAL: Locomoção
    modeToggleAction.textContent = "Manual";

    // Destrava Rodas
    wheelButtons.forEach(btn => btn.disabled = false);
    speedInput.disabled = false;
    // Trava Garfo
    forkButtons.forEach(btn => btn.disabled = true);
    forkSpeedInput.disabled = true;

  } else if (newMode === 1) { // AUTÔNOMO: Tudo travado
    modeToggleAction.textContent = "Autônomo";

    wheelButtons.forEach(btn => btn.disabled = true);
    speedInput.disabled = true;
    forkButtons.forEach(btn => btn.disabled = true);
    forkSpeedInput.disabled = true;

  } else if (newMode === 3) { // GARRA: Foco no Garfo
    modeToggleAction.textContent = "Garra";

    // Trava Rodas 
    wheelButtons.forEach(btn => btn.disabled = true);
    speedInput.disabled = true;
    // Destrava Garfo
    forkButtons.forEach(btn => btn.disabled = false);
    forkSpeedInput.disabled = false;
  }
}

modeToggle.addEventListener('click', () => {
  let currentMode = dadosMovimento.modo;
  let nextMode;
  dadosMovimento.direcao = "up"; // Define a direção como "up" ao mudar de modo

  if (currentMode === 0) nextMode = 1;
  else if (currentMode === 1) nextMode = 3;
  else if (currentMode === 3) nextMode = 0;

  setMode(nextMode);
  console.log('Modo alterado para:', nextMode);
  enviaDados();
});

setMode(0); // Inicializa no modo manual

// ---------- LÓGICA DE MOVIMENTO (INICIAR E PARAR) ----------

function iniciarMovimento(direcao) {
  dadosMovimento.direcao = direcao;

  if (dadosMovimento.modo === 3) { // Se estiver no modo Garfo, usa a velocidade do garfo
    dadosMovimento.velocidade = velocidadeGarfoConfigurada;
  } else {
    dadosMovimento.velocidade = velocidadeRodasConfigurada;
  }

  console.log(`Iniciando movimento: ${direcao} a ${dadosMovimento.velocidade}%`);
  enviaDados();
}

function pararMovimento() {
  dadosMovimento.velocidade = 0;
  console.log('Parando movimento (velocidade 0)');
  enviaDados();
}

// ---------- EVENTOS DE MOUSE E TOUCH (TELA) ----------
allButtons.forEach(btn => {
  btn.addEventListener('contextmenu', e => e.preventDefault());

  const startEvent = (e) => {
    e.preventDefault();
    if (btn.disabled) return;
    iniciarMovimento(btn.dataset.dir);
    btn.classList.add('is-active');
  };

  const stopEvent = (e) => {
    e.preventDefault();
    if (btn.disabled) return;
    pararMovimento();
    btn.classList.remove('is-active');
  };

  btn.addEventListener('mousedown', startEvent);
  btn.addEventListener('mouseup', stopEvent);
  // btn.addEventListener('mouseleave', stopEvent); 

  btn.addEventListener('touchstart', startEvent, { passive: false });
  btn.addEventListener('touchend', stopEvent);
  btn.addEventListener('touchcancel', stopEvent);
});

document.addEventListener('mouseup', () => {
  if ([...allButtons].some(btn => btn.classList.contains('is-active'))) {
    pararMovimento();
    allButtons.forEach(btn => btn.classList.remove('is-active'));
  }
});

// ---------- EVENTOS DE TECLADO ----------
document.addEventListener('keydown', (event) => {
  if (event.repeat) return;

  let dir = "";

  // Aceita comandos das rodas APENAS no Modo 0
  if (dadosMovimento.modo === 0) {
    switch (event.key) {
      case 'ArrowUp': case 'w': dir = 'up'; break;
      case 'ArrowDown': case 's': dir = 'down'; break;
      case 'ArrowLeft': case 'a': dir = 'left'; break;
      case 'ArrowRight': case 'd': dir = 'right'; break;
    }
  }
  // Aceita comandos do garfo APENAS no Modo 3
  else if (dadosMovimento.modo === 3) {
    switch (event.key) {
      case 'ArrowUp': case 'w': dir = 'up'; break;
      case 'ArrowDown': case 's': dir = 'down'; break;
    }
  }

  // Se uma tecla válida para o modo atual foi pressionada
  if (dir !== "") {
    teclaPressionada = event.key;
    iniciarMovimento(dir);
  }
});

document.addEventListener('keyup', (event) => {
  if (event.key === teclaPressionada) {
    teclaPressionada = null;
    pararMovimento();
  }
});

// ---------- SLIDERS DE VELOCIDADE ----------
speedInput.addEventListener('input', () => {
  speedValue.textContent = speedInput.value;
  velocidadeRodasConfigurada = parseInt(speedInput.value);
});

forkSpeedInput.addEventListener('input', () => {
  forkSpeedValue.textContent = forkSpeedInput.value;
  velocidadeGarfoConfigurada = parseInt(forkSpeedInput.value);
});

// ---------- ENVIO PARA O SERVIDOR ----------
function enviaDados() {
  fetch('/', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json'
    },
    body: JSON.stringify(dadosMovimento)
  })
    .then(response => response.json())
    .then(data => {
      console.log('Sucesso:', data);
    })
    .catch(error => {
      console.error('Erro:', error);
    });
}

// ---------- RECEPÇÃO DE IMAGENS VIA WEBSOCKET ----------
// Descobre dinamicamente se a página usa HTTP ou HTTPS
const protocol = window.location.protocol === 'https:' ? 'wss://' : 'ws://';

// Conecta ao WebSocket usando o protocolo correto (WSS para ngrok, WS para local)
const ws = new WebSocket(protocol + location.host + '/video_feed');
const videoStream = document.getElementById('videoStream');

ws.onopen = () => {
  console.log('Conectado via WebSocket puro!');
};

ws.onmessage = (event) => {
  // 1. Verifica se o dado recebido é uma String (Base64)
  if (typeof event.data === "string") {
    if (event.data.length > 50) {
      // Evita duplicar o prefixo caso o robô já o tenha enviado
      if (event.data.startsWith("data:image")) {
        videoStream.src = event.data;
      } else {
        videoStream.src = "data:image/jpeg;base64," + event.data;
      }
    }
  }
  // 2. Verifica se o dado recebido é Binário (Blob)
  else if (event.data instanceof Blob) {
    // Cria um URL interno otimizado para renderizar bytes brutos imediatamente
    const imageUrl = URL.createObjectURL(event.data);
    videoStream.src = imageUrl;
  }
};

ws.onclose = () => {
  console.log('Conexão WebSocket encerrada.');
};