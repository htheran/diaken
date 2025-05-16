/**
 * Playbook Select - Mejora visual para selectores de playbooks
 * Versión 1.0 - Mayo 2025
 */

document.addEventListener('DOMContentLoaded', function() {
  // Función para aplicar clases a las opciones según su categoría
  function enhancePlaybookSelect() {
    const playbookSelects = document.querySelectorAll('#playbook');
    
    playbookSelects.forEach(select => {
      // Añadir clase al select
      select.classList.add('playbook-select');
      
      // Observar cambios en las opciones del select
      const observer = new MutationObserver(function(mutations) {
        mutations.forEach(function(mutation) {
          if (mutation.type === 'childList') {
            // Aplicar clases a las opciones según su categoría
            const options = select.querySelectorAll('option');
            options.forEach(option => {
              const category = option.getAttribute('data-category');
              if (category) {
                option.classList.add(category);
              }
            });
          }
        });
      });
      
      // Configurar el observador
      observer.observe(select, { childList: true, subtree: true });
    });
  }
  
  // Inicializar al cargar la página
  enhancePlaybookSelect();
  
  // Exponer la función para uso global
  window.enhancePlaybookSelect = enhancePlaybookSelect;
});
