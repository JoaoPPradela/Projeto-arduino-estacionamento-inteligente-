// =======================================================
// ESTACIONAMENTO INTELIGENTE • JAVASCRIPT EM PORTUGUÊS
// =======================================================

let somLigado = false;
let contextoAudio = null;
let temporizadorBipe = null;
let intervaloAtual = null;
let temporizadorSimulacao = null;
let statusCancela = 'FECHADA';

// Emite um bipe sonoro sintetizado pelo navegador
function emitirBipe(frequencia, duracao = 0.08) {
  if (!somLigado) return;

  try {
    if (!contextoAudio) {
      contextoAudio = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (contextoAudio.state === 'suspended') {
      contextoAudio.resume();
    }

    const oscilador = contextoAudio.createOscillator();
    const controleVolume = contextoAudio.createGain();

    oscilador.frequency.value = frequencia;
    controleVolume.gain.value = 0.08;

    oscilador.connect(controleVolume);
    controleVolume.connect(contextoAudio.destination);

    oscilador.start();
    oscilador.stop(contextoAudio.currentTime + duracao);
  } catch (erro) {
    console.log("Aguardando interação de áudio:", erro);
  }
}

// Controla o intervalo e o ritmo dos bipes conforme a distância medida
function controlarRitmoBipes(distanciaCentimetros) {
  if (!somLigado || distanciaCentimetros == null || distanciaCentimetros <= 0 || distanciaCentimetros > 200) {
    if (temporizadorBipe) clearInterval(temporizadorBipe);
    temporizadorBipe = null;
    intervaloAtual = null;
    return;
  }

  let tempoIntervalo = distanciaCentimetros < 15 ? 120 : (distanciaCentimetros < 50 ? 200 : (distanciaCentimetros <= 100 ? 450 : 800));
  let frequenciaSom = distanciaCentimetros < 15 ? 2400 : (distanciaCentimetros < 50 ? 2200 : (distanciaCentimetros <= 100 ? 1900 : 1600));

  if (intervaloAtual === tempoIntervalo && temporizadorBipe) return;

  if (temporizadorBipe) clearInterval(temporizadorBipe);
  intervaloAtual = tempoIntervalo;
  temporizadorBipe = setInterval(() => emitirBipe(frequenciaSom), tempoIntervalo);
}

// Atualiza todas as informações da tela com os dados mais recentes da API
function atualizarPainel() {
  // 1. Busca os dados ao vivo da vaga
  fetch('/api/vaga/status')
    .then(resposta => {
      if (!resposta.ok) throw new Error('Status ' + resposta.status);
      return resposta.json();
    })
    .then(dadosRecebidos => {
      const distancia = dadosRecebidos.distancia_cm ?? 0;
      const nivel = dadosRecebidos.nivel_alerta || 'Atenção';
      const corAlerta = dadosRecebidos.cor || '#eab308';

      // Atualiza textos principais
      const elDistancia = document.getElementById('distanciaValor');
      if (elDistancia) {
        elDistancia.textContent = distancia;
        elDistancia.style.color = corAlerta;
      }
      const elNivel = document.getElementById('distanciaNivel');
      if (elNivel) {
        elNivel.textContent = 'Nível de ' + nivel.toLowerCase();
        elNivel.style.color = corAlerta;
      }
      const elSensor = document.getElementById('sensorStatus');
      if (elSensor) elSensor.textContent = dadosRecebidos.sensor_status;

      const elAlerta = document.getElementById('alertaTexto');
      if (elAlerta) elAlerta.textContent = dadosRecebidos.descricao_alerta;

      // Atualiza o estado da cancela remota
      statusCancela = dadosRecebidos.cancela_status || 'FECHADA';
      const elCancelaTxt = document.getElementById('cancelaTxt');
      if (elCancelaTxt) elCancelaTxt.textContent = statusCancela;
      const elBtnCancela = document.getElementById('btnCancela');
      if (elBtnCancela) elBtnCancela.className = (statusCancela === 'ABERTA') ? 'btn btn-azul' : 'btn btn-cinza';

      // Atualiza a barra visual de proximidade
      const barraProximidade = document.getElementById('barraPreenchimento');
      if (barraProximidade) {
        barraProximidade.style.width = Math.max(5, Math.min(100, ((200 - distancia) / 200) * 100)) + '%';
        barraProximidade.style.backgroundColor = corAlerta;
      }

      // Atualiza os LEDs virtuais
      ['ledVerde', 'ledAmarelo', 'ledVermelho'].forEach(idLed => {
        const led = document.getElementById(idLed);
        if (led) led.className = 'led-bolinha';
      });
      if (dadosRecebidos.led === 'Verde') document.getElementById('ledVerde')?.classList.add('led-verde-ativo');
      if (dadosRecebidos.led === 'Amarelo') document.getElementById('ledAmarelo')?.classList.add('led-amarelo-ativo');
      if (dadosRecebidos.led === 'Vermelho') document.getElementById('ledVermelho')?.classList.add('led-vermelho-ativo');

      // Atualiza a posição do carrinho na vaga
      const elCarro = document.getElementById('carroVirtual');
      if (elCarro) {
        const posicaoCarro = Math.max(10, Math.min(78, 78 - ((distancia - 15) / 165) * 65));
        elCarro.style.left = posicaoCarro + '%';
      }

      // Atualiza o ritmo dos bipes sonoros
      controlarRitmoBipes(distancia);
    })
    .catch(() => {
      // Ignora falhas temporárias se o servidor estiver reiniciando
    });

  // 2. Busca o histórico de medições para preencher a tabela
  fetch('/api/leituras/historico')
    .then(resposta => {
      if (!resposta.ok) throw new Error('Status ' + resposta.status);
      return resposta.json();
    })
    .then(dadosHistorico => {
      const tabelaCorpo = document.getElementById('tabelaCorpo');
      if (!tabelaCorpo) return;

      if (!dadosHistorico.historico?.length) {
        tabelaCorpo.innerHTML = '<tr><td colspan="4">Nenhuma leitura cadastrada</td></tr>';
        return;
      }

      tabelaCorpo.innerHTML = dadosHistorico.historico.map(registro => {
        const classeTag = registro.nivel_alerta === 'Longe' ? 'tag-verde' : (registro.nivel_alerta === 'Muito Perto' ? 'tag-vermelho' : 'tag-amarelo');
        const horario = registro.data_hora ? (registro.data_hora.includes(' ') ? registro.data_hora.split(' ')[1] : registro.data_hora) : '--:--';
        return `<tr><td>${horario}</td><td><strong>${registro.distancia_cm} cm</strong></td><td><span class="${classeTag}">${registro.nivel_alerta}</span></td><td>${registro.descricao_alerta}</td></tr>`;
      }).join('');
    })
    .catch(() => {});
}

// Envia uma nova leitura manual para a API
function enviarLeituraManual(distanciaCentimetros) {
  fetch('/api/leituras', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ vaga_codigo: 'VAGA-01', distancia_cm: parseFloat(distanciaCentimetros) })
  }).then(atualizarPainel).catch(() => {});
}

