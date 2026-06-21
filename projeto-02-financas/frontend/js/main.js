async function checkApiStatus() {
  const statusElement = document.getElementById("api-status");

  try {
    const data = await Api.health();

    if (data.status === "ok") {
      statusElement.textContent = "Ligada";
      statusElement.classList.add("online");
    } else {
      statusElement.textContent = "Resposta inesperada";
      statusElement.classList.add("warning");
    }
  } catch (error) {
    statusElement.textContent = "Indisponível";
    statusElement.classList.add("offline");
  }
}

async function startApp() {
  await checkApiStatus();

  try {
    await initialiseDashboard();
  } catch (error) {
    console.error(error);
    alert("Ocorreu um erro ao carregar os dados do dashboard.");
  }
}

startApp();
