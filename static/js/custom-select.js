/**
 * Custom Select - Implementación de selectores personalizados con iconos
 * Versión 1.0 - Mayo 2025
 */

class CustomSelect {
  constructor(selectElement) {
    this.originalSelect = selectElement;
    this.container = document.createElement('div');
    this.customSelect = document.createElement('div');
    this.dropdown = document.createElement('div');
    this.selectedOption = null;
    
    this.init();
  }
  
  init() {
    // Configurar el contenedor
    this.container.className = 'custom-select-container';
    this.originalSelect.parentNode.insertBefore(this.container, this.originalSelect);
    this.container.appendChild(this.originalSelect);
    
    // Configurar el select personalizado
    this.customSelect.className = 'custom-select';
    this.container.appendChild(this.customSelect);
    
    // Configurar el dropdown
    this.dropdown.className = 'custom-select-dropdown';
    this.container.appendChild(this.dropdown);
    
    // Poblar el dropdown con las opciones del select original
    this.populateDropdown();
    
    // Configurar eventos
    this.setupEvents();
    
    // Actualizar el texto inicial
    this.updateSelectedText();
  }
  
  populateDropdown() {
    const options = this.originalSelect.querySelectorAll('option');
    const optgroups = this.originalSelect.querySelectorAll('optgroup');
    
    if (optgroups.length > 0) {
      // Si hay optgroups, crear categorías
      optgroups.forEach(optgroup => {
        const categoryDiv = document.createElement('div');
        categoryDiv.className = 'custom-select-category';
        categoryDiv.textContent = optgroup.label;
        this.dropdown.appendChild(categoryDiv);
        
        const groupOptions = optgroup.querySelectorAll('option');
        groupOptions.forEach(option => {
          this.createOptionElement(option);
        });
      });
    } else {
      // Si no hay optgroups, crear opciones directamente
      options.forEach(option => {
        this.createOptionElement(option);
      });
    }
  }
  
  createOptionElement(option) {
    if (option.value === '') return; // Ignorar opciones vacías
    
    const optionDiv = document.createElement('div');
    optionDiv.className = 'custom-select-option';
    optionDiv.dataset.value = option.value;
    
    // Añadir icono si hay categoría
    const category = option.getAttribute('data-category') || '';
    if (category) {
      const icon = document.createElement('i');
      icon.className = `fas ${this.getCategoryIcon(category)} ${category}`;
      optionDiv.appendChild(icon);
    }
    
    // Añadir texto
    const text = document.createElement('span');
    text.textContent = option.textContent;
    optionDiv.appendChild(text);
    
    // Evento de clic para seleccionar
    optionDiv.addEventListener('click', () => {
      this.selectOption(optionDiv);
    });
    
    this.dropdown.appendChild(optionDiv);
    
    // Marcar como seleccionado si es la opción actual
    if (option.selected) {
      this.selectOption(optionDiv, false);
    }
  }
  
  getCategoryIcon(category) {
    const icons = {
      'install': 'fa-download',
      'configure': 'fa-cog',
      'fix': 'fa-wrench',
      'reset': 'fa-sync',
      'diagnose': 'fa-stethoscope',
      'clean': 'fa-trash',
      'other': 'fa-file-code'
    };
    return icons[category] || 'fa-file-code';
  }
  
  setupEvents() {
    // Abrir/cerrar dropdown al hacer clic en el select
    this.customSelect.addEventListener('click', (e) => {
      e.stopPropagation();
      this.toggleDropdown();
    });
    
    // Cerrar dropdown al hacer clic fuera
    document.addEventListener('click', () => {
      this.closeDropdown();
    });
    
    // Sincronizar cambios en el select original
    this.originalSelect.addEventListener('change', () => {
      this.updateSelectedText();
    });
  }
  
  toggleDropdown() {
    this.dropdown.classList.toggle('active');
  }
  
  closeDropdown() {
    this.dropdown.classList.remove('active');
  }
  
  selectOption(optionDiv, triggerChange = true) {
    const value = optionDiv.dataset.value;
    
    // Actualizar clase seleccionada
    const allOptions = this.dropdown.querySelectorAll('.custom-select-option');
    allOptions.forEach(opt => opt.classList.remove('selected'));
    optionDiv.classList.add('selected');
    
    // Actualizar select original
    this.originalSelect.value = value;
    this.selectedOption = optionDiv;
    
    // Actualizar texto mostrado
    this.updateSelectedText();
    
    // Cerrar dropdown
    this.closeDropdown();
    
    // Disparar evento change
    if (triggerChange) {
      const event = new Event('change', { bubbles: true });
      this.originalSelect.dispatchEvent(event);
    }
  }
  
  updateSelectedText() {
    // Limpiar el contenido actual
    this.customSelect.innerHTML = '';
    
    const selectedOption = this.originalSelect.options[this.originalSelect.selectedIndex];
    
    if (selectedOption && selectedOption.value) {
      const category = selectedOption.getAttribute('data-category') || '';
      
      // Añadir icono si hay categoría
      if (category) {
        const icon = document.createElement('i');
        icon.className = `fas ${this.getCategoryIcon(category)} ${category}`;
        this.customSelect.appendChild(icon);
      }
      
      // Añadir texto
      const text = document.createElement('span');
      text.textContent = selectedOption.textContent;
      this.customSelect.appendChild(text);
    } else {
      // Opción por defecto
      this.customSelect.textContent = 'Select an option';
    }
  }
}

// Inicializar al cargar el DOM
document.addEventListener('DOMContentLoaded', function() {
  // Inicializar Font Awesome si no está ya cargado
  if (!document.querySelector('link[href*="fontawesome"]')) {
    const fontAwesomeLink = document.createElement('link');
    fontAwesomeLink.rel = 'stylesheet';
    fontAwesomeLink.href = 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.3/css/all.min.css';
    document.head.appendChild(fontAwesomeLink);
  }
  
  // Inicializar selectores personalizados
  function initCustomSelects() {
    const playbookSelects = document.querySelectorAll('#playbook');
    playbookSelects.forEach(select => {
      new CustomSelect(select);
    });
  }
  
  // Inicializar al cargar la página
  initCustomSelects();
  
  // Exponer la función para uso global
  window.initCustomSelects = initCustomSelects;
});
