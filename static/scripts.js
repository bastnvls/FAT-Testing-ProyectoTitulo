// scripts.js

// 1) Función reutilizable para listar archivos
function setupFileUpload(inputId, listId) {
  const input = document.getElementById(inputId);
  const list = document.getElementById(listId);
  input.addEventListener('change', e => {
    list.innerHTML = '';
    Array.from(e.target.files).forEach(f => {
      const el = document.createElement('div');
      el.className = 'file-item';
      el.innerHTML = `<i class="fas fa-file mr-1"></i>${f.name}`;
      list.appendChild(el);
    });
  });
}

// 2) Validar .TXT para el input principal
document.getElementById('file').addEventListener('change', function (e) {
  const file = e.target.files[0];
  if (file && file.type !== "text/plain") {
    // SweetAlert2
    Swal.fire({
      icon: 'warning',
      title: 'Archivo inválido',
      text: 'Por favor, selecciona un archivo de texto (.txt)',
      confirmButtonText: 'Entendido'
    });
    e.target.value = ''; // resetea el input
  }
});

// 3) Actualiza etiquetas custom-file (Bootstrap)
$(document).on('change', '.custom-file-input', function () {
  const names = Array.from(this.files).map(f => f.name).join(', ');
  $(this).next('.custom-file-label').text(names || 'Seleccionar imágenes');
});

// 4) Progress bar
function showLoading() {
  $("#loading").css("display", "flex");
  startProgressBar();
}

function startProgressBar() {
  const progressBar = $(".progress-bar");
  let width = 0;
  const interval = setInterval(() => {
    width += 7;
    progressBar.css("width", width + "%").attr("aria-valuenow", width);
    if (width >= 100) {
      clearInterval(interval);
      $("#loading").css("display", "none");
    }
  }, 120);
}

// 5) Validación HTML5 + showLoading
function validateForm(event) {
  const form = document.getElementById('uploadForm');
  if (!form.checkValidity()) {
    event.preventDefault();
    return false;
  }
  showLoading();
  return true;
}

// 6) Validación de límite de imágenes con SweetAlert2 y llamado funcion listar archivos (txt)
document.addEventListener('DOMContentLoaded', () => {

  // funcion para mostrar nombre del archvio txt seleccionado en el formulario
  setupFileUpload('file', 'mainFileList');

  const form = document.getElementById('uploadForm');
  const limits = {
    file11: { name: 'Sección 1.1', max: 5 },
    file12: { name: 'Sección 1.2', max: 9 },
    file13: { name: 'Sección 1.3', max: 2 },
  };

  form.addEventListener('submit', e => {
    const errors = [];

    Object.keys(limits).forEach(id => {
      const input = document.getElementById(id);
      const { name, max } = limits[id];
      if (input.files.length > max) {
        errors.push(`${name}: máximo ${max} imágenes (seleccionaste ${input.files.length}).`);
      }
    });

    if (errors.length) {
      e.preventDefault();
      e.stopImmediatePropagation();

      Swal.fire({
        icon: 'warning',
        title: 'Errores en imágenes',
        html: errors.join('<br>'),
        confirmButtonText: 'Corregir'
      });
    }
    // si no hay errores, NO hacemos preventDefault ni stopImmediatePropagation
    // y el resto de listeners (validateForm, showLoading, etc.) se ejecutan
  }, /* useCapture = */ true);
});