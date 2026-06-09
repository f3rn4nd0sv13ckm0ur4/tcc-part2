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


