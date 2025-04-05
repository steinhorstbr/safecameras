document.addEventListener('DOMContentLoaded', function () {
    const addStreamForm = document.getElementById('add-stream-form');
    const refreshStreamsButton = document.getElementById('refresh-streams');
    const streamsTableBody = document.getElementById('streams-table-body');

    // Função para carregar a lista de streams
    function loadStreams() {
        fetch('/list_streams')
            .then(response => response.json())
            .then(data => {
                streamsTableBody.innerHTML = ''; // Limpa a tabela
                data.streams.forEach(stream => {
                    const row = document.createElement('tr');
                    row.innerHTML = `
                        <td>${stream.stream_key}</td>
                        <td>${stream.input_url}</td>
                        <td>${stream.recording_status}</td>
                        <td>${stream.viewing_status}</td>
                        <td>
                            ${stream.viewing_status === 'stopped' ?
                                `<button class="btn btn-success btn-sm" onclick="startViewing('${stream.stream_key}')">Iniciar Visualização</button>` :
                                `<button class="btn btn-warning btn-sm" onclick="stopViewing('${stream.stream_key}')">Parar Visualização</button>`
                            }
                            <button class="btn btn-danger btn-sm" onclick="removeStream('${stream.stream_key}')">Remover</button>
                        </td>
                    `;
                    streamsTableBody.appendChild(row);
                });
            });
    }

    // Adicionar um stream
    addStreamForm.addEventListener('submit', function (event) {
        event.preventDefault();
        const streamKey = document.getElementById('stream-key').value;
        const inputUrl = document.getElementById('input-url').value;

        fetch('/add_stream', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                stream_key: streamKey,
                input_url: inputUrl
            })
        })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                loadStreams(); // Atualiza a lista de streams
            });
    });

    // Iniciar visualização de um stream
    window.startViewing = function (streamKey) {
        fetch('/start_viewing', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                stream_key: streamKey
            })
        })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                loadStreams(); // Atualiza a lista de streams
            });
    };

    // Parar visualização de um stream
    window.stopViewing = function (streamKey) {
        fetch('/stop_viewing', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({
                stream_key: streamKey
            })
        })
            .then(response => response.json())
            .then(data => {
                alert(data.message);
                loadStreams(); // Atualiza a lista de streams
            });
    };

    // Remover um stream
    window.removeStream = function (streamKey) {
        if (confirm(`Tem certeza que deseja remover o stream ${streamKey}?`)) {
            fetch('/remove_stream', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    stream_key: streamKey
                })
            })
                .then(response => response.json())
                .then(data => {
                    alert(data.message);
                    loadStreams(); // Atualiza a lista de streams
                });
        }
    };

    // Atualizar a lista de streams
    refreshStreamsButton.addEventListener('click', loadStreams);

    // Carregar a lista de streams ao iniciar
    loadStreams();
});
