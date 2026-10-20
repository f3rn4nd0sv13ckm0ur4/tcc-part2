function controlarCriarConta() {
  const tipo = document.getElementById("tipoUsuario");
  const box = document.getElementById("criarContaBox");

  if (!tipo || !box) {
    return;
  }

  if (tipo.value === "admin") {
    box.style.display = "flex";
  } else {
    box.style.display = "none";
  }
}

document.addEventListener("DOMContentLoaded", function () {
    controlarCriarConta();

    const horaEl = document.getElementById("hora");
    if (horaEl) {
        const now = new Date();
        horaEl.value =
            now.getHours().toString().padStart(2, '0') + ":" +
            now.getMinutes().toString().padStart(2, '0');
    }

    // Registrar Service Worker para PWA
    if ('serviceWorker' in navigator) {
        navigator.serviceWorker.register('/sw.js')
            .then(reg => console.log('Service Worker registrado!', reg))
            .catch(err => console.log('Erro ao registrar Service Worker:', err));
    }
});

function alerta() {
    Swal.fire({
        title: "Item Adicionado com Sucesso!",
        icon: "success",
        draggable: true
    });
}

function showToast(msg){
    const t = document.getElementById("toast");
    if (t) {
        t.textContent = msg;
        t.classList.add("show");
        setTimeout(() => t.classList.remove("show"), 3000);
    }
}

// pagina de registrar itens
function salvar(){
    let item = document.getElementById("item").value;
    let qtd = document.getElementById("qtd").value;
    let pessoa = document.getElementById("pessoa").value;
    let hora = document.getElementById("hora").value;

    if(!item || !qtd || !pessoa || !hora){
        alert("Preencha todos os campos!");
        return;
    }

    console.log({item,qtd,pessoa,hora});
    showToast("Item registrado com sucesso!");

    document.getElementById("item").value="";
    document.getElementById("qtd").value="";
    document.getElementById("pessoa").value="";
}

// pagina de retirar itens
function retirar(){
    let item = document.getElementById("item").value;
    let qtd = document.getElementById("qtd").value;
    let pessoa = document.getElementById("pessoa").value;
    let hora = document.getElementById("hora").value;
    let obs = document.getElementById("obs").value;

    if(!item || !qtd || !pessoa || !hora){
        alert("Preencha todos os campos obrigatórios!");
        return;
    }

    console.log({item,qtd,pessoa,hora,obs});
    showToast("Retirada registrada com sucesso!");

    document.getElementById("item").value="";
    document.getElementById("qtd").value="";
    document.getElementById("pessoa").value="";
    document.getElementById("obs").value="";
}

function confirmarResetEstoque() {
    if (typeof Swal !== "undefined") {
        Swal.fire({
            title: 'Tem certeza?',
            text: 'Esta ação irá zerar as quantidades de todos os itens do estoque (as movimentações serão preservadas)!',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#ff8800',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sim, resetar estoque!',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                const form = document.getElementById("formReset");
                if (form) {
                    form.submit();
                }
            } else if (result.dismiss === Swal.DismissReason.cancel) {
                Swal.fire(
                    'Cancelado',
                    'A operação foi cancelada. Seu estoque não foi alterado.',
                    'info'
                );
            }
        });
    } else {
        const aceitou = confirm(
            "⚠️ Tem certeza que deseja zerar a quantidade de todos os itens do estoque?"
        );
        if (aceitou) {
            const form = document.getElementById("formReset");
            if (form) {
                form.submit();
            }
        } else {
            alert("❌ Operação cancelada!");
        }
    }
}

function filtrarTabela() {
    const input = document.getElementById("campo-de-pesquisa") || document.getElementById("campoPesquisa");
    if (!input) return;
    const termo = input.value.toLowerCase().trim();
    const linhas = document.querySelectorAll("tbody tr");

    linhas.forEach(linha => {
        const textoLinha = linha.textContent.toLowerCase();
        if (textoLinha.includes(termo)) {
            linha.style.display = "";
        } else {
            linha.style.display = "none";
        }
    });
}

