function validateEmail(email) {
    const pattern = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
    return pattern.test(email);
}

function validatePhone(phone) {
    const cleaned = phone.replace(/[\s\-\(\)\+]/g, '');
    return /^\d{10,15}$/.test(cleaned);
}

function validatePassword(password) {
    if (!password || password.length < 6) {
        return {
            valid: false,
            message: 'Password must be at least 6 characters long',
            strength: 'weak'
        };
    }

    let strength = 'weak';
    if (password.length >= 8) {
        strength = 'medium';
    }
    if (password.length >= 12 && /[A-Z]/.test(password) && /[0-9]/.test(password)) {
        strength = 'strong';
    }

    return {
        valid: true,
        message: 'Password is valid',
        strength: strength
    };
}

function validatePastDate(dateStr) {
    if (!dateStr) return false;
    const date = new Date(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date <= today;
}

function validateFutureDate(dateStr) {
    if (!dateStr) return false;
    const date = new Date(dateStr);
    const today = new Date();
    today.setHours(0, 0, 0, 0);
    return date >= today;
}

function validateTimeRange(startTime, endTime) {
    if (!startTime || !endTime) return false;
    return endTime > startTime;
}

function showError(field, message) {
    hideError(field);

    field.classList.add('is-invalid');
    field.classList.remove('is-valid');

    const errorDiv = document.createElement('div');
    errorDiv.className = 'invalid-feedback';
    errorDiv.textContent = message;
    field.parentNode.appendChild(errorDiv);
}

function hideError(field) {
    field.classList.remove('is-invalid');

    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
}

function showSuccess(field) {
    hideError(field);
    field.classList.add('is-valid');
    field.classList.remove('is-invalid');
}

function clearValidation(field) {
    field.classList.remove('is-valid', 'is-invalid');
    const existingError = field.parentNode.querySelector('.invalid-feedback');
    if (existingError) {
        existingError.remove();
    }
}

function validateField(field) {
    const value = field.value.trim();
    const type = field.type;
    const name = field.name;

    if (field.hasAttribute('required') && !value) {
        showError(field, 'This field is required');
        return false;
    }

    if (value) {
        if (type === 'email' || name === 'email') {
            if (!validateEmail(value)) {
                showError(field, 'Please enter a valid email address');
                return false;
            }
        } else if (type === 'tel' || name === 'phone') {
            if (!validatePhone(value)) {
                showError(field, 'Please enter a valid phone number (10-15 digits)');
                return false;
            }
        } else if (type === 'password') {
            const result = validatePassword(value);
            if (!result.valid) {
                showError(field, result.message);
                return false;
            }
        } else if (type === 'date') {
            if (name === 'dob' && !validatePastDate(value)) {
                showError(field, 'Date of birth cannot be in the future');
                return false;
            } else if (name === 'date' && !validateFutureDate(value)) {
                showError(field, 'Date must be today or in the future');
                return false;
            }
        }

        const minLength = field.getAttribute('minlength');
        if (minLength && value.length < parseInt(minLength)) {
            showError(field, `Minimum length is ${minLength} characters`);
            return false;
        }
    }

    if (value) {
        showSuccess(field);
    } else {
        clearValidation(field);
    }
    return true;
}

function initFormValidation(formSelector) {
    const form = typeof formSelector === 'string'
        ? document.querySelector(formSelector)
        : formSelector;

    if (!form) return;

    const fields = form.querySelectorAll('input, textarea, select');
    fields.forEach(field => {
        field.addEventListener('blur', function () {
            validateField(this);
        });

        field.addEventListener('focus', function () {
            if (this.classList.contains('is-invalid')) {
            }
        });

        field.addEventListener('input', function () {
            if (this.classList.contains('is-invalid') || this.classList.contains('is-valid')) {
                validateField(this);
            }
        });
    });

    form.addEventListener('submit', function (e) {
        let isValid = true;

        fields.forEach(field => {
            if (!validateField(field)) {
                isValid = false;
            }
        });

        const startTime = form.querySelector('[name="start_time"]');
        const endTime = form.querySelector('[name="end_time"]');
        if (startTime && endTime && startTime.value && endTime.value) {
            if (!validateTimeRange(startTime.value, endTime.value)) {
                showError(endTime, 'End time must be after start time');
                isValid = false;
            }
        }

        if (!isValid) {
            e.preventDefault();
            const firstError = form.querySelector('.is-invalid');
            if (firstError) {
                firstError.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstError.focus();
            }
        }
    });
}

document.addEventListener('DOMContentLoaded', function () {
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        initFormValidation(form);
    });
});
