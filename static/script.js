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