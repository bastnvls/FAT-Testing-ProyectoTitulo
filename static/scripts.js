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

// 2) Validar .TXT para el input principal (tipo y tamaño)
document.getElementById('file').addEventListener('change', function (e) {
  const file = e.target.files[0];
  const MAX_SIZE_TXT = 20 * 1024 * 1024; // 20 MB en bytes (logs de consola Cisco)

  if (file && file.type !== "text/plain") {
    // SweetAlert2
    Swal.fire({
      icon: 'warning',
      title: 'Archivo inválido',
      text: 'Por favor, selecciona un archivo de texto (.txt)',
      confirmButtonText: 'Entendido',
      confirmButtonColor: '#3b82f6'
    });
    e.target.value = ''; // resetea el input
    return;
  }

  // Validar tamaño del archivo TXT
  if (file && file.size > MAX_SIZE_TXT) {
    const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
    Swal.fire({
      icon: 'error',
      title: 'Archivo demasiado grande',
      html: `El archivo seleccionado pesa <strong>${sizeMB} MB</strong>.<br>El tamaño máximo permitido es <strong>20 MB</strong>.`,
      confirmButtonText: 'Entendido',
      confirmButtonColor: '#3b82f6',
      footer: '<span style="color: #64748b;">Sugerencia: Los logs de consola Cisco pueden ser extensos. Si excede este límite, contacte a soporte.</span>'
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
  const MAX_SIZE_IMAGE = 5 * 1024 * 1024; // 5 MB por imagen (JPG/PNG optimizado)
  const ALLOWED_IMAGE_TYPES = ['image/jpeg', 'image/png']; // Solo JPG y PNG
  const limits = {
    file11: { name: 'Sección 1.1', max: 5 },
    file12: { name: 'Sección 1.2', max: 9 },
    file13: { name: 'Sección 1.3', max: 2 },
  };

  form.addEventListener('submit', e => {
    const errors = [];

    // Validar cantidad de imágenes, tamaño y formato
    Object.keys(limits).forEach(id => {
      const input = document.getElementById(id);
      const { name, max } = limits[id];

      // Validar cantidad
      if (input.files.length > max) {
        errors.push(`${name}: máximo ${max} imágenes (seleccionaste ${input.files.length}).`);
      }

      // Validar tamaño y formato de cada imagen
      Array.from(input.files).forEach((file, index) => {
        // Validar formato (solo JPG y PNG)
        if (!ALLOWED_IMAGE_TYPES.includes(file.type)) {
          const extension = file.name.split('.').pop().toUpperCase();
          errors.push(`${name} - Imagen ${index + 1} (${file.name}): formato ${extension} no permitido. Solo se aceptan JPG y PNG.`);
        }

        // Validar tamaño
        if (file.size > MAX_SIZE_IMAGE) {
          const sizeMB = (file.size / (1024 * 1024)).toFixed(2);
          errors.push(`${name} - Imagen ${index + 1} (${file.name}): tamaño ${sizeMB} MB excede el límite de 5 MB.`);
        }
      });
    });

    if (errors.length) {
      e.preventDefault();
      e.stopImmediatePropagation();

      Swal.fire({
        icon: 'warning',
        title: 'Errores en archivos',
        html: errors.join('<br>'),
        confirmButtonText: 'Corregir',
        confirmButtonColor: '#3b82f6',
        footer: '<span style="color: #64748b;">Solo se permiten imágenes JPG y PNG de máximo 5 MB cada una</span>'
      });
    }
    // si no hay errores, NO hacemos preventDefault ni stopImmediatePropagation
    // y el resto de listeners (validateForm, showLoading, etc.) se ejecutan
  }, /* useCapture = */ true);
});