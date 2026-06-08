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
