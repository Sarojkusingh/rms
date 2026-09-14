// RMS SaaS Main Javascript Helper File

document.addEventListener('DOMContentLoaded', () => {
    // 1. Dark Theme Management
    const themeToggleBtn = document.getElementById('theme-toggle');
    const currentTheme = localStorage.getItem('theme') || 'light';
    
    // Apply current theme on load
    document.documentElement.setAttribute('data-theme', currentTheme);
    updateThemeIcon(currentTheme);
    
    if (themeToggleBtn) {
        themeToggleBtn.addEventListener('click', () => {
            const activeTheme = document.documentElement.getAttribute('data-theme');
            const newTheme = activeTheme === 'dark' ? 'light' : 'dark';
            
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            updateThemeIcon(newTheme);
        });
    }

    function updateThemeIcon(theme) {
        const icon = document.querySelector('#theme-toggle i');
        if (icon) {
            if (theme === 'dark') {
                icon.className = 'bi bi-sun-fill';
            } else {
                icon.className = 'bi bi-moon-fill';
            }
        }
    }

    // 2. Alert Auto-Dismissal
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getOrCreateInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });
});

// 3. Helper function for CSRF Cookie reading (needed for AJAX requests)
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// 4. AJAX Fetch wrapper for POST/PUT requests
async function sendAjaxRequest(url, data, method = 'POST') {
    const csrftoken = getCookie('csrftoken');
    
    try {
        const response = await fetch(url, {
            method: method,
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrftoken,
                'X-Requested-With': 'XMLHttpRequest'
            },
            body: JSON.stringify(data)
        });
        
        return await response.json();
    } catch (error) {
        console.error('AJAX request failed:', error);
        return { success: false, error: 'Connection failure' };
    }
}

// 5. Password Visibility Toggle
function togglePasswordVisibility(inputId, btn) {
    const input = document.getElementById(inputId);
    if (!input) return;
    
    const icon = btn.querySelector('i');
    if (input.type === 'password') {
        input.type = 'text';
        icon.className = 'bi bi-eye-slash';
    } else {
        input.type = 'password';
        icon.className = 'bi bi-eye';
    }
}

// 6. Password Strength Indicator
function updatePasswordStrength(password, fillEl, textEl) {
    if (!fillEl || !textEl) return;
    
    if (!password) {
        fillEl.style.width = '0%';
        fillEl.removeAttribute('data-level');
        textEl.textContent = '';
        textEl.removeAttribute('data-level');
        return;
    }
    
    let score = 0;
    
    // Length checks
    if (password.length >= 8) score++;
    if (password.length >= 12) score++;
    
    // Character variety checks
    if (/[a-z]/.test(password)) score++;
    if (/[A-Z]/.test(password)) score++;
    if (/[0-9]/.test(password)) score++;
    if (/[^a-zA-Z0-9]/.test(password)) score++;
    
    let level, label;
    if (score <= 2) {
        level = 'weak';
        label = 'Weak — add more characters and variety';
    } else if (score <= 3) {
        level = 'fair';
        label = 'Fair — try adding numbers or symbols';
    } else if (score <= 4) {
        level = 'good';
        label = 'Good — almost there!';
    } else {
        level = 'strong';
        label = 'Strong password ✓';
    }
    
    fillEl.setAttribute('data-level', level);
    textEl.setAttribute('data-level', level);
    textEl.textContent = label;
}

// Auto-initialize password toggles and strength indicators on page load
document.addEventListener('DOMContentLoaded', () => {
    // Password strength: bind to inputs with data-strength-target attribute
    document.querySelectorAll('[data-strength-target]').forEach(input => {
        const targetId = input.getAttribute('data-strength-target');
        const fillEl = document.querySelector(`#${targetId} .password-strength-fill`);
        const textEl = document.querySelector(`#${targetId} .password-strength-text`);
        
        input.addEventListener('input', () => {
            updatePasswordStrength(input.value, fillEl, textEl);
        });
    });
});
