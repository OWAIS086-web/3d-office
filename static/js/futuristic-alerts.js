// Futuristic Alert System
class FuturisticAlert {
    constructor() {
        this.createStyles();
    }

    createStyles() {
        if (document.getElementById('futuristic-alert-styles')) return;
        
        const style = document.createElement('style');
        style.id = 'futuristic-alert-styles';
        style.textContent = `
            .futuristic-alert-overlay {
                position: fixed;
                top: 0;
                left: 0;
                width: 100%;
                height: 100%;
                background: rgba(0, 0, 0, 0.8);
                backdrop-filter: blur(10px);
                z-index: 10000;
                display: flex;
                align-items: center;
                justify-content: center;
                animation: fadeIn 0.3s ease;
            }

            @keyframes fadeIn {
                from { opacity: 0; }
                to { opacity: 1; }
            }

            .futuristic-alert-content {
                background: rgba(0, 40, 60, 0.95);
                border: 2px solid rgba(0, 255, 255, 0.4);
                border-radius: 20px;
                padding: 30px;
                max-width: 500px;
                width: 90%;
                position: relative;
                overflow: hidden;
                animation: slideUp 0.3s ease;
                box-shadow: 0 0 50px rgba(0, 255, 255, 0.3);
            }

            @keyframes slideUp {
                from { transform: translateY(50px); opacity: 0; }
                to { transform: translateY(0); opacity: 1; }
            }

            .futuristic-alert-content::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(0, 255, 255, 0.1), transparent);
                animation: scan 4s infinite;
            }

            @keyframes scan {
                0% { left: -100%; }
                100% { left: 100%; }
            }

            .futuristic-alert-header {
                display: flex;
                align-items: center;
                margin-bottom: 20px;
                position: relative;
                z-index: 1;
            }

            .futuristic-alert-icon {
                font-size: 2rem;
                margin-right: 15px;
                text-shadow: 0 0 10px currentColor;
            }

            .futuristic-alert-title {
                font-size: 1.4rem;
                font-weight: bold;
                color: #ffffff;
                text-shadow: 0 0 10px rgba(255, 255, 255, 0.5);
            }

            .futuristic-alert-message {
                color: rgba(255, 255, 255, 0.9);
                font-size: 1rem;
                line-height: 1.5;
                margin-bottom: 25px;
                position: relative;
                z-index: 1;
            }

            .futuristic-alert-buttons {
                display: flex;
                gap: 15px;
                justify-content: flex-end;
                position: relative;
                z-index: 1;
            }

            .futuristic-alert-btn {
                padding: 12px 25px;
                border: none;
                border-radius: 8px;
                font-weight: 600;
                cursor: pointer;
                transition: all 0.3s ease;
                position: relative;
                overflow: hidden;
                text-transform: uppercase;
                letter-spacing: 1px;
            }

            .futuristic-alert-btn::before {
                content: '';
                position: absolute;
                top: 0;
                left: -100%;
                width: 100%;
                height: 100%;
                background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
                transition: left 0.5s;
            }

            .futuristic-alert-btn:hover::before {
                left: 100%;
            }

            .futuristic-alert-btn:hover {
                transform: translateY(-2px);
            }

            .futuristic-alert-btn-primary {
                background: linear-gradient(135deg, #00ff88, #00aaff);
                color: white;
                box-shadow: 0 4px 15px rgba(0, 255, 255, 0.3);
            }

            .futuristic-alert-btn-primary:hover {
                box-shadow: 0 8px 25px rgba(0, 255, 255, 0.5);
            }

            .futuristic-alert-btn-danger {
                background: linear-gradient(135deg, #ff4444, #cc3333);
                color: white;
                box-shadow: 0 4px 15px rgba(255, 68, 68, 0.3);
            }

            .futuristic-alert-btn-danger:hover {
                box-shadow: 0 8px 25px rgba(255, 68, 68, 0.5);
            }

            .futuristic-alert-btn-secondary {
                background: rgba(255, 255, 255, 0.1);
                color: #ffffff;
                border: 2px solid rgba(255, 255, 255, 0.3);
                box-shadow: 0 4px 15px rgba(255, 255, 255, 0.1);
            }

            .futuristic-alert-btn-secondary:hover {
                background: rgba(255, 255, 255, 0.2);
                box-shadow: 0 8px 25px rgba(255, 255, 255, 0.2);
            }

            /* Alert type colors */
            .futuristic-alert-success .futuristic-alert-icon {
                color: #00ff88;
            }

            .futuristic-alert-error .futuristic-alert-icon {
                color: #ff4444;
            }

            .futuristic-alert-warning .futuristic-alert-icon {
                color: #ffaa00;
            }

            .futuristic-alert-info .futuristic-alert-icon {
                color: #00aaff;
            }

            .futuristic-alert-confirm .futuristic-alert-icon {
                color: #ffaa00;
            }
        `;
        document.head.appendChild(style);
    }

