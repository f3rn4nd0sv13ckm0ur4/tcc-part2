function mudarTema() {

    document.body.classList.toggle("dark");

    let botao = document.getElementById("botaoTema");

    if (botao) {
        if (document.body.classList.contains("dark")) {
            botao.innerHTML = "☀ Modo Claro";
        } else {
            botao.innerHTML = "🌙 Modo Escuro";
        }
    }
}

function alerta() {
    Swal.fire({
  title: "Item Adicionado com Sucesso!",
  icon: "success",
  draggable: true
});
}

function verificarLogin() {

  const usuario = document.getElementById("usuario").value;
  const senha = document.getElementById("senha").value;

  const usuarioCorreto = "1";
  const senhaCorreta = "2";

  if (usuario === usuarioCorreto && senha === senhaCorreta) {

    window.location.href = "estoque.html";

  } else {

    Swal.fire({
      icon: 'error',
      title: 'Erro!',
      text: 'Usuário ou senha incorretos!',
      confirmButtonColor: '#3c61a5'
    });

  }

}