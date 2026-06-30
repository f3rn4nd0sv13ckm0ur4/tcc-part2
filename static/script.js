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

window.onload = function () {
  controlarCriarConta();
};

function alerta() {
    Swal.fire({
  title: "Item Adicionado com Sucesso!",
  icon: "success",
  draggable: true
});
}

function showToast(msg){
    const t=document.getElementById("toast");
    t.textContent=msg;
    t.classList.add("show");

    setTimeout(()=>t.classList.remove("show"),3000);
}

// horário automático
window.onload = () => {
    const now = new Date();
    document.getElementById("hora").value =
        now.getHours().toString().padStart(2,'0') + ":" +
        now.getMinutes().toString().padStart(2,'0');
}
//pagina de registrar itens
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
//pagina de retirar itens
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

function reset(){
let resposta = confirm
("tem certeza que deseaja resetar o estoque");
if (resposta){
  alert ("dados resetados com sucesso");
}
else {alert ("operação cancelada");
}
}