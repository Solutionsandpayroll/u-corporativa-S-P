class ContenidoDashboard {
    constructor() {
        this.currentSection = null;
        this.init();
    }

    init() {
        this.cacheDOM();
        this.bindEvents();
        this.initDynamicLinks();
        this.initEditDynamicLinks();
        this.initRenderToggleButtons();
        this.initFAB();
        this.initModals();
        this.bindEditModalSave();
        // Inicializar dropzones existentes al cargar
        this.inicializarDropzones();
    }

    // ─── INICIALIZAR DROPZONES (público) ───
    inicializarDropzones(container = document) {
        // Dropzones normales (banner)
        container.querySelectorAll('.dropzone:not(.dropzone-mini)').forEach(dz => this.setupDropzone(dz));
        // Dropzones mini (archivos adjuntos)
        container.querySelectorAll('.dropzone-mini').forEach(dz => this.setupDropzone(dz));
    }

    // ─── CONFIGURAR UN DROPZONE INDIVIDUAL ───
    setupDropzone(dropzoneElement) {
        if (!dropzoneElement) return;
        // Evitar duplicar eventos
        if (dropzoneElement.dataset.dropzoneInited === 'true') return;
        dropzoneElement.dataset.dropzoneInited = 'true';

        const fileInput = dropzoneElement.querySelector('input[type="file"]');
        if (!fileInput) return;

        const previewImg = dropzoneElement.querySelector('.dropzone-preview-thumb img');
        const previewIcon = dropzoneElement.querySelector('.dropzone-preview-thumb:not(img)');
        const fileName = dropzoneElement.querySelector('.dropzone-preview-name');
        const fileSize = dropzoneElement.querySelector('.dropzone-preview-size');
        const removeBtn = dropzoneElement.querySelector('.dropzone-remove-btn');

        // Función para mostrar preview
        const mostrarPreview = (file) => {
            if (!file) return;
            dropzoneElement.classList.add('has-file');
            fileName.textContent = file.name;
            fileSize.textContent = this.formatearTamano(file.size);
            if (file.type && file.type.startsWith('image/')) {
                const reader = new FileReader();
                reader.onload = (e) => {
                    if (previewImg) {
                        previewImg.src = e.target.result;
                        previewImg.style.display = 'block';
                        if (previewIcon) previewIcon.style.display = 'none';
                    }
                };
                reader.readAsDataURL(file);
            } else {
                if (previewImg) previewImg.style.display = 'none';
                if (previewIcon) previewIcon.style.display = 'flex';
            }
        };

        // Limpiar dropzone
        const limpiar = () => {
            fileInput.value = '';
            dropzoneElement.classList.remove('has-file');
            if (previewImg) {
                previewImg.src = '';
                previewImg.style.display = 'none';
            }
            if (previewIcon) previewIcon.style.display = 'flex';
            if (fileName) fileName.textContent = '';
            if (fileSize) fileSize.textContent = '';
        };

        // Evento change
        fileInput.addEventListener('change', function() {
            if (this.files && this.files.length > 0) {
                mostrarPreview(this.files[0]);
            } else {
                limpiar();
            }
        });

        // Botón remover
        if (removeBtn) {
            removeBtn.addEventListener('click', function(e) {
                e.preventDefault();
                e.stopPropagation();
                limpiar();
            });
        }

        // Arrastrar y soltar
        ['dragenter', 'dragover'].forEach(evt => {
            dropzoneElement.addEventListener(evt, function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropzoneElement.classList.add('dragover');
            });
        });
        ['dragleave', 'dragend'].forEach(evt => {
            dropzoneElement.addEventListener(evt, function(e) {
                e.preventDefault();
                e.stopPropagation();
                dropzoneElement.classList.remove('dragover');
            });
        });
        dropzoneElement.addEventListener('drop', function(e) {
            e.preventDefault();
            e.stopPropagation();
            dropzoneElement.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files && files.length > 0) {
                fileInput.files = files;
                // Disparar evento change manualmente
                const changeEvent = new Event('change', { bubbles: true });
                fileInput.dispatchEvent(changeEvent);
            }
        });
    }

    formatearTamano(bytes) {
        if (bytes < 1024) return bytes + ' B';
        if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
        return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
    }

    // ─── CONFIGURAR MODALES DE CONFIRMACIÓN Y ÉXITO ───
    initModals() {
        const confirmModal = document.getElementById('confirmDashModal');
        const confirmYes = document.getElementById('confirmDashYes');
        const confirmNo = document.getElementById('confirmDashNo');
        this.confirmCallback = null;

        confirmYes.addEventListener('click', () => {
            confirmModal.style.display = 'none';
            if (this.confirmCallback) this.confirmCallback();
            this.confirmCallback = null;
        });
        confirmNo.addEventListener('click', () => {
            confirmModal.style.display = 'none';
            this.confirmCallback = null;
        });
    }

    setDisplay(element, visible, fallbackDisplay = 'block') {
        if (element) {
            element.style.display = visible ? fallbackDisplay : 'none';
        }
    }

    // ─── FILAS DE ARCHIVOS ADJUNTOS (con input file) ───
    crearFilaAdjuntoHTML({ editMode = false, tipo = 'archivos', url = '', nombre = '' } = {}) {
        const fileClass = editMode ? 'input-archivo-file-editar' : 'input-archivo-file';

        const avisoActual = (editMode && url)
            ? `<small class="editar-help" style="margin-top:4px;">Archivo actual: ${nombre || url}. Sube uno nuevo solo si deseas reemplazarlo.</small>`
            : '';

        return `
            <div style="flex: 1; display: flex; flex-direction: column; gap: 4px;">
                <div class="dropzone dropzone-mini">
                    <input type="file" class="${fileClass}" accept="*/*">
                    <div class="dropzone-placeholder">
                        <div class="dropzone-icon"><i class="fas fa-cloud-arrow-up"></i></div>
                        <div class="dropzone-text-main">Selecciona archivo</div>
                        <div class="dropzone-text-sub">PDF, Word, Excel, etc.</div>
                    </div>
                    <div class="dropzone-preview">
                        <img class="dropzone-preview-thumb" style="display:none;" alt="Vista previa">
                        <div class="dropzone-preview-thumb"><i class="fas fa-file"></i></div>
                        <div class="dropzone-preview-info">
                            <div class="dropzone-preview-name"></div>
                            <div class="dropzone-preview-size"></div>
                        </div>
                        <button type="button" class="dropzone-remove-btn" title="Quitar archivo">
                            <i class="fas fa-times"></i>
                        </button>
                    </div>
                </div>
                ${avisoActual}
            </div>
            <button type="button" class="editar-btn-remover" title="Eliminar fila">
                <i class="fas fa-times"></i>
            </button>
        `;
    }

    crearFilaAdjuntoElement(options = {}) {
        const row = document.createElement('div');
        row.className = 'input-link-row dropzone-mini-wrapper';
        row.innerHTML = this.crearFilaAdjuntoHTML(options);
        // Inicializar el dropzone de esta nueva fila
        requestAnimationFrame(() => {
            const dropzoneMini = row.querySelector('.dropzone-mini');
            if (dropzoneMini) {
                this.setupDropzone(dropzoneMini);
            }
        });
        return row;
    }

    // ─── DETECCIÓN AUTOMÁTICA DE TIPO POR EXTENSIÓN ───
    detectarTipoPorExtension(nombreArchivo) {
        const ext = (nombreArchivo || '').toLowerCase().split('.').pop();
        if (['jpg', 'jpeg', 'png', 'gif', 'webp', 'svg'].includes(ext)) return 'imagen';
        if (['mp4', 'avi', 'mov', 'mkv', 'webm'].includes(ext)) return 'video';
        if (ext === 'pdf') return 'pdf';
        return 'archivos';
    }

    // ─── EXTRACCIÓN DE TIPOS Y ARCHIVOS DESDE FILAS ───
    extraerTiposDesdeFilas(rows, { editMode = false } = {}) {
        const fileSelector = editMode ? '.input-archivo-file-editar' : '.input-archivo-file';
        const tipos = [];
        rows.forEach(row => {
            const fileInput = row.querySelector(fileSelector);
            const archivo = fileInput && fileInput.files[0];
            tipos.push(archivo ? this.detectarTipoPorExtension(archivo.name) : 'archivos');
        });
        return tipos;
    }

    extraerArchivosDesdeFilas(rows, { editMode = false } = {}) {
        const fileSelector = editMode ? '.input-archivo-file-editar' : '.input-archivo-file';
        const archivos = [];
        rows.forEach(row => {
            const fileInput = row.querySelector(fileSelector);
            if (fileInput && fileInput.files[0]) archivos.push(fileInput.files[0]);
        });
        return archivos;
    }

    // ─── EXTRACCIÓN DE DATOS DE FILAS (para compatibilidad) ───
    extraerAdjuntosDesdeFilas(rows, { editMode = false } = {}) {
        const urls = [];
        const nombres = [];
        const tipos = [];

        rows.forEach(row => {
            const urlSelector = editMode ? '.input-link-archivo-editar' : '.input-link-archivo';
            const nombreSelector = editMode ? '.input-nombre-archivo-editar' : '.input-nombre-archivo';
            const tipoSelector = editMode ? '.input-tipo-archivo-editar' : '.input-tipo-archivo';

            const urlInput = row.querySelector(urlSelector);
            const nombreInput = row.querySelector(nombreSelector);
            const tipoSelect = row.querySelector(tipoSelector);

            if (!urlInput) return;

            const valor = urlInput.value.trim();
            if (!valor) return;

            if (editMode) {
                urls.push(valor);
                nombres.push(nombreInput ? nombreInput.value.trim() : '');
                tipos.push(tipoSelect ? tipoSelect.value : 'archivos');
                return;
            }

            const urlLimpia = this.limpiarIframe(valor);
            if (!urlLimpia) return;

            urls.push(urlLimpia);

            let nombre = nombreInput ? nombreInput.value.trim() : '';
            if (!nombre) {
                const titleMatch = valor.match(/title="([^"]+)"/);
                nombre = titleMatch ? titleMatch[1] : urlLimpia.split('/').pop() || 'Archivo';
            }

            nombres.push(nombre);
            tipos.push(tipoSelect ? tipoSelect.value : 'archivos');
        });

        return { urls, nombres, tipos };
    }

    // ─── INICIALIZACIÓN DE LINKS DINÁMICOS (crear) ───
    initDynamicLinks() {
        if (!this.btnAgregarLink || !this.urlsArchivosContainer) return;

        this.btnAgregarLink.addEventListener('click', () => {
            const newRow = this.crearFilaAdjuntoElement();
            this.urlsArchivosContainer.appendChild(newRow);
        });

        this.urlsArchivosContainer.addEventListener('click', (e) => {
            const btnRemover = e.target.closest('.editar-btn-remover');
            if (!btnRemover) return;

            const row = btnRemover.closest('.input-link-row');
            const rows = this.urlsArchivosContainer.querySelectorAll('.input-link-row');

            if (rows.length > 1) {
                row.remove();
            } else {
                const inputs = row.querySelectorAll('input');
                inputs.forEach(input => input.value = '');
                const dropzone = row.querySelector('.dropzone-mini');
                if (dropzone) {
                    // Limpiar visualmente el dropzone
                    dropzone.classList.remove('has-file');
                    const previewImg = dropzone.querySelector('.dropzone-preview-thumb img');
                    const previewIcon = dropzone.querySelector('.dropzone-preview-thumb:not(img)');
                    const fileName = dropzone.querySelector('.dropzone-preview-name');
                    const fileSize = dropzone.querySelector('.dropzone-preview-size');
                    if (previewImg) { previewImg.src = ''; previewImg.style.display = 'none'; }
                    if (previewIcon) previewIcon.style.display = 'flex';
                    if (fileName) fileName.textContent = '';
                    if (fileSize) fileSize.textContent = '';
                }
            }
        });
    }

    // ─── INICIALIZACIÓN DE LINKS DINÁMICOS (editar) ───
    initEditDynamicLinks() {
        if (!this.btnAgregarLinkEditar || !this.urlsArchivosContainerEditar) return;

        this.btnAgregarLinkEditar.addEventListener('click', () => {
            const newRow = this.crearFilaAdjuntoElement({ editMode: true });
            this.urlsArchivosContainerEditar.appendChild(newRow);
        });

        this.urlsArchivosContainerEditar.addEventListener('click', (e) => {
            const btnRemover = e.target.closest('.editar-btn-remover');
            if (!btnRemover) return;

            const row = btnRemover.closest('.input-link-row');
            const rows = this.urlsArchivosContainerEditar.querySelectorAll('.input-link-row');

            if (rows.length > 1) {
                row.remove();
            } else {
                const inputs = row.querySelectorAll('input');
                inputs.forEach(input => input.value = '');
                const dropzone = row.querySelector('.dropzone-mini');
                if (dropzone) {
                    dropzone.classList.remove('has-file');
                    const previewImg = dropzone.querySelector('.dropzone-preview-thumb img');
                    const previewIcon = dropzone.querySelector('.dropzone-preview-thumb:not(img)');
                    const fileName = dropzone.querySelector('.dropzone-preview-name');
                    const fileSize = dropzone.querySelector('.dropzone-preview-size');
                    if (previewImg) { previewImg.src = ''; previewImg.style.display = 'none'; }
                    if (previewIcon) previewIcon.style.display = 'flex';
                    if (fileName) fileName.textContent = '';
                    if (fileSize) fileSize.textContent = '';
                }
            }
        });
    }

    // ─── BOTONES DE RENDER TOGGLE ───
    initRenderToggleButtons() {
        document.querySelectorAll('.render-toggle-btn-editar').forEach(btn => {
            btn.addEventListener('click', function(e) {
                e.preventDefault();

                const group = this.closest('.render-toggle-group-editar');
                if (!group) return;

                group.querySelectorAll('.render-toggle-btn-editar').forEach(b => b.classList.remove('active'));
                this.classList.add('active');

                const hiddenInput = this.closest('#modal-editar-bloque')
                    ? document.getElementById('editar-render-type')
                    : document.getElementById('id_render_type');

                if (hiddenInput) {
                    hiddenInput.value = this.dataset.render;
                }
            });
        });
    }

    // ─── ELIMINAR ARCHIVO ADJUNTO ───
    eliminarArchivoAdjunto(boton) {
        const url = boton.getAttribute('data-url');
        if (!url) return;

        this.showConfirmDash('¿Eliminar este archivo adjunto?', async () => {
            try {
                const csrfToken = this.getCookie('csrftoken');
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });

                if (!response.ok) throw new Error(`Error HTTP ${response.status}`);
                const data = await response.json();

                if (data.success) {
                    let contenedor = boton.closest('.adjunto-card');
                    if (!contenedor) contenedor = boton.closest('.media-contenedor');
                    if (!contenedor) contenedor = boton.closest('.contenedor-archivo');
                    if (!contenedor && boton.closest('.adjunto-acciones')) {
                        contenedor = boton.closest('.adjunto-acciones')?.parentElement;
                        if (contenedor && contenedor.id && contenedor.id.startsWith('contenido-')) {
                            // lo dejamos
                        } else {
                            contenedor = boton.closest('[style*="margin: 15px 0"]');
                        }
                    }
                    if (!contenedor) contenedor = boton.parentElement?.parentElement;

                    if (contenedor) {
                        contenedor.style.transition = 'opacity 0.3s';
                        contenedor.style.opacity = '0';
                        setTimeout(() => contenedor.remove(), 300);
                    } else {
                        location.reload();
                        return;
                    }
                    this.showSuccessDash('Archivo eliminado correctamente');
                } else {
                    this.showToast(data.error || 'Error al eliminar el archivo', 'error');
                }
            } catch (error) {
                console.error('Error:', error);
                this.showToast('Error de conexión', 'error');
            }
        });
    }

    // ─── MODALES DE CONFIRMACIÓN Y ÉXITO ───
    showConfirmDash(message, callback) {
        const modal = document.getElementById('confirmDashModal');
        const messageEl = document.getElementById('confirmDashMessage');
        messageEl.textContent = message;
        modal.style.display = 'flex';
        this.confirmCallback = callback;
    }

    showSuccessDash(message) {
        const modal = document.getElementById('successDashModal');
        const messageEl = document.getElementById('successDashMessage');
        messageEl.textContent = message;
        modal.style.display = 'flex';
        modal.classList.remove('fade-out');
        setTimeout(() => {
            modal.classList.add('fade-out');
            setTimeout(() => {
                modal.style.display = 'none';
            }, 500);
        }, 1500);
    }

    // ─── VINCULAR BOTÓN GUARDAR DEL MODAL DE EDICIÓN ───
    bindEditModalSave() {
        const btn = document.getElementById('btnGuardarEditarBloque');
        if (btn) {
            btn.removeEventListener('click', this._saveEditHandler);
            this._saveEditHandler = () => this.guardarCambiosBloque();
            btn.addEventListener('click', this._saveEditHandler);
        }
    }

    // ─── FAB (Botón flotante) ───
    initFAB() {
        const fabToggle = document.getElementById('fabToggle');
        const fabContainer = document.querySelector('.fab-container');
        const fabMenu = document.getElementById('fabMenu');

        if (!fabToggle || !fabContainer || !fabMenu) return;

        fabToggle.addEventListener('click', (e) => {
            e.stopPropagation();
            fabContainer.classList.toggle('open');
        });

        fabMenu.querySelectorAll('.fab-menu-item').forEach(item => {
            item.addEventListener('click', () => {
                fabContainer.classList.remove('open');
            });
        });

        document.addEventListener('click', (e) => {
            if (!fabContainer.contains(e.target)) {
                fabContainer.classList.remove('open');
            }
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                fabContainer.classList.remove('open');
            }
        });
    }

    // ─── CACHÉ DE DOM ───
    cacheDOM() {
        this.modalOverlay = document.getElementById('modalContenido');
        this.formBloque = document.getElementById('formBloqueContenido');

        this.tipoContenidoSelect =
            document.getElementById('id_tipo') ||
            this.formBloque?.querySelector('select[name="tipo"]') ||
            this.formBloque?.querySelector('select');

        this.seccionInput =
            document.getElementById('id_seccion') ||
            this.formBloque?.querySelector('[name="seccion"]');

        this.renderTypeGroup = document.getElementById('renderTypeGroup');
        this.renderTypeSelect =
            document.getElementById('id_render_type') ||
            this.formBloque?.querySelector('[name="render_type"]');

        this.urlsArchivosContainerEditar = document.getElementById('urlsArchivosContainerEditar');
        this.btnAgregarLinkEditar = document.getElementById('btnAgregarLinkEditar');

        this.cardsPrincipalesGrid = document.getElementById('cardsPrincipalesGrid');
        this.lateralScroll = document.getElementById('lateralScroll');
        this.grupoUrlsArchivos = document.getElementById('grupoUrlsArchivos');
        this.urlsArchivosContainer = document.getElementById('urlsArchivosContainer');
        this.btnAgregarLink = document.getElementById('btnAgregarLink');
        this.idUrlsArchivos = document.getElementById('id_urls_archivos');
        this.idNombresArchivos = document.getElementById('id_nombres_archivos');
        this.idTiposArchivos = document.getElementById('id_tipos_archivos');
        this.grupoUrlRecurso = document.getElementById('grupoUrlRecurso');
        this.grupoDescripcion = document.getElementById('grupoDescripcion');
        this.grupoOrden = document.getElementById('grupoOrden');
        this.labelUrlRecurso = document.getElementById('labelUrlRecurso');
        this.helpUrlRecurso = document.getElementById('helpUrlRecurso');

        // 🔹 Nuevas referencias para alternar dropzone vs input de texto
        this.dropzoneBanner = document.getElementById('dropzoneBanner');
        this.urlRecursoInput = document.getElementById('id_url_recurso');

        if (this.seccionInput) this.seccionInput.classList.add('editar-input');
        if (this.tipoContenidoSelect) this.tipoContenidoSelect.classList.add('editar-input');
        const tituloInput = document.getElementById('id_titulo');
        if (tituloInput) tituloInput.classList.add('editar-input');
        const descripcionInput = document.getElementById('id_descripcion');
        if (descripcionInput) descripcionInput.classList.add('editar-textarea');
        const urlRecursoInput = document.getElementById('id_url_recurso');
        if (urlRecursoInput) urlRecursoInput.classList.add('editar-input');
        const renderTypeInput = document.getElementById('id_render_type');
        if (renderTypeInput) renderTypeInput.classList.add('editar-input');

        const btnGuardar = document.getElementById('btnGuardarContenido');
        if (btnGuardar) {
            btnGuardar.addEventListener('click', (e) => {
                e.preventDefault();
                this.handleSubmit(e);
            });
        }
    }

    // ─── EVENTOS ───
    bindEvents() {
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') this.cerrarModal();
        });

        this.modalOverlay?.addEventListener('click', (e) => {
            if (e.target === this.modalOverlay) this.cerrarModal();
        });

        this.tipoContenidoSelect?.addEventListener('change', () => {
            this.actualizarCamposPorTipo();
        });

        this.seccionInput?.addEventListener('change', () => {
            this.handleSeccionChange();
        });

        this.formBloque?.addEventListener('submit', (e) => this.handleSubmit(e));
    }

    // ─── ABRIR MODAL ───
    abrirModal(seccion) {
        this.currentSection = seccion;

        if (!this.tipoContenidoSelect) {
            this.tipoContenidoSelect = document.getElementById('id_tipo')
                || document.querySelector('#formBloqueContenido select[name="tipo"]')
                || document.querySelector('#formBloqueContenido select');
        }
        if (!this.seccionInput) {
            this.seccionInput = document.getElementById('id_seccion')
                || document.querySelector('#formBloqueContenido input[name="seccion"]')
                || document.querySelector('#formBloqueContenido [name="seccion"]');
        }

        if (this.seccionInput) this.seccionInput.value = seccion;

        const seccionGroup = this.seccionInput?.closest('.form-group');
        this.setDisplay(seccionGroup, false);

        if (seccion === 'principal') {
            this.habilitarTipos(['banner']);
            if (this.tipoContenidoSelect) this.tipoContenidoSelect.value = 'banner';
            const tipoGroup = this.tipoContenidoSelect?.closest('.form-group');
            this.setDisplay(tipoGroup, false);
        } else if (seccion === 'lateral') {
            this.habilitarTipos(['informativa', 'archivos', 'enlace']);
            if (this.tipoContenidoSelect) this.tipoContenidoSelect.value = '';
            const tipoGroup = this.tipoContenidoSelect?.closest('.form-group');
            this.setDisplay(tipoGroup, true);
        }

        if (this.modalOverlay) this.modalOverlay.style.display = 'flex';
        this.limpiarInputsLinks();
        this.actualizarCamposPorTipo();
        // Inicializar dropzones después de mostrar el modal
        requestAnimationFrame(() => {
            this.inicializarDropzones(this.modalOverlay);
        });
    }

    cerrarModal() {
        this.modalOverlay.style.display = 'none';
        this.currentSection = null;
        this.formBloque.reset();
        this.limpiarInputsLinks();

        const seccionGroup = this.seccionInput?.closest('.form-group');
        this.setDisplay(seccionGroup, true);
        const tipoGroup = this.tipoContenidoSelect?.closest('.form-group');
        this.setDisplay(tipoGroup, true);
    }

    handleSeccionChange() {
        const seccion = this.seccionInput?.value || '';
        this.setDisplay(this.renderTypeGroup, seccion === 'principal');
        this.handleTipoChange();
        this.actualizarCamposPorTipo();
    }

    handleTipoChange() {
        const seccion = this.seccionInput?.value || '';
        if (seccion === 'principal') {
            this.habilitarTipos(['banner']);
        } else if (seccion === 'lateral') {
            this.habilitarTipos(['informativa', 'archivos', 'enlace']);
        }
    }

    habilitarTipos(tiposPermitidos) {
        if (!this.tipoContenidoSelect) return;

        const todasLasOpciones = [
            { value: 'banner', text: 'Banner Grande' },
            { value: 'informativa', text: 'Card Informativa' },
            { value: 'archivos', text: 'Archivos' },
            { value: 'enlace', text: 'Enlace Web' },
        ];

        const valorActual = this.tipoContenidoSelect.value;
        this.tipoContenidoSelect.innerHTML = '<option value="">Seleccione tipo...</option>';

        todasLasOpciones.forEach(opt => {
            if (tiposPermitidos.includes(opt.value)) {
                const option = document.createElement('option');
                option.value = opt.value;
                option.textContent = opt.text;
                this.tipoContenidoSelect.appendChild(option);
            }
        });

        if (valorActual && tiposPermitidos.includes(valorActual)) {
            this.tipoContenidoSelect.value = valorActual;
        }
    }

    // ─── ACTUALIZAR CAMPOS POR TIPO (MODIFICADO) ───
    actualizarCamposPorTipo() {
        const tipo = this.tipoContenidoSelect?.value || '';
        const seccion = this.seccionInput?.value || '';

        // Resetear visibilidad de todos los grupos
        this.setDisplay(this.grupoDescripcion, false);
        this.setDisplay(this.grupoUrlRecurso, false);
        this.setDisplay(this.grupoUrlsArchivos, false);
        this.setDisplay(this.renderTypeGroup, false);
        this.setDisplay(this.grupoOrden, false);
        this.setDisplay(this.btnAgregarLink, false);

        // 🔹 Ocultar tanto dropzone como input de texto por defecto (para que cada tipo decida)
        this.setDisplay(this.dropzoneBanner, false);
        this.setDisplay(this.urlRecursoInput, false);

        if (seccion === 'principal' && tipo === 'banner') {
            this.setDisplay(this.grupoDescripcion, true);
            this.setDisplay(this.grupoUrlRecurso, true);
            this.setDisplay(this.renderTypeGroup, true);
            if (this.labelUrlRecurso) this.labelUrlRecurso.textContent = 'Imagen o Archivo:';
            if (this.helpUrlRecurso) this.helpUrlRecurso.innerHTML = '<i class="fas fa-info-circle"></i> Selecciona la imagen desde tu equipo.';

            // 🔹 Mostrar dropzone, ocultar input de texto
            this.setDisplay(this.dropzoneBanner, true, 'flex');
            this.setDisplay(this.urlRecursoInput, false);

            requestAnimationFrame(() => {
                const dz = document.getElementById('dropzoneBanner');
                if (dz) this.setupDropzone(dz);
            });
        } else if (seccion === 'lateral') {
            if (tipo === 'informativa') {
                this.setDisplay(this.grupoDescripcion, true);
            } else if (tipo === 'archivos') {
                this.setDisplay(this.grupoDescripcion, true);
                this.setDisplay(this.grupoUrlsArchivos, true);
                this.setDisplay(this.btnAgregarLink, true, 'inline-flex');
                requestAnimationFrame(() => {
                    this.inicializarDropzones(this.grupoUrlsArchivos);
                });
            } else if (tipo === 'enlace') {
                this.setDisplay(this.grupoDescripcion, true);
                this.setDisplay(this.grupoUrlRecurso, true);
                if (this.labelUrlRecurso) this.labelUrlRecurso.textContent = 'URL del Enlace Web:';
                if (this.helpUrlRecurso) this.helpUrlRecurso.innerHTML = '<i class="fas fa-info-circle"></i> El enlace se abrirá en una pestaña nueva.';

                // 🔹 Ocultar dropzone, mostrar input de texto
                this.setDisplay(this.dropzoneBanner, false);
                this.setDisplay(this.urlRecursoInput, true, 'block');
            }
        }
    }

    formatearTexto(texto) {
        if (!texto) return '';
        let html = texto.replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;');
        html = html.replace(/\n/g, '<br>');
        html = html.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');
        html = html.replace(/__(.+?)__/g, '<strong>$1</strong>');
        html = html.replace(/\*(.+?)\*/g, '<em>$1</em>');
        html = html.replace(/_(.+?)_/g, '<em>$1</em>');
        html = html.replace(/`(.+?)`/g, '<code>$1</code>');
        html = html.replace(/\[(.+?)\]\((.+?)\)/g, '<a href="$2" target="_blank">$1</a>');
        html = html.replace(/^### (.+)$/gm, '<h4>$1</h4>');
        html = html.replace(/^## (.+)$/gm, '<h4>$1</h4>');
        html = html.replace(/^[\*\-] (.+)$/gm, '<li>$1</li>');
        html = html.replace(/(<li>.*?<\/li>(?:<br>)?)+/g, (match) => {
            const clean = match.replace(/<br>/g, '');
            return '<ul>' + clean + '</ul>';
        });
        html = html.replace(/<br><ul>/g, '<ul>');
        html = html.replace(/<\/ul><br>/g, '</ul>');
        return html;
    }

    limpiarIframe(url) {
        if (!url) return '';
        if (url.startsWith('http://') || url.startsWith('https://')) return url.trim();
        const match = url.match(/src="([^"]+)"/);
        if (match) return match[1].trim();
        if (url.startsWith('www.')) return 'https://' + url.trim();
        return url.trim();
    }

    limpiarInputsLinks() {
        if (this.urlsArchivosContainer) {
            this.urlsArchivosContainer.innerHTML = '';
            this.urlsArchivosContainer.appendChild(this.crearFilaAdjuntoElement());
        }
        if (this.idUrlsArchivos) this.idUrlsArchivos.value = '';
        if (this.idNombresArchivos) this.idNombresArchivos.value = '';
        if (this.idTiposArchivos) this.idTiposArchivos.value = '';
    }

    // ─── HANDLE SUBMIT (CREAR CONTENIDO) ───
    async handleSubmit(e) {
        e.preventDefault();

        const seccion = this.seccionInput?.value || '';
        const tipo = this.tipoContenidoSelect?.value || '';

        if (!tipo) {
            this.showToast('Seleccione un tipo de contenido', 'error');
            return;
        }

        const rows = document.querySelectorAll('#urlsArchivosContainer .input-link-row');
        const tipos = this.extraerTiposDesdeFilas(rows);
        const archivos = this.extraerArchivosDesdeFilas(rows);

        const payload = {
            seccion: seccion,
            tipo: tipo,
            titulo: this.formBloque.querySelector('[name="titulo"]')?.value || '',
            descripcion: this.formBloque.querySelector('[name="descripcion"]')?.value || '',
            orden: 0,
            render_type: this.renderTypeSelect?.value || 'imagen_debajo',
            tipos_archivos_subidos: tipos.join('\n')
        };

        if (tipo === 'enlace') {
            const urlInput = document.getElementById('id_url_recurso');
            payload.url_recurso = this.limpiarIframe(urlInput?.value || '');
        }

        const formData = new FormData();
        formData.append('payload', JSON.stringify(payload));

        const bannerFile = document.getElementById('id_banner_archivo')?.files[0];
        if (bannerFile) formData.append('banner_archivo', bannerFile);

        archivos.forEach(file => formData.append('archivos_adjuntos', file));

        const submitBtn = document.getElementById('btnGuardarContenido');
        const originalText = submitBtn.innerHTML;
        submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Subiendo...';
        submitBtn.disabled = true;

        try {
            const cursoId = this.getCursoId();
            const url = `/contenido/api/curso/${cursoId}/bloque/guardar/`;
            const csrfToken = this.getCookie('csrftoken');

            const response = await fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': csrfToken,
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: formData
            });

            if (!response.ok) throw new Error(`Error HTTP ${response.status}`);
            const data = await response.json();

            if (data.success) {
                this.showSuccessDash('Contenido agregado exitosamente');
                this.agregarNuevaCard(data.bloque);
                this.cerrarModal();
            } else {
                this.showToast(data.error || 'Error al guardar', 'error');
            }
        } catch (error) {
            console.error('Error:', error);
            this.showToast('Error de conexión con el servidor', 'error');
        } finally {
            submitBtn.innerHTML = originalText;
            submitBtn.disabled = false;
        }
    }

    // ─── GUARDAR CAMBIOS (EDITAR BLOQUE) ───
    guardarCambiosBloque() {
        if (!bloqueEnEdicion) return;

        const rows = document.querySelectorAll('#urlsArchivosContainerEditar .input-link-row');
        const tipos = this.extraerTiposDesdeFilas(rows, { editMode: true });
        const archivos = this.extraerArchivosDesdeFilas(rows, { editMode: true });

        const payload = {
            titulo: document.getElementById('editar-titulo').value,
            descripcion: document.getElementById('editar-descripcion').value,
            render_type: document.getElementById('editar-render-type').value,
            tipos_archivos_subidos: tipos.join('\n')
        };

        const tipoBloque = document.getElementById('editar-tipo').value;
        if (tipoBloque === 'enlace') {
            payload.url_recurso = document.getElementById('editar-url-recurso').value;
        }

        const formData = new FormData();
        formData.append('payload', JSON.stringify(payload));

        const bannerFile = document.getElementById('editar_banner_archivo')?.files[0];
        if (bannerFile) formData.append('banner_archivo', bannerFile);

        archivos.forEach(file => formData.append('archivos_adjuntos', file));

        const btn = document.getElementById('btnGuardarEditarBloque');
        if (!btn) return;
        const originalContent = btn.innerHTML;
        btn.disabled = true;
        btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Subiendo...';

        fetch(`/contenido/api/bloque/${bloqueEnEdicion}/editar/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': this.getCookie('csrftoken'),
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                cerrarModalEditarBloque();
                this.showSuccessDash('Cambios guardados correctamente');
                setTimeout(() => location.reload(), 800);
            } else {
                alert('Error: ' + (data.error || 'No se pudieron guardar los cambios'));
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al guardar: ' + error);
        })
        .finally(() => {
            btn.disabled = false;
            btn.innerHTML = originalContent;
        });
    }

    // ─── GENERAR HTML DE CARD ───
    generarCardHTML(bloque) {
        if (bloque.seccion === 'principal') {
            return this.generarCardPrincipalHTML(bloque);
        } else {
            return this.generarCardLateralHTML(bloque);
        }
    }

    agregarNuevaCard(bloque) {
        const cardHTML = this.generarCardHTML(bloque);
        if (bloque.seccion === 'principal') {
            if (this.cardsPrincipalesGrid) {
                this.cardsPrincipalesGrid.insertAdjacentHTML('beforeend', cardHTML);
            }
        } else if (bloque.seccion === 'lateral') {
            const columnaDerecha = document.querySelector('.columna-derecha');
            if (columnaDerecha) {
                columnaDerecha.insertAdjacentHTML('beforeend', cardHTML);
            }
        }

        this.actualizarContadorLateral();

        setTimeout(() => {
            const nuevaCard = document.getElementById(`bloque-${bloque.id}`);
            if (nuevaCard) {
                nuevaCard.scrollIntoView({ behavior: 'smooth', block: 'center' });
                nuevaCard.style.boxShadow = '0 0 0 3px #3b82f6, 0 8px 25px rgba(59, 130, 246, 0.2)';
                nuevaCard.style.borderColor = '#3b82f6';
                setTimeout(() => {
                    nuevaCard.style.boxShadow = '';
                    nuevaCard.style.borderColor = '';
                }, 2000);
            }
        }, 100);
    }

    actualizarContadorLateral() {
        const cards = document.querySelectorAll('.columna-derecha .card-lateral-item');
        const contador = document.querySelector('.lateral-count-independiente');
        if (contador) {
            contador.textContent = `${cards.length} items`;
        }
    }

    generarCardPrincipalHTML(bloque) {
        const esFondo = bloque.render_type === 'imagen_fondo' && bloque.url_recurso;

        let cardClass = '';
        let fondoStyle = '';
        let iframeFondo = '';

        if (esFondo) {
            const url = bloque.url_recurso;
            if (url.includes('sharepoint.com') || url.includes('embed.aspx')) {
                cardClass = 'card-fondo-sharepoint';
                iframeFondo = `<iframe class="sharepoint-bg-iframe" src="${url}" frameborder="0" scrolling="no" allowfullscreen></iframe>`;
            } else {
                cardClass = 'card-fondo-imagen';
                fondoStyle = `background-image: url('${url}'); background-size: cover; background-position: center;`;
            }
        }

        const descripcionHTML = bloque.descripcion ? this.formatearTexto(bloque.descripcion) : '';

        let recursoHTML = '';
        if (!esFondo && bloque.url_recurso && bloque.tipo === 'banner') {
            const url = bloque.url_recurso;
            if (url.includes('sharepoint.com') || url.includes('embed.aspx')) {
                recursoHTML = `<div class="card-adicional-imagen"><iframe src="${url}" width="100%" height="400" frameborder="0" scrolling="no" allowfullscreen></iframe></div>`;
            } else if (url.includes('youtube.com') || url.includes('youtu.be') || url.includes('vimeo.com')) {
                const urlEmbed = this.transformURL(url);
                recursoHTML = `<div class="card-adicional-imagen"><iframe src="${urlEmbed}" width="100%" height="315" frameborder="0" allowfullscreen></iframe></div>`;
            } else {
                recursoHTML = `<div class="card-adicional-imagen"><img src="${url}" alt="${bloque.titulo || 'Recurso'}" onerror="this.onerror=null; this.parentElement.innerHTML='<div style=\'background:#f1f5f9;padding:40px;text-align:center;border-radius:8px;color:#94a3b8\'><i class=\'fas fa-image\' style=\'font-size:48px;margin-bottom:10px;display:block\'></i><p>El recurso no está disponible</p></div>';"></div>`;
            }
        }

        if (esFondo) {
            return `
                <div class="card-adicional-item ${cardClass}" id="bloque-${bloque.id}" data-tipo="${bloque.tipo}" style="animation: fadeInUp 0.4s ease; ${fondoStyle}">
                    <div class="card-buttons-group">
                        <button class="btn-editar-card" onclick="editarBloque(${bloque.id})" title="Editar"><i class="fas fa-edit"></i></button>
                        <button class="btn-eliminar-card" onclick="dashboard.eliminarBloque(${bloque.id})" title="Eliminar"><i class="fas fa-times"></i></button>
                    </div>
                    ${iframeFondo}
                    <div class="card-fondo-overlay"></div>
                    <div class="card-contenido-superpuesto">
                        ${bloque.titulo ? `<h3 class="card-adicional-titulo">${bloque.titulo}</h3>` : ''}
                        ${descripcionHTML ? `<div class="card-adicional-descripcion">${descripcionHTML}</div>` : ''}
                    </div>
                    <div class="card-adicional-footer"><span><i class="far fa-clock"></i> ${bloque.fecha_creacion || ''}</span></div>
                </div>
            `;
        }

        return `
            <div class="card-adicional-item" id="bloque-${bloque.id}" data-tipo="${bloque.tipo}" style="animation: fadeInUp 0.4s ease;">
                <div class="card-buttons-group">
                    <button class="btn-editar-card" onclick="editarBloque(${bloque.id})" title="Editar"><i class="fas fa-edit"></i></button>
                    <button class="btn-eliminar-card" onclick="dashboard.eliminarBloque(${bloque.id})" title="Eliminar"><i class="fas fa-times"></i></button>
                </div>
                ${bloque.titulo ? `<h3 class="card-adicional-titulo">${bloque.titulo}</h3>` : ''}
                ${descripcionHTML ? `<div class="card-adicional-descripcion">${descripcionHTML}</div>` : ''}
                ${recursoHTML}
                <div class="card-adicional-footer"><span><i class="far fa-clock"></i> ${bloque.fecha_creacion || ''}</span></div>
            </div>
        `;
    }

    generarCardLateralHTML(bloque) {
        const iconos = {
            'informativa': { class: 'icon-mini', icon: 'fa-info-circle', label: 'Informativa' },
            'archivos': { class: 'icon-mini', icon: 'fa-folder-open', label: 'Archivos' },
            'enlace': { class: 'icon-enlace', icon: 'fa-link', label: 'Enlace Web' }
        };

        const tipoInfo = iconos[bloque.tipo] || iconos['informativa'];
        const descripcionHTML = bloque.descripcion ? this.formatearTexto(bloque.descripcion) : '';

        let contenidoEspecificoHTML = '';

        if (bloque.tipo === 'archivos' && bloque.archivos && bloque.archivos.length > 0) {
            const archivosMedia = bloque.archivos.filter(a => ['imagen', 'video'].includes(a.tipo_archivo));
            const archivosNormal = bloque.archivos.filter(a => !['imagen', 'video'].includes(a.tipo_archivo));

            const mediaHTML = archivosMedia.map(archivo => {
                const urlArchivo = archivo.url_archivo || '';
                const esSharepoint = archivo.es_sharepoint || urlArchivo.includes('sharepoint.com') || urlArchivo.includes('embed.aspx');
                const tipoDisplay = archivo.tipo_display || archivo.tipo_archivo || '';
                const archivoId = archivo.id;

                let embedHTML = '';
                if (archivo.tipo_archivo === 'imagen') {
                    if (esSharepoint) {
                        embedHTML = `<div style="position:relative;padding-bottom:75%;height:0;overflow:hidden;border-radius:8px;"><iframe src="${urlArchivo}" style="position:absolute;top:0;left:0;width:100%;height:100%;border:none;border-radius:8px;" frameborder="0" scrolling="no" allowfullscreen></iframe></div>`;
                    } else {
                        embedHTML = `<a href="${urlArchivo}" target="_blank" style="display:block;border-radius:8px;overflow:hidden;background:#f1f5f9;"><img src="${urlArchivo}" alt="${archivo.nombre || ''}" style="width:100%;height:200px;object-fit:cover;display:block;" onerror="this.parentElement.innerHTML='<div style=\'padding:40px;text-align:center;background:#f1f5f9;border-radius:8px;color:#94a3b8\'><i class=\'fas fa-image\' style=\'font-size:32px;margin-bottom:10px;display:block\'></i><p style=\'font-size:12px\'>Imagen no disponible</p></div>';"></a>`;
                    }
                } else if (archivo.tipo_archivo === 'video') {
                    embedHTML = `<div style="position:relative;padding-bottom:56.25%;height:0;overflow:hidden;border-radius:8px;"><iframe src="${urlArchivo}" style="position:absolute;top:0;left:0;width:100%;height:100%;border:none;border-radius:8px;" allowfullscreen></iframe></div>`;
                }

                const accionesHTML = `
                    <div class="adjunto-acciones" style="margin-top: 8px;">
                        <a href="${urlArchivo}" target="_blank" rel="noopener noreferrer" class="adjunto-btn" title="Abrir">
                            <i class="fas fa-external-link-alt"></i> Abrir
                        </a>
                        <button class="adjunto-btn adjunto-btn-eliminar" 
                                data-url="/contenido/api/contenido/${archivoId}/eliminar/"
                                onclick="dashboard.eliminarArchivoAdjunto(this)" 
                                title="Eliminar archivo">
                            <i class="fas fa-trash-alt"></i> Eliminar
                        </button>
                    </div>
                `;

                return `
                    <div style="margin:15px 0;" class="media-contenedor">
                        ${embedHTML}
                        <div style="margin-top:8px;font-size:12px;color:#94a3b8;">
                            <i class="fas ${archivo.tipo_archivo === 'imagen' ? 'fa-image' : 'fa-video'}"></i> ${tipoDisplay}
                        </div>
                        ${accionesHTML}
                    </div>
                `;
            }).join('');

            const iconosPorTipo = { 'pdf': 'fa-file-pdf', 'word': 'fa-file-word', 'excel': 'fa-file-excel', 'powerpoint': 'fa-file-powerpoint', 'sharepoint': 'fa-cloud', 'url': 'fa-link', 'otro': 'fa-file' };
            const archivosNormalHTML = archivosNormal.map(archivo => {
                const urlArchivo = archivo.url_archivo || '';
                const nombreArchivo = archivo.nombre || urlArchivo.split('/').pop() || 'Archivo';
                const displayName = nombreArchivo.length > 35 ? nombreArchivo.substring(0, 35) + '...' : nombreArchivo;
                const iconoArchivo = iconosPorTipo[archivo.tipo_archivo] || 'fa-file';
                const esSharePoint = archivo.es_sharepoint || archivo.tipo_archivo === 'sharepoint' || urlArchivo.includes('sharepoint.com');
                const tipoDisplay = archivo.tipo_display || 'Archivo';
                const archivoId = archivo.id;

                let urlVisualizacion = urlArchivo;
                let urlDescarga = '';

                if (archivo.tipo_archivo === 'pdf') {
                    urlVisualizacion = urlArchivo;
                    const uniqueIdMatchPdf = urlArchivo.match(/UniqueId=([a-f0-9\-]{36})/i);
                    if (uniqueIdMatchPdf) {
                        const baseMatchPdf = urlArchivo.match(/(https?:\/\/[^\/]+\/[^\/]+\/[^\/]+)/);
                        const baseSPPdf = baseMatchPdf ? baseMatchPdf[1] : '';
                        if (baseSPPdf) {
                            urlDescarga = `${baseSPPdf}/_layouts/15/download.aspx?UniqueId=${uniqueIdMatchPdf[1]}`;
                        }
                    }
                } else if (esSharePoint) {
                    const uniqueIdMatch = urlArchivo.match(/UniqueId=([a-f0-9\-]{36})/i) || urlArchivo.match(/sourcedoc=\{([a-f0-9\-]{36})\}/i);
                    if (uniqueIdMatch) {
                        const uniqueId = uniqueIdMatch[1];
                        const baseMatch = urlArchivo.match(/(https?:\/\/[^\/]+\/[^\/]+\/[^\/]+)/);
                        const baseSP = baseMatch ? baseMatch[1] : '';
                        if (baseSP && uniqueId) {
                            urlVisualizacion = `${baseSP}/_layouts/15/Doc.aspx?sourcedoc=%7B${uniqueId}%7D&action=default`;
                            urlDescarga = `${baseSP}/_layouts/15/download.aspx?UniqueId=${uniqueId}`;
                        }
                    }
                }

                if (esSharePoint) {
                    return `
                        <div class="adjunto-card">
                            <div class="adjunto-icon"><i class="fas ${iconoArchivo}"></i></div>
                            <div class="adjunto-info">
                                <div class="adjunto-nombre" title="${nombreArchivo}">${displayName}</div>
                                <div class="adjunto-tipo">${tipoDisplay}</div>
                            </div>
                            <div class="adjunto-acciones">
                                <a href="${urlVisualizacion}" target="_blank" rel="noopener noreferrer" class="adjunto-btn" title="Abrir archivo"><i class="fas fa-external-link-alt"></i> Abrir</a>
                                <a href="${urlDescarga}" class="adjunto-btn" title="Descargar archivo" download><i class="fas fa-download"></i> Descargar</a>
                                <button class="adjunto-btn adjunto-btn-eliminar" data-url="/contenido/api/contenido/${archivoId}/eliminar/" onclick="dashboard.eliminarArchivoAdjunto(this)" title="Eliminar archivo">
                                    <i class="fas fa-trash-alt"></i>
                                </button>
                            </div>
                        </div>`;
                } else {
                    return `
                        <div class="adjunto-card">
                            <div class="adjunto-icon"><i class="fas ${iconoArchivo}"></i></div>
                            <div class="adjunto-info">
                                <div class="adjunto-nombre" title="${nombreArchivo}">${displayName}</div>
                                <div class="adjunto-tipo">${tipoDisplay}</div>
                            </div>
                            <div class="adjunto-acciones">
                                <a href="${urlVisualizacion}" target="_blank" rel="noopener noreferrer" class="adjunto-btn" title="Abrir archivo"><i class="fas fa-external-link-alt"></i></a>
                                <button class="adjunto-btn adjunto-btn-eliminar" data-url="/contenido/api/contenido/${archivoId}/eliminar/" onclick="dashboard.eliminarArchivoAdjunto(this)" title="Eliminar archivo">
                                    <i class="fas fa-trash-alt"></i>
                                </button>
                            </div>
                        </div>`;
                }
            }).join('');

            const listaNormalHTML = archivosNormal.length > 0 ? `
                <div class="archivos-adjuntos-lista">
                    <div class="archivos-adjuntos-titulo"><i class="fas fa-paperclip"></i> Archivos</div>
                    ${archivosNormalHTML}
                </div>` : '';

            contenidoEspecificoHTML = mediaHTML + listaNormalHTML;
        } else if (bloque.tipo === 'enlace' && bloque.url_recurso) {
            contenidoEspecificoHTML = `
                <a href="${bloque.url_recurso}" target="_blank" rel="noopener noreferrer" class="btn-mini-action" style="background: #3b82f6;">
                    <i class="fas fa-external-link-alt"></i> Visitar Enlace
                </a>`;
        }

        const archivosUrls = (bloque.archivos || []).map(a => a.url_archivo || '').join('|');
        const archivosNombres = (bloque.archivos || []).map(a => a.nombre || '').join('|');
        const archivosTipos = (bloque.archivos || []).map(a => a.tipo_archivo || '').join('|');

        const dataAttrs = `
            data-tipo="${bloque.tipo}"
            data-url-recurso="${bloque.url_recurso || ''}"
            data-archivos-urls="${archivosUrls}"
            data-archivos-nombres="${archivosNombres}"
            data-archivos-tipos="${archivosTipos}"
            data-render-type="${bloque.render_type || ''}"
        `;

        return `
            <div class="card-lateral-item" id="bloque-${bloque.id}" ${dataAttrs} style="animation: fadeInUp 0.4s ease;">
                <div class="mini-card-buttons">
                    <button class="btn-editar-mini" onclick="editarBloque(${bloque.id})" title="Editar"><i class="fas fa-edit"></i></button>
                    <button class="btn-eliminar-mini" onclick="dashboard.eliminarBloque(${bloque.id})" title="Eliminar"><i class="fas fa-times"></i></button>
                </div>
                <div class="card-lateral-header">
                    <div class="mini-card-icon ${tipoInfo.class}">
                        <i class="fas ${tipoInfo.icon}"></i>
                    </div>
                    <div class="card-lateral-title-section">
                        <h4 class="mini-card-title">${bloque.titulo || 'Sin título'}</h4>
                        <span class="card-tipo-label">${tipoInfo.label}</span>
                    </div>
                </div>
                ${descripcionHTML ? `<div class="mini-card-description">${descripcionHTML}</div>` : ''}
                ${contenidoEspecificoHTML}
                <div class="mini-card-meta">
                    <span><i class="far fa-calendar-alt"></i> ${bloque.fecha_creacion || ''}</span>
                </div>
            </div>
        `;
    }

    // ─── ELIMINAR BLOQUE ───
    async eliminarBloque(idBloque) {
        this.showConfirmDash('¿Eliminar este bloque de contenido?', async () => {
            try {
                const csrfToken = this.getCookie('csrftoken');
                const url = `/contenido/api/bloque/${idBloque}/eliminar/`;
                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-CSRFToken': csrfToken,
                        'X-Requested-With': 'XMLHttpRequest'
                    }
                });
                if (!response.ok) throw new Error(`Error HTTP ${response.status}`);
                const data = await response.json();

                if (data.success) {
                    const bloqueElement = document.getElementById(`bloque-${idBloque}`);
                    if (bloqueElement) {
                        bloqueElement.style.transition = 'all 0.3s ease';
                        bloqueElement.style.opacity = '0';
                        bloqueElement.style.transform = 'scale(0.9)';
                        setTimeout(() => {
                            bloqueElement.remove();
                            this.actualizarContadorLateral();
                        }, 300);
                    }
                    this.showSuccessDash('Bloque eliminado exitosamente');
                }
            } catch (error) {
                console.error('Error:', error);
                this.showToast('Error de conexión', 'error');
            }
        });
    }

    transformURL(url) {
        if (!url) return '';
        if (url.includes('youtube.com/embed/') || url.includes('youtube-nocookie.com/embed/')) return url;
        if (url.includes('youtube.com/watch?v=')) {
            const urlObj = new URL(url);
            const videoId = urlObj.searchParams.get('v');
            if (videoId) return `https://www.youtube.com/embed/${videoId}`;
            return url.replace('watch?v=', 'embed/');
        }
        if (url.includes('youtu.be/')) return url.replace('youtu.be/', 'youtube.com/embed/');
        return url;
    }

    getCursoId() {
        const match = window.location.pathname.match(/curso\/([^/]+)/);
        return match ? match[1] : '';
    }

    getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
        return null;
    }

    showToast(message, type = 'info') {
        const existingToast = document.querySelector('.toast-notification');
        if (existingToast) existingToast.remove();

        const icons = { 'success': 'fa-check-circle', 'error': 'fa-exclamation-circle', 'info': 'fa-info-circle' };
        const toast = document.createElement('div');
        toast.className = `toast-notification toast-${type}`;
        toast.innerHTML = `<i class="fas ${icons[type]}"></i> ${message}`;
        document.body.appendChild(toast);

        setTimeout(() => toast.classList.add('toast-show'), 10);
        setTimeout(() => {
            toast.classList.remove('toast-show');
            setTimeout(() => toast.remove(), 300);
        }, 3000);
    }
}