let assistenteTimer;
let assistenteConsulta = 0;

function atualizarAssistenteAoDigitar() {
    clearTimeout(assistenteTimer);
    const input = document.getElementById("campo-de-pesquisa");
    const painel = document.getElementById("resposta-assistente");
    if (!input || !painel) return;

    const termo = input.value.trim();
    if (!termo) {
        painel.className = "resposta-assistente assistente-oculto";
        painel.innerHTML = "<strong>Assistente do estoque</strong><span>Digite o nome de um item para verificar se ele está no sistema.</span>";
        return;
    }

    painel.classList.remove("assistente-oculto");
    painel.className = "resposta-assistente carregando";
    painel.innerHTML = "<strong>Consultando o sistema...</strong><span>Verificando o item informado.</span>";
    assistenteTimer = setTimeout(() => descreverItemPesquisado(), 450);
}

async function descreverItemPesquisado() {
    const input = document.getElementById("campo-de-pesquisa");
    const painel = document.getElementById("resposta-assistente");
    if (!input || !painel) return;

    const termo = input.value.trim();
    if (!termo) {
        atualizarAssistenteAoDigitar();
        return;
    }

    const consultaAtual = ++assistenteConsulta;
    painel.classList.remove("assistente-oculto");
    painel.className = "resposta-assistente carregando";
    painel.innerHTML = "<strong>Consultando o sistema...</strong><span>Verificando o item informado.</span>";

    try {
        const busca = await fetch(`/api/estoque/buscar?nome=${encodeURIComponent(termo)}`);
        const resultadoBusca = await busca.json();
        if (!busca.ok) throw new Error(resultadoBusca.erro || "Falha ao consultar o estoque");
        if (consultaAtual !== assistenteConsulta) return;

        if (!resultadoBusca.encontrado) {
            painel.className = "resposta-assistente aviso";
            painel.innerHTML = "<strong>Item não encontrado</strong><span>Esse item ainda não está cadastrado no sistema.</span>";
            return;
        }

        const item = resultadoBusca.item;
        const quantidade = Number(item.quantidade) || 0;
        const status = quantidade > 0 ? "Está disponível no sistema" : "Está cadastrado, mas sem estoque";
        painel.className = `resposta-assistente ${quantidade > 0 ? "sucesso" : "aviso"}`;
        painel.innerHTML = `<strong>${item.nome}<small>${status}</small></strong><span>Gerando uma descrição...</span>`;

        const resposta = await fetch(`/api/estoque/${item.id}/descricao`);
        const dados = await resposta.json();
        if (!resposta.ok) throw new Error(dados.erro || "Falha ao consultar o assistente");
        if (consultaAtual !== assistenteConsulta) return;

        const descricao = document.createElement("span");
        descricao.textContent = `${dados.descricao} Quantidade registrada: ${quantidade}.`;
        painel.replaceChildren();
        const titulo = document.createElement("strong");
        titulo.textContent = item.nome;
        const statusEl = document.createElement("small");
        statusEl.textContent = status;
        titulo.appendChild(statusEl);
        painel.append(titulo, descricao);
    } catch (erro) {
        if (consultaAtual !== assistenteConsulta) return;
        painel.className = "resposta-assistente aviso";
        painel.innerHTML = `<strong>Não foi possível gerar a descrição</strong><span>${erro.message}</span>`;
    }
}

function toggleMenu() {
    const menu = document.getElementById("menu-lateral");
    const overlay = document.getElementById("overlay-menu");
    if (menu && overlay) {
        menu.classList.toggle("open");
        overlay.classList.toggle("open");
    }
}
function ampliarImagem(url, nome) {
    if (typeof Swal !== "undefined") {
        Swal.fire({
            title: nome || "Imagem do Produto",
            imageUrl: url,
            imageAlt: nome || "Imagem do Produto",
            showCloseButton: true,
            showConfirmButton: false,
            focusClose: false,
            background: "#ffffff"
        });
    } else {
        window.open(url, "_blank");
    }
}
