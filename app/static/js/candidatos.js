// Fetch curriculos from the server
let hasDataBeenLoaded = false;

function fetchCurriculos(offset, limit) {
        
    const CSRFtoken = document.cookie
        .split('; ')
        .find(row => row.startsWith('csrf_access_token='))
        .split('=')[1];

    fetch(`/api/curriculos?offset=${offset}&limit=${limit}`, {
        headers: {
            'X-CSRF-TOKEN': CSRFtoken
        }
    })
    .then(response => response.json())
    .then(data => {
        // Render curriculos on the page
        if (data.length > 0) {
            renderCurriculos(data);
            hasDataBeenLoaded = true;
        } else {
            const curriculosContainer = document.getElementById('curriculos-container');
            if (hasDataBeenLoaded) {
                alert('Não há mais candidados disponiveis');
                document.getElementById('load-more-button').remove();
            } else {
                curriculosContainer.innerHTML = "<p>Nenhum candidato cadastrado</p>";
                document.getElementById('load-more-button').remove();
            }
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}
    // Load more curriculos when the button is clicked
    document.getElementById('load-more-button').addEventListener('click', () => {
        const curriculosContainer = document.getElementById('curriculos-container');
        const curriculosCount = curriculosContainer.childElementCount;
        fetchCurriculos(curriculosCount, 20);
    });

    // Initial load of curriculos
    fetchCurriculos(0, 9);

    function renderCurriculos(curriculos) {
        const curriculosContainer = document.getElementById('curriculos-container');
        curriculos.forEach(curriculo => {
            const curriculoElement = document.createElement('div');
            curriculoElement.innerHTML = `
                <h3 class="curriculo-nome">${curriculo[1]}</h3>
                <p class="cargo">${curriculo[4]}</p>
                <button class="ver-curriculo-button">+</button>
            `;
            curriculosContainer.appendChild(curriculoElement);
            
            // Adiciona um evento de clique ao nome do candidato
            curriculoElement.querySelector('.ver-curriculo-button').addEventListener('click', () => {
                let data = new Date(curriculo[9]);
                let dia = ("0" + data.getDate()).slice(-2);
                let mes = ("0" + (data.getMonth() + 1)).slice(-2);
                let ano = data.getFullYear();
                let horas = ("0" + data.getHours()).slice(-2);
                let minutos = ("0" + data.getMinutes()).slice(-2);

                let dataFormatada = `${dia}/${mes}/${ano} ${horas}:${minutos}`;

                document.getElementById('cadidato-info').innerHTML = `
                    <b>Email:</b> <a href="mailto:${curriculo[2]}" target="_blank">${curriculo[2]}</a>
                    <br>
                    <b>Telefone:</b> <a href="tel:${curriculo[3]}" target="_blank">${curriculo[3]}</a>
                    <br>
                    <b>Cargo:</b> ${curriculo[4]}
                    <br>
                    <b>Escolaridade:</b> ${curriculo[5]}
                    <br>
                    <b>Observações:</b> ${curriculo[6]}
                    <br>
                    <b>IP:</b> ${curriculo[8]}
                    <br>
                    <b>Data e Hora:</b> ${dataFormatada}
                    <br><br>
                    <b>Curriculo enviado pelo candidato:</b>
                    <iframe id="view-curriculo" src="${curriculo[7]}" width="100%" height="500px"></iframe>
                `;
                document.getElementById('popup-info').style.display = "block";
            });
        });
    }

// Quando o usuário clica em qualquer lugar fora do modal, fecha o modal
window.onclick = function(event) {
    var modal = document.getElementById('popup-info');
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

// Quando o usuário clica no elemento <span> (x), fecha o modal
document.getElementsByClassName("close")[0].onclick = function() {
    document.getElementById('popup-info').style.display = "none";
}

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