// Verifica se o arquivo foi selecionado antes de enviar o formulário e checa o tamanho do arquivo
document.getElementById('form_curriculum').addEventListener('submit', function (e) {
    var fileInput = document.getElementById('fileInput');
    if (!fileInput.files.length) {
        alert('Por favor, anexe um arquivo antes de enviar.');
        e.preventDefault(); // Impede o envio do formulário
    }
});

function updateFileName() {
    var fileInput = document.getElementById('fileInput');
    var arquivoInput = document.getElementById('arquivo');
    arquivoInput.value = fileInput.files[0] ? fileInput.files[0].name : '';

    var fileSize = fileInput.files[0]?.size; // Tamanho em bytes
    var maxSize = 1024 * 1024; // Tamanho máximo em bytes (1MB)

    if (fileSize && fileSize > maxSize) {
        alert('Por favor, selecione um arquivo com tamanho máximo de 1MB.');
        fileInput.value = ''; // Limpar a seleção do arquivo
        arquivoInput.value = ''; // Limpar o nome do arquivo
    }
}

// Mostra popup de erro ou sucesso ao enviar o formulário
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