// ============================================================
// INICIALIZACIÓN Y VARIABLES GLOBALES
// ============================================================

let dashboard;
let bloqueEnEdicion = null;

document.addEventListener('DOMContentLoaded', () => {
    dashboard = new ContenidoDashboard();
    window.dashboard = dashboard;
});

// Funciones globales para los botones en el HTML
function abrirModalContenido(seccion) {
    if (dashboard) dashboard.abrirModal(seccion);
}

function editarBloque(bloqueId) {
    const bloqueElement = document.getElementById(`bloque-${bloqueId}`);
    if (!bloqueElement) return;

    bloqueEnEdicion = bloqueId;

    const titulo = bloqueElement.querySelector('.mini-card-title, .card-adicional-titulo')?.textContent || '';
    const descripcion = bloqueElement.querySelector('.mini-card-description, .card-adicional-descripcion')?.textContent || '';
    const tipo = bloqueElement.dataset.tipo || '';
    const seccion = bloqueElement.closest('.columna-derecha') ? 'lateral' : 'principal';

    document.getElementById('editar-id').value = bloqueId;
    document.getElementById('editar-seccion').value = seccion;
    document.getElementById('editar-tipo').value = tipo;
    document.getElementById('editar-titulo').value = titulo;
    document.getElementById('editar-descripcion').value = descripcion;

    const urlRecurso = bloqueElement.dataset.urlRecurso || '';
    document.getElementById('editar-url-recurso').value = urlRecurso;

    const urlsArchivos = (bloqueElement.dataset.archivosUrls || '').split('|').filter(Boolean);
    const nombresArchivos = (bloqueElement.dataset.archivosNombres || '').split('|').filter(Boolean);
    const tiposArchivos = (bloqueElement.dataset.archivosTipos || '').split('|').filter(Boolean);

    const container = document.getElementById('urlsArchivosContainerEditar');
    container.innerHTML = '';

    if (urlsArchivos.length > 0) {
        for (let i = 0; i < urlsArchivos.length; i++) {
            container.appendChild(dashboard.crearFilaAdjuntoElement({
                editMode: true,
                tipo: tiposArchivos[i] || 'archivos',
                url: urlsArchivos[i] || '',
                nombre: nombresArchivos[i] || ''
            }));
        }
    } else {
        container.appendChild(dashboard.crearFilaAdjuntoElement({ editMode: true }));
    }

    const renderType = bloqueElement.dataset.renderType || 'imagen_debajo';
    document.getElementById('editar-render-type').value = renderType;

    const grupos = {
        descripcion: document.getElementById('grupoDescripcionEditar'),
        urlRecurso: document.getElementById('grupoUrlRecursoEditar'),
        archivos: document.getElementById('grupoUrlsArchivosEditar'),
        render: document.getElementById('grupoRenderTypeEditar')
    };

    const dropzoneBannerEditar = document.getElementById('dropzoneBannerEditar');
    const inputUrlEditar = document.getElementById('editar-url-recurso');
    const helpUrlRecursoEditar = document.getElementById('helpUrlRecursoEditar');
    const labelUrlRecursoEditar = document.getElementById('labelUrlRecursoEditar');
    const avisoImagenActual = document.getElementById('editar-imagen-actual-aviso');

    Object.values(grupos).forEach(g => g.style.display = 'none');

    // Estado base: ocultar controles específicos y mostrarlos según el tipo.
    if (dropzoneBannerEditar) dropzoneBannerEditar.style.display = 'none';
    if (inputUrlEditar) inputUrlEditar.style.display = 'none';
    if (helpUrlRecursoEditar) helpUrlRecursoEditar.style.display = 'none';
    if (avisoImagenActual) avisoImagenActual.style.display = 'none';

    if (seccion === 'principal' && tipo === 'banner') {
        grupos.descripcion.style.display = 'block';
        grupos.urlRecurso.style.display = 'block';
        grupos.render.style.display = 'block';

        if (labelUrlRecursoEditar) labelUrlRecursoEditar.textContent = 'Imagen o Archivo:';
        if (dropzoneBannerEditar) dropzoneBannerEditar.style.display = 'block';
        if (helpUrlRecursoEditar) helpUrlRecursoEditar.style.display = 'block';
        if (avisoImagenActual && urlRecurso) avisoImagenActual.style.display = 'flex';

        // Inicializar dropzone del banner en edición
        requestAnimationFrame(() => {
            const dz = document.getElementById('dropzoneBannerEditar');
            if (dz) dashboard.setupDropzone(dz);
        });
    } else if (seccion === 'lateral') {
        if (tipo === 'informativa') {
            grupos.descripcion.style.display = 'block';
        } else if (tipo === 'archivos') {
            grupos.descripcion.style.display = 'block';
            grupos.archivos.style.display = 'block';
            // Inicializar dropzones mini dentro del grupo
            requestAnimationFrame(() => {
                dashboard.inicializarDropzones(grupos.archivos);
            });
        } else if (tipo === 'enlace') {
            grupos.descripcion.style.display = 'block';
            grupos.urlRecurso.style.display = 'block';

            if (labelUrlRecursoEditar) labelUrlRecursoEditar.textContent = 'URL del Enlace:';
            if (inputUrlEditar) inputUrlEditar.style.display = 'block';
        }
    }

    document.getElementById('modal-editar-bloque').style.display = 'flex';
}

function cerrarModalEditarBloque() {
    document.getElementById('modal-editar-bloque').style.display = 'none';
    bloqueEnEdicion = null;
    document.getElementById('form-editar-bloque').reset();
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Escape' && document.getElementById('modal-editar-bloque').style.display === 'flex') {
        cerrarModalEditarBloque();
    }
});