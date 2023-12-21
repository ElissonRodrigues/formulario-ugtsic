// Inicializa o tempo de sessão em 4 minutos
var tempoSessao = 4 * 60;

// Define a função que será chamada a cada segundo para atualizar o tempo restante
function atualizarTempoRestante() {
    var minutos = Math.floor(tempoSessao / 60);
    var segundos = tempoSessao % 60;
    document.getElementById("tempo_restante").textContent = (minutos < 10 ? "0" : "") + minutos + ":" + (segundos < 10 ? "0" : "") + segundos;
    tempoSessao--;
    if (tempoSessao < 0) {
        fimSessao();
    }
}

// Define a função que será chamada quando o tempo da sessão expirar
function fimSessao() {
    alert("Sua sessão expirou!");
    // Aqui você pode adicionar o código para encerrar a sessão
}

// Inicia o contador de tempo
atualizarTempoRestante();
var contador = setInterval(atualizarTempoRestante, 1000);


// função para mostrar popup de erro
$(document).ready(function(){
    var statusInfo = $('#status_info');
    if (statusInfo.length) {
        var statusText = statusInfo.text();
        if (statusText.includes("sucesso")) {
            swal("Sucesso!", statusText, "success");
        } else {
            swal("Erro!", statusText, "error");
        }
    }
});

// Path: app/static/js/cadastrar_admin.js