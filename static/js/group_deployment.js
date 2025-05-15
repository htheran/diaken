// Funcionalidad para filtrar grupos por ambiente
document.addEventListener('DOMContentLoaded', function() {
    const environmentSelect = document.getElementById('id_environment');
    const groupSelect = document.getElementById('id_group');
    const playbookSelect = document.getElementById('id_playbook');
    
    if (environmentSelect && groupSelect) {
        // Guardar las opciones originales
        let originalGroups = [];
        
        // Capturar las opciones originales después de que la página se cargue completamente
        setTimeout(() => {
            originalGroups = Array.from(groupSelect.options);
        }, 100);
        
        // Función para filtrar los grupos según el ambiente seleccionado
        function filterGroupsByEnvironment() {
            const selectedEnvironmentId = environmentSelect.value;
            
            // Deshabilitar el selector de grupos mientras se cargan los datos
            groupSelect.disabled = true;
            
            // Limpiar el select de grupos
            groupSelect.innerHTML = '';
            
            // Añadir la opción por defecto
            const defaultOption = document.createElement('option');
            defaultOption.value = '';
            defaultOption.textContent = 'Seleccione un grupo';
            groupSelect.appendChild(defaultOption);
            
            if (!selectedEnvironmentId) {
                groupSelect.disabled = false;
                return;
            }
            
            // Hacer una petición AJAX para obtener los grupos del ambiente seleccionado
            fetch(`/api/groups-by-environment/${selectedEnvironmentId}/`)
                .then(response => response.json())
                .then(data => {
                    if (data.groups && data.groups.length > 0) {
                        data.groups.forEach(group => {
                            const option = document.createElement('option');
                            option.value = group.id;
                            option.textContent = group.name;
                            groupSelect.appendChild(option);
                        });
                    } else {
                        // No hay grupos disponibles para este ambiente
                    }
                    groupSelect.disabled = false;
                })
                .catch(error => {
                    // Error al obtener los grupos
                    groupSelect.disabled = false;
                });
        }
        
        // Filtrar los grupos cuando cambia el ambiente
        environmentSelect.addEventListener('change', filterGroupsByEnvironment);
        
        // Iniciar la carga de grupos si ya hay un ambiente seleccionado
        if (environmentSelect.value) {
            filterGroupsByEnvironment();
        }
    }
});
