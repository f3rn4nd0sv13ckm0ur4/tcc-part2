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
            text: 'Esta ação irá apagar todos os itens do estoque!',
            icon: 'warning',
            showCancelButton: true,
            confirmButtonColor: '#d33',
            cancelButtonColor: '#3085d6',
            confirmButtonText: 'Sim, resetar!',
            cancelButtonText: 'Cancelar'
        }).then((result) => {
            if (result.isConfirmed) {
                Swal.fire(
                    'Resetado!',
                    'O estoque foi resetado com sucesso.',
                    'success'
                ).then(() => {
                    const form = document.getElementById("formReset");
                    if (form) form.submit();
                });
            } else if (result.dismiss === Swal.DismissReason.cancel) {
                Swal.fire(
                    'Cancelado',
                    'A operação foi cancelada. Seu estoque não foi alterado.',
                    'info'
                );
            }
        });
    } else {
        const aceitou = confirm("⚠️ Tem certeza que deseja resetar todo o estoque?");
        if (aceitou) {
            alert("✅ Estoque resetado!");
            const form = document.getElementById("formReset");
            if (form) form.submit();
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