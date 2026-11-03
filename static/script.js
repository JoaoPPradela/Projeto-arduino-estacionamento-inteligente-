// =======================================================
// ESTACIONAMENTO INTELIGENTE • JS COMPACTO (100% FUNCIONAL)
// =======================================================

let somLigado = false, audioCtx = null, timerBipe = null, intervaloAtual = null, timerSimulacao = null;

// Toca o bipe sonoro do buzzer
function bipe(freq, dur = 0.08) {
  if (!somLigado) return;
  if (!audioCtx) audioCtx = new (window.AudioContext || window.webkitAudioContext)();
  if (audioCtx.state === 'suspended') audioCtx.resume();

  const osc = audioCtx.createOscillator(), gain = audioCtx.createGain();
  osc.frequency.value = freq;
  gain.gain.value = 0.08;
  osc.connect(gain);
  gain.connect(audioCtx.destination);
  osc.start();
  osc.stop(audioCtx.currentTime + dur);
}

// Controla o ritmo dos bipes conforme a distância
function tocarBipes(dist) {
  if (!somLigado || dist == null || dist <= 0 || dist > 200) {
    if (timerBipe) clearInterval(timerBipe);
    timerBipe = intervaloAtual = null;
    return;
  }

  // Define tempo e frequência conforme as faixas da apresentação
  let tempo = dist < 15 ? 120 : (dist < 50 ? 200 : (dist <= 100 ? 450 : 800));
  let freq = dist < 15 ? 2400 : (dist < 50 ? 2200 : (dist <= 100 ? 1900 : 1600));

  if (intervaloAtual === tempo && timerBipe) return;
  if (timerBipe) clearInterval(timerBipe);
  intervaloAtual = tempo;
  timerBipe = setInterval(() => bipe(freq), tempo);
}

// Atualiza o painel e o histórico
function atualizar() {
  // 1. Dados em tempo real da vaga
  fetch('/api/vaga/status')
    .then(r => r.json())
    .then(dados => {
      const dist = dados.distancia_cm ?? 0;
      document.getElementById('distanciaValor').textContent = dist;
      document.getElementById('distanciaValor').style.color = dados.cor;
      document.getElementById('distanciaNivel').textContent = 'Nível de ' + (dados.nivel_alerta || '').toLowerCase();
      document.getElementById('distanciaNivel').style.color = dados.cor;
      document.getElementById('sensorStatus').textContent = dados.sensor_status;
      document.getElementById('alertaTexto').textContent = dados.descricao_alerta;

      // Barra de proximidade e LEDs
      const barra = document.getElementById('barraPreenchimento');
      barra.style.width = Math.max(5, Math.min(100, ((200 - dist) / 200) * 100)) + '%';
      barra.style.backgroundColor = dados.cor;

      ['ledVerde', 'ledAmarelo', 'ledVermelho'].forEach(id => {
        document.getElementById(id).className = 'led-bolinha';
      });
      if (dados.led === 'Verde') document.getElementById('ledVerde').className = 'led-bolinha led-verde-ativo';
      if (dados.led === 'Amarelo') document.getElementById('ledAmarelo').className = 'led-bolinha led-amarelo-ativo';
      if (dados.led === 'Vermelho') document.getElementById('ledVermelho').className = 'led-bolinha led-vermelho-ativo';

      // Posiciona o carrinho na vaga
      const pos = Math.max(10, Math.min(78, 78 - ((dist - 15) / 165) * 65));
      document.getElementById('carroVirtual').style.left = pos + '%';

      tocarBipes(dist);
    });

  // 2. Histórico de leituras na tabela
  fetch('/api/leituras/historico')
    .then(r => r.json())
    .then(dados => {
      const tb = document.getElementById('tabelaCorpo');
      if (!dados.historico?.length) return (tb.innerHTML = '<tr><td colspan="4">Sem leituras</td></tr>');

      tb.innerHTML = dados.historico.map(h => {
        const corTag = h.nivel_alerta === 'Longe' ? 'tag-verde' : (h.nivel_alerta === 'Muito Perto' ? 'tag-vermelho' : 'tag-amarelo');
        const hora = h.data_hora ? h.data_hora.split(' ')[1] || h.data_hora : '--:--';
        return `<tr><td>${hora}</td><td><strong>${h.distancia_cm} cm</strong></td><td><span class="${corTag}">${h.nivel_alerta}</span></td><td>${h.descricao_alerta}</td></tr>`;
      }).join('');
    });
}

// Envia uma nova leitura para a API
function enviar(dist) {
  fetch('/api/leituras', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ vaga_codigo: 'VAGA-01', distancia_cm: parseFloat(dist) })
  }).then(atualizar);
}

// Função única com loop para simulações
function simular(passos) {
  if (timerSimulacao) clearInterval(timerSimulacao);
  let i = 0;
  timerSimulacao = setInterval(() => {
    if (i >= passos.length) return clearInterval(timerSimulacao);
    document.getElementById('sliderDistancia').value = passos[i];
    document.getElementById('sliderTexto').textContent = passos[i] + ' cm';
    enviar(passos[i++]);
  }, 600);
}

// Inicialização dos botões e eventos
window.addEventListener('DOMContentLoaded', () => {
  const slider = document.getElementById('sliderDistancia');
  slider.oninput = () => document.getElementById('sliderTexto').textContent = slider.value + ' cm';

  document.getElementById('btnAplicarSlider').onclick = () => enviar(slider.value);
  document.getElementById('btn68').onclick = () => { slider.value = 68; slider.oninput(); enviar(68); };
  document.getElementById('btnEntrar').onclick = () => simular([150, 110, 85, 68, 40, 15]);
  document.getElementById('btnSair').onclick = () => simular([15, 45, 68, 95, 130, 175]);

  const btnAudio = document.getElementById('btnAudio');
  btnAudio.onclick = () => {
    somLigado = !somLigado;
    btnAudio.innerHTML = somLigado ? '🔊 Som de Bipes: <strong>Ligado</strong>' : '🔇 Som de Bipes: <strong>Desligado</strong>';
    btnAudio.classList.toggle('ativo', somLigado);
    if (!somLigado && timerBipe) clearInterval(timerBipe);
    atualizar();
  };

  atualizar();
  setInterval(atualizar, 350); // Loop de atualização em tempo real
});
