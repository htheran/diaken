/**
 * Enhanced Select - Mejora visual para selectores con iconos
 * Versión 1.0 - Mayo 2025
 */

document.addEventListener('DOMContentLoaded', function() {
  // Función para inicializar selectores mejorados
  function initEnhancedSelects() {
    // Aplicar a todos los selectores con la clase 'modern-select'
    const selects = document.querySelectorAll('.modern-select');
    
    selects.forEach(select => {
      // Crear un contenedor personalizado
      const container = document.createElement('div');
      container.className = 'enhanced-select-container';
      select.parentNode.insertBefore(container, select);
      container.appendChild(select);
      
      // Crear el elemento visual del selector
      const visualSelect = document.createElement('div');
      visualSelect.className = 'enhanced-select-visual';
      container.appendChild(visualSelect);
      
      // Crear el elemento para mostrar la opción seleccionada
      const selectedOption = document.createElement('div');
      selectedOption.className = 'enhanced-select-selected';
      selectedOption.innerHTML = select.options[select.selectedIndex]?.innerHTML || 'Seleccione una opción';
      visualSelect.appendChild(selectedOption);
      
      // Crear el icono de flecha
      const arrow = document.createElement('div');
      arrow.className = 'enhanced-select-arrow';
      visualSelect.appendChild(arrow);
      
      // Crear el contenedor de opciones
      const optionsContainer = document.createElement('div');
      optionsContainer.className = 'enhanced-select-options';
      container.appendChild(optionsContainer);
      
      // Evento para mostrar/ocultar opciones
      visualSelect.addEventListener('click', function(e) {
        e.stopPropagation();
        this.classList.toggle('active');
        optionsContainer.classList.toggle('show');
        
        // Cerrar otros selectores abiertos
        document.querySelectorAll('.enhanced-select-visual.active').forEach(el => {
          if (el !== this) {
            el.classList.remove('active');
            el.nextElementSibling.classList.remove('show');
          }
        });
      });
      
      // Generar las opciones visuales
      let currentOptgroup = null;
      let currentOptgroupEl = null;
      
      Array.from(select.options).forEach(option => {
        // Verificar si es un nuevo grupo
        if (option.parentNode.tagName === 'OPTGROUP' && option.parentNode !== currentOptgroup) {
          currentOptgroup = option.parentNode;
          currentOptgroupEl = document.createElement('div');
          currentOptgroupEl.className = 'enhanced-select-optgroup';
          currentOptgroupEl.innerHTML = `<div class="enhanced-select-optgroup-label">${currentOptgroup.label}</div>`;
          optionsContainer.appendChild(currentOptgroupEl);
        }
        
        // Crear la opción visual
        const optionEl = document.createElement('div');
        optionEl.className = 'enhanced-select-option';
        optionEl.setAttribute('data-value', option.value);
        optionEl.innerHTML = option.innerHTML;
        
        // Añadir estilos si tiene atributos de icono
        if (option.getAttribute('data-icon')) {
          const icon = option.getAttribute('data-icon');
          const color = option.getAttribute('data-color');
          optionEl.classList.add('with-icon');
          optionEl.style.setProperty('--icon-color', color);
          
          // Prepend icon
          const iconEl = document.createElement('i');
          iconEl.className = `fas ${icon}`;
          iconEl.style.color = color;
          optionEl.prepend(iconEl);
        }
        
        // Evento al hacer clic en la opción
        optionEl.addEventListener('click', function(e) {
          e.stopPropagation();
          select.value = this.getAttribute('data-value');
          selectedOption.innerHTML = this.innerHTML;
          optionsContainer.classList.remove('show');
          visualSelect.classList.remove('active');
          
          // Disparar evento change en el select original
          const event = new Event('change', { bubbles: true });
          select.dispatchEvent(event);
        });
        
        // Añadir la opción al contenedor correspondiente
        if (currentOptgroupEl && option.parentNode === currentOptgroup) {
          currentOptgroupEl.appendChild(optionEl);
        } else {
          optionsContainer.appendChild(optionEl);
        }
      });
      
      // Cerrar al hacer clic fuera
      document.addEventListener('click', function() {
        optionsContainer.classList.remove('show');
        visualSelect.classList.remove('active');
      });
      
      // Actualizar el select visual cuando cambia el original
      select.addEventListener('change', function() {
        const selectedOption = this.options[this.selectedIndex];
        if (selectedOption) {
          visualSelect.querySelector('.enhanced-select-selected').innerHTML = selectedOption.innerHTML;
        }
      });
    });
  }
  
  // Inicializar selectores al cargar la página
  initEnhancedSelects();
  
  // Exponer la función para uso global
  window.initEnhancedSelects = initEnhancedSelects;
});
