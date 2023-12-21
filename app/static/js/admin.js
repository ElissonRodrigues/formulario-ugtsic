
function openRecruiterForm() {
    document.getElementById("recruiterFormPopup").style.display = "block";
}

function closeRecruiterForm() {
    document.getElementById("recruiterFormPopup").style.display = "none";
}

function openCandidatesPage() {
    document.getElementById("candidatesPopup").style.display = "block";
}

function closeCandidatesPage() {
    document.getElementById("candidatesPopup").style.display = "none";
}

function updateAdminPanel() {

    const CSRFtoken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_access_token='))
        .split('=')[1];

    // Fazer uma solicitação GET para a API
    fetch('/api/estatisticas', {
        method: 'GET',
        headers: {
            'X-CSRF-TOKEN': CSRFtoken
        }
    })
        .then(response => response.json()) // Converter a resposta em JSON
        .then(data => {
            // Atualizar o número de administradores
            document.getElementById('totalAdmin').textContent = data.total_administradores;
            // Atualizar o número de recrutadores
            document.getElementById('totalRecruiter').textContent = data.total_entrevistadores;
            // Atualizar o número de candidatos
            document.getElementById('totalCandidates').textContent = data.total_candidatos;
        })
        .catch(error => {
            console.error('Erro:', error);
            // Definir o texto para "Erro" se ocorrer um erro
            document.getElementById('totalAdmin').textContent = "Erro";
            document.getElementById('totalRecruiter').textContent = "Erro";
            document.getElementById('totalCandidates').textContent = "Erro";
        });
}

// Chamar a função quando a página é carregada
window.onload = updateAdminPanel;

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

// Quando o usuário clicar no botão, fecha a sessão atual e redireciona para a página de login
document.getElementById('logout-button').addEventListener('click', function() {

    // Faz uma solicitação para o endpoint /logout
    const CSRFtoken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_access_token='))
        .split('=')[1];
    
    fetch('/api/logout', {
        method: 'DELETE',
        headers: {
            'X-CSRF-TOKEN': CSRFtoken
        }
    })
    .then(response => {
        if (response.ok) {
            // Redireciona para a página de login
            window.location.href = '/login';
        } else {
            console.error('Logout failed');
        }
    })
        .catch(error => console.error('Error:', error));
    
    var cookies = document.cookie.split(";");

    for (var i = 0; i < cookies.length; i++) {
        var cookie = cookies[i];
        var eqPos = cookie.indexOf("=");
        var name = eqPos > -1 ? cookie.substr(0, eqPos) : cookie;
        document.cookie = name + "=;expires=Thu, 01 Jan 1970 00:00:00 GMT";
    } 
   
});
