console.log("JS carregado!")

let dadosMovimento = {
  modo : false,
  direcao: "",        
  velocidade: 0,
  direcaoGarfo: "",  
  velocidadeGarfo: 0
};

// Referências dos elementos principais
const manualToggle = document.getElementById('manualToggle');
const manualToggleAction = document.getElementById('manualToggleAction');
const dpadButtons = document.querySelectorAll('.dbtn');
const speedInput = document.getElementById('speed');
const speedValue = document.getElementById('speedValue');

// Referências dos novos elementos do garfo
const forkSpeedInput = document.getElementById('forkSpeed');
const forkSpeedValue = document.getElementById('forkSpeedValue');

// Modo manual: liga/desliga e bloqueia os demais controles quando desligado
function setManualMode(isOn){
  manualToggle.dataset.manual = isOn;
  manualToggle.setAttribute('aria-pressed', isOn);
  manualToggleAction.textContent = isOn ? 'desligar' : 'ligar';

  dpadButtons.forEach(btn => btn.disabled = !isOn);
  speedInput.disabled = !isOn;
  forkSpeedInput.disabled = !isOn; // Destrava também o slider do garfo

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

    // Atalhos extras para o garfo (Q = Sobe, E = Desce)
    case 'q':
      dadosMovimento.direcaoGarfo = 'fork-up';
      break;
      
    case 'e':
      dadosMovimento.direcaoGarfo = 'down';
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

// Botões direcionais 
document.querySelectorAll('.dbtn').forEach(btn => {
  btn.addEventListener('click', () => {
    const direcaoPressionada = btn.dataset.dir;
    
    // Se o data-dir começar com "fork-", é comando do garfo
    if (direcaoPressionada.startsWith('fork-')) {
      // Remove o "fork-" do nome para enviar apenas "up" ou "down"
      dadosMovimento.direcaoGarfo = direcaoPressionada.replace('fork-', '');
      console.log('Garfo:', dadosMovimento.direcaoGarfo);
    } else {
      // Se não, é comando das rodas
      dadosMovimento.direcao = direcaoPressionada;
      console.log('Rodas:', dadosMovimento.direcao);
    }
    
    enviaDados();
  });
});

// Slider de velocidade principal
speedInput.addEventListener('input', () => {
  speedValue.textContent = speedInput.value;
  dadosMovimento.velocidade = parseInt(speedInput.value); // Convertido para Inteiro
  console.log('Velocidade:', speedInput.value);
  enviaDados()
});

// Slider de velocidade do garfo
forkSpeedInput.addEventListener('input', () => {
  forkSpeedValue.textContent = forkSpeedInput.value;
  dadosMovimento.velocidadeGarfo = parseInt(forkSpeedInput.value); // Convertido para Inteiro
  console.log('Velocidade Garfo:', forkSpeedInput.value);
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
      console.log('Sucesso:', data);
  })
  .catch(error => {
      console.error('Erro:', error);
  });
}