// Envia comando para os atuadores remotos (Cancela ou Buzzer)
function enviarComandoAtuador(atuador, acao) {
  fetch('/api/atuadores/comando', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ atuador: atuador, acao: acao })
  }).then(atualizarPainel).catch(() => {});
}

// Executa simulações de manobra em passos sucessivos
function executarSimulacao(passosDistancia) {
  if (temporizadorSimulacao) clearInterval(temporizadorSimulacao);
  let indicePasso = 0;

  temporizadorSimulacao = setInterval(() => {
    if (indicePasso >= passosDistancia.length) {
      clearInterval(temporizadorSimulacao);
      temporizadorSimulacao = null;
      return;
    }
    const distanciaAtual = passosDistancia[indicePasso++];
    const slider = document.getElementById('sliderDistancia');
    const sliderTxt = document.getElementById('sliderTexto');
    if (slider) slider.value = distanciaAtual;
    if (sliderTxt) sliderTxt.textContent = distanciaAtual + ' cm';
    enviarLeituraManual(distanciaAtual);
  }, 600);
}

// Configuração dos eventos quando a página é carregada
window.addEventListener('DOMContentLoaded', () => {
  const controleDeslizante = document.getElementById('sliderDistancia');
  if (controleDeslizante) {
    controleDeslizante.oninput = () => {
      const sliderTxt = document.getElementById('sliderTexto');
      if (sliderTxt) sliderTxt.textContent = controleDeslizante.value + ' cm';
    };
  }

  // Botões de teste e simulação
  document.getElementById('btnAplicarSlider')?.addEventListener('click', () => {
    if (controleDeslizante) enviarLeituraManual(controleDeslizante.value);
  });
  document.getElementById('btn68')?.addEventListener('click', () => {
    if (controleDeslizante) {
      controleDeslizante.value = 68;
      controleDeslizante.oninput();
    }
    enviarLeituraManual(68);
  });
  document.getElementById('btnEntrar')?.addEventListener('click', () => executarSimulacao([150, 110, 85, 68, 40, 15]));
  document.getElementById('btnSair')?.addEventListener('click', () => executarSimulacao([15, 45, 68, 95, 130, 175]));

  // Controles dos atuadores remotos
  document.getElementById('btnCancela')?.addEventListener('click', () => {
    enviarComandoAtuador('cancela', statusCancela === 'ABERTA' ? 'FECHAR' : 'ABRIR');
  });
  document.getElementById('btnBuzzerRemoto')?.addEventListener('click', () => {
    enviarComandoAtuador('buzzer', 'TESTE');
    emitirBipe(2000, 0.4);
  });

  // Botão para ligar e desligar o som
  const botaoAlarmeSonoro = document.getElementById('btnAudio');
  if (botaoAlarmeSonoro) {
    botaoAlarmeSonoro.onclick = () => {
      somLigado = !somLigado;
      botaoAlarmeSonoro.innerHTML = somLigado ? '🔊 Som de Bipes: <strong>Ligado</strong>' : '🔇 Som de Bipes: <strong>Desligado</strong>';
      botaoAlarmeSonoro.classList.toggle('ativo', somLigado);
      if (!somLigado && temporizadorBipe) clearInterval(temporizadorBipe);
      atualizarPainel();
    };
  }

  // Atualização inicial e periódica a cada 350 milissegundos
  atualizarPainel();
  setInterval(atualizarPainel, 350);
});
