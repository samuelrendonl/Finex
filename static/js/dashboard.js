// Load user information on page load
document.addEventListener('DOMContentLoaded', () => {
    loadUserInfo();
    setupMenuListeners();
    setupProfileForm();
    setupPasswordForm();
    setupUserMenu();
});

// Load user information
async function loadUserInfo() {
    try {
        const response = await fetch('/api/usuario-info');
        
        if (!response.ok) {
            if (response.status === 401) {
                window.location.href = '/';
                return;
            }
            throw new Error('Error al cargar información del usuario');
        }
        
        const data = await response.json();
        
        // Update user name in header and sidebar
        document.getElementById('userName').textContent = data.nombre;
        
        // Update profile form
        document.getElementById('profileName').value = data.nombre;
        document.getElementById('profileCompany').value = data.empresa || '';
        document.getElementById('profileEmail').value = data.email;
        
    } catch (error) {
        console.error('Error:', error);
        showModal('Error al cargar la información del usuario');
    }
}

// Setup menu navigation
function setupMenuListeners() {
    const menuItems = document.querySelectorAll('.menu-item');
    
    menuItems.forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            
            // Remove active class from all items
            menuItems.forEach(mi => mi.classList.remove('active'));
            
            // Add active class to clicked item
            item.classList.add('active');
            
            // Get section id
            const sectionId = item.getAttribute('data-section');
            
            // Show section
            openSection(sectionId);
            
            // Close user dropdown if open
            const userDropdown = document.getElementById('userDropdown');
            if (userDropdown.classList.contains('show')) {
                userDropdown.classList.remove('show');
            }
        });
    });
}

// Open section
function openSection(sectionId, e = null) {
    if (e) {
        e.preventDefault();
    }
    
    // Hide all sections
    const sections = document.querySelectorAll('.content-section');
    sections.forEach(section => {
        section.classList.remove('active');
    });
    
    // Show selected section
    const selectedSection = document.getElementById(sectionId);
    if (selectedSection) {
        selectedSection.classList.add('active');
        
        // Update header title
        const title = selectedSection.querySelector('.section-title h2');
        if (title) {
            document.querySelector('.header-left h1').textContent = title.textContent;
        }
    }
}

// User menu toggle
function setupUserMenu() {
    const userMenuBtn = document.getElementById('userMenuBtn');
    const userDropdown = document.getElementById('userDropdown');
    
    userMenuBtn.addEventListener('click', (e) => {
        e.preventDefault();
        userDropdown.classList.toggle('show');
    });
    
    // Close dropdown when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.user-menu')) {
            userDropdown.classList.remove('show');
        }
    });
}

// Setup profile form
function setupProfileForm() {
    const form = document.getElementById('formProfile');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const nombre = document.getElementById('profileName').value.trim();
        const empresa = document.getElementById('profileCompany').value.trim();
        
        if (!nombre) {
            showModal('Por favor ingresa tu nombre', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/actualizar-perfil', {
                method: 'PUT',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    nombre: nombre,
                    empresa: empresa
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                showModal(data.error || 'Error al actualizar perfil', 'error');
                return;
            }
            
            // Update user name in header
            document.getElementById('userName').textContent = nombre;
            
            showModal(data.message, 'success');
            
        } catch (error) {
            showModal('Error de conexión: ' + error.message, 'error');
        }
    });
}

// Setup password form
function setupPasswordForm() {
    const form = document.getElementById('formPassword');
    
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const actual = document.getElementById('currentPassword').value;
        const nueva = document.getElementById('newPassword').value;
        const confirmar = document.getElementById('confirmPassword').value;
        
        if (!actual || !nueva || !confirmar) {
            showModal('Por favor completa todos los campos', 'error');
            return;
        }
        
        if (nueva.length < 6) {
            showModal('La nueva contraseña debe tener al menos 6 caracteres', 'error');
            return;
        }
        
        if (nueva !== confirmar) {
            showModal('Las contraseñas nuevas no coinciden', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/cambiar-contraseña', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    contraseña_actual: actual,
                    contraseña_nueva: nueva
                })
            });
            
            const data = await response.json();
            
            if (!response.ok) {
                showModal(data.error || 'Error al cambiar contraseña', 'error');
                return;
            }
            
            showModal(data.message, 'success');
            
            // Clear form
            form.reset();
            
        } catch (error) {
            showModal('Error de conexión: ' + error.message, 'error');
        }
    });
}

// Logout
async function logout(e) {
    if (e) {
        e.preventDefault();
    }
    
    try {
        const response = await fetch('/api/logout', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            window.location.href = data.redirect;
        }
        
    } catch (error) {
        console.error('Error:', error);
        window.location.href = '/';
    }
}

// Alternative logout from sidebar button
document.addEventListener('DOMContentLoaded', () => {
    const logoutBtn = document.getElementById('btnLogout');
    if (logoutBtn) {
        logoutBtn.addEventListener('click', logout);
    }
});

// Change password modal
function changePassword(e) {
    if (e) {
        e.preventDefault();
    }
    
    openSection('configuracion');
    
    // Focus on the password field
    setTimeout(() => {
        document.getElementById('currentPassword').focus();
    }, 300);
}

// Modal functions
function showModal(message, type = 'info') {
    const modal = document.getElementById('messageModal');
    const modalMessage = document.getElementById('modalMessage');
    
    modalMessage.innerHTML = message;
    
    // Add color based on type
    if (type === 'success') {
        modalMessage.style.color = '#16a34a';
    } else if (type === 'error') {
        modalMessage.style.color = '#dc2626';
    }
    
    modal.classList.add('show');
}

function closeModal() {
    const modal = document.getElementById('messageModal');
    modal.classList.remove('show');
}

// Close modal when clicking the X
document.addEventListener('DOMContentLoaded', () => {
    const closeBtn = document.querySelector('.close');
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }
    
    // Close modal when clicking outside
    const modal = document.getElementById('messageModal');
    if (modal) {
        window.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    }
});

// Session timeout warning (opcional)
let sessionTimeout;

function resetSessionTimeout() {
    clearTimeout(sessionTimeout);
    
    sessionTimeout = setTimeout(() => {
        logout();
    }, 30 * 60 * 1000); // 30 minutes
}

document.addEventListener('mousemove', resetSessionTimeout);
document.addEventListener('keypress', resetSessionTimeout);
document.addEventListener('click', resetSessionTimeout);

resetSessionTimeout();

// Page visibility - renew session on return
document.addEventListener('visibilitychange', () => {
    if (!document.hidden) {
        resetSessionTimeout();
    }
});
