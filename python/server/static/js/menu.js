
console.log("JS carregado!")

let dadosMovimento = {
  modo : false,
  direcao: "",
  velocidade: 0 
};

// Referências dos elementos
const manualToggle = document.getElementById('manualToggle');
const manualToggleAction = document.getElementById('manualToggleAction');
const dpadButtons = document.querySelectorAll('.dbtn');

// Modo manual: liga/desliga e bloqueia os demais controles quando desligado
function setManualMode(isOn){
  manualToggle.dataset.manual = isOn;
  manualToggle.setAttribute('aria-pressed', isOn);
  manualToggleAction.textContent = isOn ? 'desligar' : 'ligar';

  dpadButtons.forEach(btn => btn.disabled = !isOn);
  speedInput.disabled = !isOn;

  // Envie esse valor (true/false) junto com as outras informações da requisição
  console.log('Modo manual:', isOn);
}

document.addEventListener('keydown', (event) => {

  if (manualToggle.dataset.manual !== 'true')
    return;

  switch(event.key) {
    case 'ArrowUp':
    case 'w':
      dadosMovimento.direcao = 'up';
      break;

    case 'ArrowDown':
    case 's':
      dadosMovimento.direcao = 'down';
      break;

    case 'ArrowLeft':
    case 'a':
      dadosMovimento.direcao = 'left';
      break;

    case 'ArrowRight':
    case 'd':
      dadosMovimento.direcao = 'right';
      break;

    default:
      return;
  }

  enviaDados();
});

manualToggle.addEventListener('click', () => {
  const isOn = manualToggle.dataset.manual === 'true';
  setManualMode(!isOn);
  dadosMovimento.modo = !isOn;
  console.log(!isOn);
  enviaDados();
});


// Botões direcionais: troque o console.log pela sua lógica (ex: enviar comando)
document.querySelectorAll('.dbtn').forEach(btn => {
  btn.addEventListener('click', () => {
    console.log('Direção pressionada:', btn.dataset.dir);
    dadosMovimento.direcao = btn.dataset.dir
    enviaDados()
  });
});

// Slider de velocidade
const speedInput = document.getElementById('speed');
const speedValue = document.getElementById('speedValue');
speedInput.addEventListener('input', () => {
  speedValue.textContent = speedInput.value;
  dadosMovimento.velocidade = speedInput.value;
  console.log('Velocidade:', speedInput.value);
  enviaDados()
});


function enviaDados()
{
  fetch('/', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json'
    },
    body: JSON.stringify(dadosMovimento)
  })
  .then(response => response.json())
  .then(data => {
      console.log('Sucesso:', data.mensagem);
  })
  .catch(error => {
      console.error('Erro:', error);
  });
}

