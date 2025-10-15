// Scripts JavaScript pour l'application Solvabilité II

document.addEventListener('DOMContentLoaded', function() {
    // Gestion des messages flash
    const alerts = document.querySelectorAll('.alert');
    alerts.forEach(alert => {
        setTimeout(() => {
            alert.classList.add('fade');
            setTimeout(() => {
                if (alert.parentElement) {
                    alert.remove();
                }
            }, 150);
        }, 5000);
    });

    // Validation des formulaires numériques
    const numberInputs = document.querySelectorAll('input[type="number"]');
    numberInputs.forEach(input => {
        input.addEventListener('change', function() {
            if (this.value < 0) {
                this.value = 0;
                showToast('Les valeurs négatives ne sont pas autorisées', 'warning');
            }

            // Formatage automatique des grands nombres
            if (this.value >= 1000) {
                const formatted = new Intl.NumberFormat('fr-FR').format(this.value);
                this.value = formatted.replace(/,/g, ' ');
            }
        });
    });

    // Amélioration de l'UX des formulaires
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                submitBtn.disabled = true;
                submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Traitement...';
            }
        });
    });

    // Tooltips Bootstrap
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    const tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Gestion des dropdowns
    const dropdowns = document.querySelectorAll('.dropdown');
    dropdowns.forEach(dropdown => {
        dropdown.addEventListener('show.bs.dropdown', function() {
            this.querySelector('.dropdown-toggle').classList.add('active');
        });

        dropdown.addEventListener('hide.bs.dropdown', function() {
            this.querySelector('.dropdown-toggle').classList.remove('active');
        });
    });

    // Initialisation automatique des toggle password
    initPasswordToggles();

    // Initialisation de la force du mot de passe pour l'inscription
    initPasswordStrength();
});

// Fonction pour basculer l'affichage du mot de passe
function togglePasswordVisibility(inputId, iconId) {
    const passwordInput = document.getElementById(inputId);
    const toggleIcon = document.getElementById(iconId);

    if (passwordInput.type === 'password') {
        passwordInput.type = 'text';
        toggleIcon.classList.remove('fa-eye');
        toggleIcon.classList.add('fa-eye-slash');
        toggleIcon.title = 'Masquer le mot de passe';
    } else {
        passwordInput.type = 'password';
        toggleIcon.classList.remove('fa-eye-slash');
        toggleIcon.classList.add('fa-eye');
        toggleIcon.title = 'Afficher le mot de passe';
    }
}

// Fonction pour initialiser les toggle password
function initPasswordToggles() {
    const passwordInputs = document.querySelectorAll('input[type="password"]');
    passwordInputs.forEach(input => {
        // Vérifier si le wrapper existe déjà
        if (!input.parentElement.classList.contains('password-toggle-group')) {
            const wrapper = document.createElement('div');
            wrapper.className = 'password-toggle-group';

            const toggleBtn = document.createElement('button');
            toggleBtn.type = 'button';
            toggleBtn.className = 'password-toggle-icon';
            toggleBtn.innerHTML = '<i class="fas fa-eye"></i>';
            toggleBtn.title = 'Afficher le mot de passe';

            // Déplacer l'input dans le wrapper
            input.parentNode.insertBefore(wrapper, input);
            wrapper.appendChild(input);
            wrapper.appendChild(toggleBtn);

            // Ajouter la classe pour le padding
            input.classList.add('password-field');

            // Ajouter l'événement
            toggleBtn.addEventListener('click', function() {
                const icon = this.querySelector('i');
                if (input.type === 'password') {
                    input.type = 'text';
                    icon.classList.remove('fa-eye');
                    icon.classList.add('fa-eye-slash');
                    this.title = 'Masquer le mot de passe';
                } else {
                    input.type = 'password';
                    icon.classList.remove('fa-eye-slash');
                    icon.classList.add('fa-eye');
                    this.title = 'Afficher le mot de passe';
                }
            });
        }
    });
}

