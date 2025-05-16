/**
 * Simple Select - Script para mostrar iconos en el selector de playbooks
 * Versión 1.0 - Mayo 2025
 */

document.addEventListener('DOMContentLoaded', function() {
  // Función para añadir iconos a las opciones seleccionadas
  function updateSelectedOption(select) {
    // Obtener la opción seleccionada
    const selectedOption = select.options[select.selectedIndex];
    
    // Si no hay opción seleccionada o es la opción por defecto, no hacer nada
    if (!selectedOption || !selectedOption.value) {
      return;
    }
    
    // Obtener la categoría de la opción seleccionada
    const category = selectedOption.getAttribute('data-category');
    
    // Si no hay categoría, no hacer nada
    if (!category) {
      return;
    }
    
    // Crear un div para mostrar la opción seleccionada con icono
    const selectedDiv = document.createElement('div');
    selectedDiv.className = 'selected-option';
    selectedDiv.style.display = 'flex';
    selectedDiv.style.alignItems = 'center';
    
    // Añadir el icono según la categoría
    const iconSpan = document.createElement('span');
    iconSpan.className = `icon-container icon-${category}`;
    
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
    
    // Añadir el texto de la opción
    const textSpan = document.createElement('span');
    textSpan.textContent = selectedOption.textContent;
    
    // Añadir los elementos al div
    selectedDiv.appendChild(iconSpan);
    selectedDiv.appendChild(textSpan);
    
    // Insertar el div antes del select
    const parent = select.parentNode;
    
    // Eliminar cualquier div de selección anterior
    const previousSelected = parent.querySelector('.selected-option');
    if (previousSelected) {
      parent.removeChild(previousSelected);
    }
    
    // Insertar el nuevo div
    parent.insertBefore(selectedDiv, select);
    
    // Ocultar el select original
    select.style.opacity = '0';
    select.style.position = 'absolute';
    select.style.zIndex = '-1';
  }
  
  // Función para añadir iconos a las opciones del selector
  function enhancePlaybookSelects() {
    const selects = document.querySelectorAll('#playbook');
    
    selects.forEach(select => {
      // Añadir clase al select
      select.classList.add('playbook-select');
      
      // Crear un contenedor para el select
      const container = document.createElement('div');
      container.className = 'select-container';
      
      // Reemplazar el select con el contenedor
      select.parentNode.insertBefore(container, select);
      container.appendChild(select);
      
      // Actualizar la opción seleccionada cuando cambia el select
      select.addEventListener('change', function() {
        updateSelectedOption(this);
      });
      
      // Inicializar la opción seleccionada
      if (select.options.length > 0 && select.selectedIndex >= 0) {
        updateSelectedOption(select);
      }
    });
  }
  
  // Inicializar los selectores al cargar la página
  enhancePlaybookSelects();
  
  // Exponer la función para uso global
  window.enhancePlaybookSelects = enhancePlaybookSelects;
});
