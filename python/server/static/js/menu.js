console.log("JS carregado!");

// Modos: 0 = Manual (dpad + velocidade), 1 = Autônomo (tudo travado), 3 = Garra (fork-dpad + velocidade)
let dadosMovimento = {
  modo: 0,
  direcao: "",
  velocidade: 0
};

// Referências
const modeToggle = document.getElementById('modeToggle');
const modeToggleAction = document.getElementById('modeToggleAction');
const dpadButtons = document.querySelectorAll('.dbtn');
const speedInput = document.getElementById('speed');
const speedValue = document.getElementById('speedValue');
const forkSpeedInput = document.getElementById('forkSpeed');
const forkSpeedValue = document.getElementById('forkSpeedValue');

// Botões do dpad principal (movimento) e do garfo, separados
const moveButtons = document.querySelectorAll('.dpad .dbtn');
const forkButtons = document.querySelectorAll('.fork-buttons .dbtn');

// Função que aplica as regras de cada modo
function setMode(newMode) {
  dadosMovimento.modo = newMode;
  modeToggle.dataset.mode = newMode;

  let moveEnabled = false;
  let forkEnabled = false;

  if (newMode === 0) {
    modeToggleAction.textContent = "Manual";
    moveEnabled = true;
  } else if (newMode === 1) {
    modeToggleAction.textContent = "Autônomo";
    // tudo travado
  } else if (newMode === 3) {
    modeToggleAction.textContent = "Garra";
    forkEnabled = true;
  }

  // Habilita/desabilita cada conjunto de controles de acordo com o modo
  moveButtons.forEach(btn => btn.disabled = !moveEnabled);
  forkButtons.forEach(btn => btn.disabled = !forkEnabled);
  speedInput.disabled = !moveEnabled;
  forkSpeedInput.disabled = !forkEnabled;

  // Zera o slider e o valor exibido do controle que ficou desabilitado,
  // para não carregar um valor "fantasma" de um modo anterior
  if (!moveEnabled) {
    speedInput.value = 0;
    speedValue.textContent = "0";
  }
  if (!forkEnabled) {
    forkSpeedInput.value = 0;
    forkSpeedValue.textContent = "0";
  }

  // Como trocamos de modo, a velocidade e a direção antigas não fazem
  // mais sentido para o novo contexto
  dadosMovimento.velocidade = 0;
  dadosMovimento.direcao = "";
}

// Lógica de ciclo de modos no clique
modeToggle.addEventListener('click', () => {
  let currentMode = dadosMovimento.modo;
  let nextMode;

  if (currentMode === 0) nextMode = 1;
  else if (currentMode === 1) nextMode = 3;
  else if (currentMode === 3) nextMode = 0;

  setMode(nextMode);
  console.log('Modo alterado para:', nextMode);
  enviaDados();
});

// Inicializa a tela no estado correto
setMode(0);

document.addEventListener('keydown', (event) => {
  const modo = dadosMovimento.modo;

  // Autônomo: teclado não faz nada
  if (modo === 1) return;

  switch (event.key) {
    case 'ArrowUp':
    case 'w':
      if (modo !== 0) return; // só no modo Manual
      dadosMovimento.direcao = 'up';
      break;
    case 'ArrowDown':
    case 's':
      if (modo !== 0) return;
      dadosMovimento.direcao = 'down';
      break;
    case 'ArrowLeft':
    case 'a':
      if (modo !== 0) return;
      dadosMovimento.direcao = 'left';
      break;
    case 'ArrowRight':
    case 'd':
      if (modo !== 0) return;
      dadosMovimento.direcao = 'right';
      break;
    case 'q':
      if (modo !== 3) return; // só no modo Garra
      dadosMovimento.direcao = 'fork-up';
      break;
    case 'e':
      if (modo !== 3) return;
      dadosMovimento.direcao = 'fork-down';
      break;
    default:
      return;
  }
  enviaDados();
});

// Cliques nos botões do dpad (movimento) e do garfo
dpadButtons.forEach(btn => {
  btn.addEventListener('click', () => {
    dadosMovimento.direcao = btn.dataset.dir;
    console.log('Direção pressionada:', dadosMovimento.direcao);
    enviaDados();
  });
});

// Slider de velocidade das rodas — só atualiza dadosMovimento no modo Manual
speedInput.addEventListener('input', () => {
  speedValue.textContent = speedInput.value;
  if (dadosMovimento.modo !== 0) return;
  dadosMovimento.velocidade = parseInt(speedInput.value);
  console.log('Velocidade das Rodas:', speedInput.value);
  enviaDados();
});

// Slider de velocidade do garfo — só atualiza dadosMovimento no modo Garra
forkSpeedInput.addEventListener('input', () => {
  forkSpeedValue.textContent = forkSpeedInput.value;
  if (dadosMovimento.modo !== 3) return;
  dadosMovimento.velocidade = parseInt(forkSpeedInput.value);
  console.log('Velocidade do Garfo:', forkSpeedInput.value);
  enviaDados();
});

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