    show(options) {
        const {
            type = 'info',
            title = 'Alert',
            message = '',
            confirmText = 'OK',
            cancelText = 'Cancel',
            showCancel = false,
            onConfirm = null,
            onCancel = null
        } = options;

        // Remove existing alerts
        this.removeAll();

        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'futuristic-alert-overlay';

        // Create content
        const content = document.createElement('div');
        content.className = `futuristic-alert-content futuristic-alert-${type}`;

        // Get icon based on type
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle',
            confirm: 'fas fa-question-circle'
        };

        content.innerHTML = `
            <div class="futuristic-alert-header">
                <i class="futuristic-alert-icon ${icons[type] || icons.info}"></i>
                <div class="futuristic-alert-title">${title}</div>
            </div>
            <div class="futuristic-alert-message">${message}</div>
            <div class="futuristic-alert-buttons">
                ${showCancel ? `<button class="futuristic-alert-btn futuristic-alert-btn-secondary" data-action="cancel">${cancelText}</button>` : ''}
                <button class="futuristic-alert-btn ${type === 'error' || type === 'confirm' ? 'futuristic-alert-btn-danger' : 'futuristic-alert-btn-primary'}" data-action="confirm">${confirmText}</button>
            </div>
        `;

        overlay.appendChild(content);
        document.body.appendChild(overlay);

        // Add event listeners
        const confirmBtn = content.querySelector('[data-action="confirm"]');
        const cancelBtn = content.querySelector('[data-action="cancel"]');

        confirmBtn.addEventListener('click', () => {
            this.remove(overlay);
            if (onConfirm) onConfirm();
        });

        if (cancelBtn) {
            cancelBtn.addEventListener('click', () => {
                this.remove(overlay);
                if (onCancel) onCancel();
            });
        }

        // Close on overlay click
        overlay.addEventListener('click', (e) => {
            if (e.target === overlay) {
                this.remove(overlay);
                if (onCancel) onCancel();
            }
        });

        // Close on Escape key
        const escapeHandler = (e) => {
            if (e.key === 'Escape') {
                this.remove(overlay);
                if (onCancel) onCancel();
                document.removeEventListener('keydown', escapeHandler);
            }
        };
        document.addEventListener('keydown', escapeHandler);

        return overlay;
    }

    remove(overlay) {
        if (overlay && overlay.parentNode) {
            overlay.style.animation = 'fadeOut 0.3s ease';
            setTimeout(() => {
                if (overlay.parentNode) {
                    overlay.parentNode.removeChild(overlay);
                }
            }, 300);
        }
    }

    removeAll() {
        const existingAlerts = document.querySelectorAll('.futuristic-alert-overlay');
        existingAlerts.forEach(alert => this.remove(alert));
    }

    // Convenience methods
    success(message, title = 'Success') {
        return this.show({
            type: 'success',
            title,
            message
        });
    }

    error(message, title = 'Error') {
        return this.show({
            type: 'error',
            title,
            message
        });
    }

    warning(message, title = 'Warning') {
        return this.show({
            type: 'warning',
            title,
            message
        });
    }

    info(message, title = 'Information') {
        return this.show({
            type: 'info',
            title,
            message
        });
    }

    confirm(message, title = 'Confirm', onConfirm = null, onCancel = null) {
        return this.show({
            type: 'confirm',
            title,
            message,
            showCancel: true,
            confirmText: 'Yes',
            cancelText: 'No',
            onConfirm,
            onCancel
        });
    }
}

// Create global instance
window.FAlert = new FuturisticAlert();

// Add fadeOut animation
const fadeOutStyle = document.createElement('style');
fadeOutStyle.textContent = `
    @keyframes fadeOut {
        from { opacity: 1; }
        to { opacity: 0; }
    }
`;
document.head.appendChild(fadeOutStyle);