// Fonction pour vérifier la force du mot de passe en temps réel
function checkPasswordStrength(password) {
    let strength = 0;
    const requirements = {
        length: false,
        uppercase: false,
        lowercase: false,
        number: false,
        special: false
    };

    // Vérification de la longueur
    if (password.length >= 8) {
        strength += 1;
        requirements.length = true;
    }

    // Vérification des majuscules
    if (/[A-Z]/.test(password)) {
        strength += 1;
        requirements.uppercase = true;
    }

    // Vérification des minuscules
    if (/[a-z]/.test(password)) {
        strength += 1;
        requirements.lowercase = true;
    }

    // Vérification des chiffres
    if (/[0-9]/.test(password)) {
        strength += 1;
        requirements.number = true;
    }

    // Vérification des caractères spéciaux
    if (/[!@#$%^&*()_+\-=\[\]{};':"\\|,.<>?`~]/.test(password)) {
        strength += 1;
        requirements.special = true;
    }

    return { strength, requirements };
}

// Fonction pour initialiser la force du mot de passe
function initPasswordStrength() {
    const password1Input = document.getElementById('id_password1');
    if (password1Input) {
        // Créer les éléments d'affichage de la force
        let strengthBar = document.getElementById('password-strength-bar');
        let requirementsDiv = document.getElementById('password-requirements');

        if (!strengthBar) {
            strengthBar = document.createElement('div');
            strengthBar.id = 'password-strength-bar';
            strengthBar.className = 'password-strength';
            password1Input.parentNode.appendChild(strengthBar);
        }

        if (!requirementsDiv) {
            requirementsDiv = document.createElement('div');
            requirementsDiv.id = 'password-requirements';
            password1Input.parentNode.appendChild(requirementsDiv);
        }

        password1Input.addEventListener('input', function() {
            updatePasswordStrength(this.value, 'password-strength-bar', 'password-requirements');
        });

        // Initialiser avec la valeur actuelle
        updatePasswordStrength(password1Input.value, 'password-strength-bar', 'password-requirements');
    }
}

// Fonction pour mettre à jour l'affichage de la force du mot de passe
function updatePasswordStrength(password, strengthBarId, requirementsId) {
    const { strength, requirements } = checkPasswordStrength(password);
    const strengthBar = document.getElementById(strengthBarId);
    const requirementsContainer = document.getElementById(requirementsId);

    // Mise à jour de la barre de force
    if (strengthBar) {
        strengthBar.className = 'password-strength';

        if (password.length === 0) {
            strengthBar.style.width = '0%';
            strengthBar.style.backgroundColor = '#e9ecef';
        } else if (strength <= 2) {
            strengthBar.classList.add('password-strength-weak');
        } else if (strength === 3) {
            strengthBar.classList.add('password-strength-medium');
        } else if (strength === 4) {
            strengthBar.classList.add('password-strength-good');
        } else {
            strengthBar.classList.add('password-strength-strong');
        }
    }

    // Mise à jour des exigences
    if (requirementsContainer) {
        requirementsContainer.innerHTML = `
            <div class="password-requirements">
                <div class="${requirements.length ? 'requirement-met' : 'requirement-unmet'}">
                    <i class="fas ${requirements.length ? 'fa-check-circle' : 'fa-circle'} me-1"></i>
                    Au moins 8 caractères
                </div>
                <div class="${requirements.uppercase ? 'requirement-met' : 'requirement-unmet'}">
                    <i class="fas ${requirements.uppercase ? 'fa-check-circle' : 'fa-circle'} me-1"></i>
                    Une lettre majuscule
                </div>
                <div class="${requirements.lowercase ? 'requirement-met' : 'requirement-unmet'}">
                    <i class="fas ${requirements.lowercase ? 'fa-check-circle' : 'fa-circle'} me-1"></i>
                    Une lettre minuscule
                </div>
                <div class="${requirements.number ? 'requirement-met' : 'requirement-unmet'}">
                    <i class="fas ${requirements.number ? 'fa-check-circle' : 'fa-circle'} me-1"></i>
                    Un chiffre
                </div>
                <div class="${requirements.special ? 'requirement-met' : 'requirement-unmet'}">
                    <i class="fas ${requirements.special ? 'fa-check-circle' : 'fa-circle'} me-1"></i>
                    Un caractère spécial
                </div>
            </div>
        `;
    }
}

// Fonction pour afficher des toasts (notification)
function showToast(message, type = 'info') {
    // Création du toast Bootstrap
    const toastContainer = document.getElementById('toast-container') || createToastContainer();

    const toastEl = document.createElement('div');
    toastEl.className = `toast align-items-center text-bg-${type} border-0`;
    toastEl.setAttribute('role', 'alert');
    toastEl.setAttribute('aria-live', 'assertive');
    toastEl.setAttribute('aria-atomic', 'true');

    toastEl.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                <i class="fas fa-${getToastIcon(type)} me-2"></i>
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;

    toastContainer.appendChild(toastEl);

    const toast = new bootstrap.Toast(toastEl);
    toast.show();

    // Nettoyage après disparition
    toastEl.addEventListener('hidden.bs.toast', function() {
        this.remove();
    });
}

function createToastContainer() {
    const container = document.createElement('div');
    container.id = 'toast-container';
    container.className = 'toast-container position-fixed top-0 end-0 p-3';
    container.style.zIndex = '9999';
    document.body.appendChild(container);
    return container;
}

function getToastIcon(type) {
    const icons = {
        'success': 'check-circle',
        'error': 'exclamation-triangle',
        'warning': 'exclamation-triangle',
        'info': 'info-circle'
    };
    return icons[type] || 'info-circle';
}

// Fonctions utilitaires pour les calculs financiers
class FinancialUtils {
    static formatCurrency(amount, currency = '€') {
        return new Intl.NumberFormat('fr-FR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(amount) + ' ' + currency;
    }

    static formatPercentage(value) {
        return new Intl.NumberFormat('fr-FR', {
            minimumFractionDigits: 1,
            maximumFractionDigits: 1
        }).format(value) + '%';
    }

    static calculateRatio(numerator, denominator) {
        if (denominator === 0) return 0;
        return (numerator / denominator) * 100;
    }

    static calculateExcessCapital(fondsPropres, scr) {
        return fondsPropres - scr;
    }
}

// Export pour utilisation globale
window.FinancialUtils = FinancialUtils;
window.showToast = showToast;
window.togglePasswordVisibility = togglePasswordVisibility;