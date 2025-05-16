/**
 * Icon Select - Script para mostrar iconos en el selector de playbooks
 * Versión 1.1 - Mayo 2025
 */

// Función que se ejecuta cuando el DOM está listo
document.addEventListener('DOMContentLoaded', function() {
  // Inicializar los selectores al cargar la página
  initializeSelectors();
  
  // Función para inicializar todos los selectores de playbooks
  function initializeSelectors() {
    // Añadir estilos CSS directamente al documento
    addStyles();
    
    // Inicializar los selectores existentes
    setupExistingSelectors();
    
    // Observar cambios en el DOM para inicializar nuevos selectores
    observeDOMChanges();
  }
  
  // Añadir estilos CSS directamente al documento
  function addStyles() {
    const styleEl = document.createElement('style');
    styleEl.textContent = `
      .playbook-select-container {
        position: relative;
        width: 100%;
      }
      
      .playbook-select {
        width: 100%;
        padding: 8px 12px;
        border: 1px solid #ced4da;
        border-radius: 4px;
        appearance: none;
        -webkit-appearance: none;
        -moz-appearance: none;
        background-color: white;
        background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 16 16'%3E%3Cpath fill='none' stroke='%23343a40' stroke-linecap='round' stroke-linejoin='round' stroke-width='2' d='M2 5l6 6 6-6'/%3E%3C/svg%3E");
        background-repeat: no-repeat;
        background-position: right 12px center;
        background-size: 16px 12px;
        cursor: pointer;
      }
      
      .playbook-display {
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        bottom: 0;
        padding: 8px 12px;
        display: flex;
        align-items: center;
        pointer-events: none;
        background-color: transparent;
      }
      
      .playbook-icon {
        margin-right: 8px;
        display: inline-block;
        width: 16px;
        text-align: center;
      }
      
      .playbook-text {
        white-space: nowrap;
        overflow: hidden;
        text-overflow: ellipsis;
      }
      
      .icon-install { color: #28a745; }
      .icon-configure { color: #007bff; }
      .icon-fix { color: #fd7e14; }
      .icon-reset { color: #6f42c1; }
      .icon-diagnose { color: #17a2b8; }
      .icon-clean { color: #dc3545; }
      .icon-other { color: #6c757d; }
    `;
    document.head.appendChild(styleEl);
  }
  
  // Configurar los selectores existentes
  function setupExistingSelectors() {
    const selects = document.querySelectorAll('#playbook');
    selects.forEach(setupPlaybookSelect);
  }
  
  // Observar cambios en el DOM para inicializar nuevos selectores
  function observeDOMChanges() {
    const observer = new MutationObserver(function(mutations) {
      mutations.forEach(function(mutation) {
        if (mutation.type === 'childList') {
          mutation.addedNodes.forEach(function(node) {
            if (node.nodeType === 1) { // Elemento HTML
              if (node.id === 'playbook') {
                setupPlaybookSelect(node);
              } else {
                const selects = node.querySelectorAll('#playbook');
                selects.forEach(setupPlaybookSelect);
              }
            }
          });
        }
      });
    });
    
    observer.observe(document.body, {
      childList: true,
      subtree: true
    });
  }
  
  // Configurar un selector de playbooks individual
  function setupPlaybookSelect(select) {
    // Evitar inicializar el mismo select múltiples veces
    if (select.dataset.initialized === 'true') {
      return;
    }
    
    // Marcar como inicializado
    select.dataset.initialized = 'true';
    
    // Añadir clase al select
    select.classList.add('playbook-select');
    
    // Crear contenedor
    const container = document.createElement('div');
    container.className = 'playbook-select-container';
    
    // Reemplazar el select con el contenedor
    select.parentNode.insertBefore(container, select);
    container.appendChild(select);
    
    // Crear el div para mostrar la opción seleccionada con icono
    const displayDiv = document.createElement('div');
    displayDiv.className = 'playbook-display';
    container.appendChild(displayDiv);
    
    // Hacer clic en el display para abrir el select nativo
    displayDiv.addEventListener('click', function() {
      // Simular clic en el select nativo
      const event = new MouseEvent('mousedown', {
        bubbles: true,
        cancelable: true,
        view: window
      });
      select.dispatchEvent(event);
    });
    
    // Actualizar el display cuando cambia el select
    select.addEventListener('change', function() {
      updateDisplay(select, displayDiv);
    });
    
    // Inicializar el display
    updateDisplay(select, displayDiv);
    
    // Asegurarse de que el select original no esté oculto completamente
    // Solo hacerlo visualmente invisible pero mantenerlo accesible
    select.style.opacity = '0.01';
    select.style.position = 'absolute';
    select.style.pointerEvents = 'auto';
    select.style.height = '100%';
    select.style.width = '100%';
    select.style.zIndex = '1';
  }
  
  // Actualizar el display con la opción seleccionada
  function updateDisplay(select, displayDiv) {
    // Limpiar el contenido actual
    displayDiv.innerHTML = '';
    
    // Obtener la opción seleccionada
    const selectedOption = select.options[select.selectedIndex];
    
    // Si no hay opción seleccionada o es la opción por defecto, mostrar texto por defecto
    if (!selectedOption || !selectedOption.value) {
      const textSpan = document.createElement('span');
      textSpan.className = 'playbook-text';
      textSpan.textContent = 'Seleccionar playbook';
      displayDiv.appendChild(textSpan);
      return;
    }
    
    // Obtener la categoría de la opción seleccionada
    const category = selectedOption.getAttribute('data-category');
    
    // Crear el icono según la categoría
    if (category) {
      const iconSpan = document.createElement('span');
      iconSpan.className = `playbook-icon icon-${category}`;
      
      // Definir el icono según la categoría
      const iconClass = {
        'install': 'fa-download',
        'configure': 'fa-cog',
        'fix': 'fa-wrench',
        'reset': 'fa-sync',
        'diagnose': 'fa-stethoscope',
        'clean': 'fa-trash',
        'other': 'fa-file-code'
      };
      
      // Crear el icono
      iconSpan.innerHTML = `<i class="fas ${iconClass[category] || 'fa-file-code'}"></i>`;
      
      // Añadir el icono al display
      displayDiv.appendChild(iconSpan);
    }
    
    // Añadir el texto de la opción
    const textSpan = document.createElement('span');
    textSpan.className = 'playbook-text';
    textSpan.textContent = selectedOption.textContent;
    displayDiv.appendChild(textSpan);
  }
  
  // Exponer funciones para uso global
  window.setupPlaybookSelectors = setupExistingSelectors;
  window.initializePlaybookSelectors = initializeSelectors;
});
