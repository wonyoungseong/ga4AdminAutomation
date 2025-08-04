/**
 * GA4 Admin - Role-based UI Components Library
 * Enhanced component system with accessibility and mobile support
 */

// Global configuration
const GA4Admin = {
    config: {
        apiBase: '/api',
        theme: {
            current: localStorage.getItem('user-role') || 'viewer',
            transitions: true
        },
        accessibility: {
            announcements: true,
            focusManagement: true,
            keyboardNavigation: true
        },
        mobile: {
            touchTargets: 44, // minimum touch target size in pixels
            swipeThreshold: 50,
            tapDelay: 300
        }
    },
    
    // Component registry
    components: new Map(),
    
    // Event system
    events: new EventTarget(),
    
    // Utility functions
    utils: {}
};

// Theme Management
GA4Admin.theme = {
    /**
     * Set user role theme
     * @param {string} role - User role (super_admin, admin, requester, viewer)
     */
    setRole(role) {
        const validRoles = ['super_admin', 'admin', 'requester', 'viewer'];
        if (!validRoles.includes(role)) {
            console.warn(`Invalid role: ${role}. Using 'viewer' as fallback.`);
            role = 'viewer';
        }
        
        document.documentElement.setAttribute('data-role', role);
        localStorage.setItem('user-role', role);
        GA4Admin.config.theme.current = role;
        
        // Announce theme change to screen readers
        this.announceToScreenReader(`Theme changed to ${role.replace('_', ' ')} mode`);
        
        // Emit theme change event
        GA4Admin.events.dispatchEvent(new CustomEvent('themeChanged', {
            detail: { role, timestamp: Date.now() }
        }));
    },
    
    /**
     * Get current theme colors
     * @returns {Object} Theme color object
     */
    getColors() {
        const style = getComputedStyle(document.documentElement);
        return {
            primary: style.getPropertyValue('--role-primary').trim(),
            secondary: style.getPropertyValue('--role-secondary').trim(),
            accent: style.getPropertyValue('--role-accent').trim(),
            background: style.getPropertyValue('--role-background').trim(),
            surface: style.getPropertyValue('--role-surface').trim(),
            text: style.getPropertyValue('--role-text').trim(),
            textSecondary: style.getPropertyValue('--role-text-secondary').trim()
        };
    },
    
    /**
     * Apply custom theme overrides
     * @param {Object} overrides - Color overrides
     */
    applyOverrides(overrides) {
        const root = document.documentElement;
        Object.entries(overrides).forEach(([key, value]) => {
            root.style.setProperty(`--role-${key}`, value);
        });
    },
    
    /**
     * Announce changes to screen readers
     * @param {string} message - Message to announce
     */
    announceToScreenReader(message) {
        if (!GA4Admin.config.accessibility.announcements) return;
        
        const announcement = document.createElement('div');
        announcement.setAttribute('aria-live', 'polite');
        announcement.setAttribute('aria-atomic', 'true');
        announcement.className = 'sr-only';
        announcement.textContent = message;
        
        document.body.appendChild(announcement);
        setTimeout(() => document.body.removeChild(announcement), 1000);
    }
};

// Component System
GA4Admin.components = {
    /**
     * Register a new component
     * @param {string} name - Component name
     * @param {Function} factory - Component factory function
     */
    register(name, factory) {
        GA4Admin.components.set(name, factory);
    },
    
    /**
     * Create component instance
     * @param {string} name - Component name
     * @param {Object} options - Component options
     * @returns {Object} Component instance
     */
    create(name, options = {}) {
        const factory = GA4Admin.components.get(name);
        if (!factory) {
            throw new Error(`Component '${name}' not found`);
        }
        return factory(options);
    },
    
    /**
     * Initialize all components on page
     */
    initializeAll() {
        // Initialize data-component elements
        document.querySelectorAll('[data-component]').forEach(element => {
            const componentName = element.dataset.component;
            const options = this.parseDataAttributes(element);
            
            try {
                const component = this.create(componentName, {
                    element,
                    ...options
                });
                element._ga4Component = component;
            } catch (error) {
                console.error(`Failed to initialize component ${componentName}:`, error);
            }
        });
    },
    
    /**
     * Parse data attributes as component options
     * @param {Element} element - DOM element
     * @returns {Object} Parsed options
     */
    parseDataAttributes(element) {
        const options = {};
        Array.from(element.attributes).forEach(attr => {
            if (attr.name.startsWith('data-') && attr.name !== 'data-component') {
                const key = attr.name.slice(5).replace(/-([a-z])/g, (g) => g[1].toUpperCase());
                let value = attr.value;
                
                // Try to parse as JSON for complex values
                try {
                    value = JSON.parse(value);
                } catch {
                    // Keep as string if not valid JSON
                }
                
                options[key] = value;
            }
        });
        return options;
    }
};

// Notification System
GA4Admin.notifications = {
    /**
     * Show notification
     * @param {string} type - Notification type (success, error, warning, info)
     * @param {string} message - Notification message
     * @param {Object} options - Additional options
     */
    show(type, message, options = {}) {
        const {
            duration = 5000,
            actions = [],
            persistent = false,
            role = 'status'
        } = options;
        
        const notification = this.createNotificationElement(type, message, actions, role);
        this.displayNotification(notification, duration, persistent);
        
        // Announce to screen readers
        GA4Admin.theme.announceToScreenReader(message);
        
        return notification;
    },
    
    /**
     * Create notification DOM element
     */
    createNotificationElement(type, message, actions, role) {
        const notification = document.createElement('div');
        notification.className = `
            fixed top-4 right-4 z-50 max-w-sm w-full bg-white shadow-lg 
            rounded-lg pointer-events-auto ring-1 ring-black ring-opacity-5 
            overflow-hidden animate-slide-up
        `;
        notification.setAttribute('role', role);
        notification.setAttribute('aria-live', 'polite');
        
        const colors = {
            success: { bg: 'bg-green-50', border: 'border-green-200', icon: 'check-circle', iconColor: 'text-green-600' },
            error: { bg: 'bg-red-50', border: 'border-red-200', icon: 'alert-circle', iconColor: 'text-red-600' },
            warning: { bg: 'bg-yellow-50', border: 'border-yellow-200', icon: 'alert-triangle', iconColor: 'text-yellow-600' },
            info: { bg: 'bg-blue-50', border: 'border-blue-200', icon: 'info', iconColor: 'text-blue-600' }
        };
        
        const config = colors[type] || colors.info;
        
        notification.innerHTML = `
            <div class="p-4 ${config.bg} border-l-4 ${config.border}">
                <div class="flex">
                    <div class="flex-shrink-0">
                        <i data-lucide="${config.icon}" class="h-5 w-5 ${config.iconColor}"></i>
                    </div>
                    <div class="ml-3 flex-1">
                        <p class="text-sm font-medium text-gray-900">${message}</p>
                        ${actions.length > 0 ? this.createActionButtons(actions) : ''}
                    </div>
                    <div class="ml-auto pl-3">
                        <button 
                            class="inline-flex text-gray-400 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-gray-500 rounded"
                            onclick="this.closest('.fixed').remove()"
                            aria-label="Close notification">
                            <i data-lucide="x" class="h-5 w-5"></i>
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        return notification;
    },
    
    /**
     * Create action buttons for notifications
     */
    createActionButtons(actions) {
        return `
            <div class="mt-2 flex space-x-2">
                ${actions.map(action => `
                    <button 
                        class="btn btn-sm btn-ghost"
                        onclick="${action.onclick}"
                        ${action.ariaLabel ? `aria-label="${action.ariaLabel}"` : ''}>
                        ${action.icon ? `<i data-lucide="${action.icon}" class="h-4 w-4 mr-1"></i>` : ''}
                        ${action.label}
                    </button>
                `).join('')}
            </div>
        `;
    },
    
    /**
     * Display notification with auto-removal
     */
    displayNotification(notification, duration, persistent) {
        document.body.appendChild(notification);
        
        // Initialize Lucide icons
        if (typeof lucide !== 'undefined') {
            lucide.createIcons();
        }
        
        // Auto remove if not persistent
        if (!persistent && duration > 0) {
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.classList.add('animate-fade-out');
                    setTimeout(() => notification.remove(), 300);
                }
            }, duration);
        }
    }
};

// Mobile Utilities
GA4Admin.mobile = {
    /**
     * Check if device is mobile
     * @returns {boolean} True if mobile device
     */
    isMobile() {
        return window.innerWidth < 768 || 'ontouchstart' in window;
    },
    
    /**
     * Add touch-friendly behavior to element
     * @param {Element} element - DOM element
     * @param {Object} options - Touch options
     */
    addTouchSupport(element, options = {}) {
        if (!this.isMobile()) return;
        
        const {
            tapDelay = GA4Admin.config.mobile.tapDelay,
            swipeThreshold = GA4Admin.config.mobile.swipeThreshold,
            onTap,
            onSwipe
        } = options;
        
        let startX, startY, startTime;
        
        element.addEventListener('touchstart', (e) => {
            const touch = e.touches[0];
            startX = touch.clientX;
            startY = touch.clientY;
            startTime = Date.now();
        }, { passive: true });
        
        element.addEventListener('touchend', (e) => {
            if (!startX || !startY) return;
            
            const touch = e.changedTouches[0];
            const deltaX = touch.clientX - startX;
            const deltaY = touch.clientY - startY;
            const deltaTime = Date.now() - startTime;
            
            // Check for tap
            if (Math.abs(deltaX) < 10 && Math.abs(deltaY) < 10 && deltaTime < tapDelay) {
                if (onTap) onTap(e);
            }
            
            // Check for swipe
            else if (Math.abs(deltaX) > swipeThreshold || Math.abs(deltaY) > swipeThreshold) {
                if (onSwipe) {
                    const direction = Math.abs(deltaX) > Math.abs(deltaY) 
                        ? (deltaX > 0 ? 'right' : 'left')
                        : (deltaY > 0 ? 'down' : 'up');
                    onSwipe(direction, { deltaX, deltaY, deltaTime });
                }
            }
            
            startX = startY = startTime = null;
        }, { passive: true });
    },
    
    /**
     * Ensure touch targets meet minimum size requirements
     */
    optimizeTouchTargets() {
        if (!this.isMobile()) return;
        
        const minSize = GA4Admin.config.mobile.touchTargets;
        const selectors = 'button, a, input, select, textarea, [role="button"], [tabindex="0"]';
        
        document.querySelectorAll(selectors).forEach(element => {
            const rect = element.getBoundingClientRect();
            if (rect.width < minSize || rect.height < minSize) {
                element.classList.add('touch-target');
            }
        });
    }
};

// Accessibility Utilities
GA4Admin.accessibility = {
    /**
     * Enhance keyboard navigation
     */
    enhanceKeyboardNavigation() {
        // Escape key handling
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.handleEscapeKey(e);
            }
        });
        
        // Focus management for modals and dropdowns
        this.setupFocusTrapping();
        
        // Skip links
        this.addSkipLinks();
    },
    
    /**
     * Handle escape key press
     */
    handleEscapeKey(event) {
        // Close modals
        const openModal = document.querySelector('.modal.open, [role="dialog"][aria-hidden="false"]');
        if (openModal) {
            this.closeModal(openModal);
            return;
        }
        
        // Close dropdowns
        const openDropdown = document.querySelector('.dropdown.open, [aria-expanded="true"]');
        if (openDropdown) {
            this.closeDropdown(openDropdown);
            return;
        }
        
        // Clear search
        const searchInput = document.activeElement;
        if (searchInput && searchInput.matches('input[type="search"], input[role="searchbox"]')) {
            searchInput.value = '';
            searchInput.dispatchEvent(new Event('input'));
        }
    },
    
    /**
     * Setup focus trapping for modals
     */
    setupFocusTrapping() {
        document.addEventListener('focusin', (e) => {
            const modal = e.target.closest('[role="dialog"]');
            if (modal && modal.getAttribute('aria-hidden') === 'false') {
                this.trapFocusInModal(modal, e);
            }
        });
    },
    
    /**
     * Trap focus within modal
     */
    trapFocusInModal(modal, event) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstFocusable = focusableElements[0];
        const lastFocusable = focusableElements[focusableElements.length - 1];
        
        if (event.shiftKey && event.target === firstFocusable) {
            event.preventDefault();
            lastFocusable.focus();
        } else if (!event.shiftKey && event.target === lastFocusable) {
            event.preventDefault();
            firstFocusable.focus();
        }
    },
    
    /**
     * Add skip links for keyboard navigation
     */
    addSkipLinks() {
        if (document.querySelector('.skip-links')) return;
        
        const skipLinks = document.createElement('div');
        skipLinks.className = 'skip-links';
        skipLinks.innerHTML = `
            <a href="#main-content" class="sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-0 bg-blue-600 text-white p-2 rounded z-50">
                Skip to main content
            </a>
            <a href="#main-navigation" class="sr-only focus:not-sr-only focus:absolute focus:top-0 focus:left-20 bg-blue-600 text-white p-2 rounded z-50">
                Skip to navigation
            </a>
        `;
        
        document.body.insertBefore(skipLinks, document.body.firstChild);
    },
    
    /**
     * Update ARIA attributes dynamically
     */
    updateAriaAttributes(element, attributes) {
        Object.entries(attributes).forEach(([key, value]) => {
            if (key.startsWith('aria-') || key === 'role') {
                element.setAttribute(key, value);
            }
        });
    }
};

// Data Management
GA4Admin.data = {
    /**
     * Fetch data from API
     * @param {string} endpoint - API endpoint
     * @param {Object} options - Fetch options
     * @returns {Promise} API response
     */
    async fetch(endpoint, options = {}) {
        const url = `${GA4Admin.config.apiBase}${endpoint}`;
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            }
        };
        
        try {
            const response = await fetch(url, { ...defaultOptions, ...options });
            
            if (!response.ok) {
                throw new Error(`HTTP ${response.status}: ${response.statusText}`);
            }
            
            return await response.json();
        } catch (error) {
            console.error(`API request failed for ${endpoint}:`, error);
            GA4Admin.notifications.show('error', `Failed to load data: ${error.message}`);
            throw error;
        }
    },
    
    /**
     * Cache management
     */
    cache: new Map(),
    
    /**
     * Get cached data or fetch if not available
     */
    async getCached(key, fetcher, ttl = 300000) { // 5 minutes default TTL
        const cached = this.cache.get(key);
        if (cached && Date.now() - cached.timestamp < ttl) {
            return cached.data;
        }
        
        const data = await fetcher();
        this.cache.set(key, {
            data,
            timestamp: Date.now()
        });
        
        return data;
    }
};

// Animation Utilities
GA4Admin.animations = {
    /**
     * Animate element with CSS classes
     * @param {Element} element - DOM element
     * @param {string} animation - Animation class name
     * @param {number} duration - Animation duration in ms
     * @returns {Promise} Promise that resolves when animation completes
     */
    animate(element, animation, duration = 300) {
        return new Promise((resolve) => {
            element.classList.add(animation);
            
            const handleAnimationEnd = () => {
                element.classList.remove(animation);
                element.removeEventListener('animationend', handleAnimationEnd);
                resolve();
            };
            
            element.addEventListener('animationend', handleAnimationEnd);
            
            // Fallback timeout
            setTimeout(() => {
                if (element.classList.contains(animation)) {
                    handleAnimationEnd();
                }
            }, duration + 50);
        });
    },
    
    /**
     * Stagger animations for multiple elements
     * @param {NodeList|Array} elements - Elements to animate
     * @param {string} animation - Animation class
     * @param {number} delay - Delay between each element in ms
     */
    stagger(elements, animation, delay = 100) {
        elements.forEach((element, index) => {
            setTimeout(() => {
                this.animate(element, animation);
            }, index * delay);
        });
    }
};

// Initialize GA4Admin when DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    // Set initial theme
    const savedRole = localStorage.getItem('user-role') || 'viewer';
    GA4Admin.theme.setRole(savedRole);
    
    // Initialize accessibility features
    if (GA4Admin.config.accessibility.keyboardNavigation) {
        GA4Admin.accessibility.enhanceKeyboardNavigation();
    }
    
    // Optimize for mobile
    if (GA4Admin.mobile.isMobile()) {
        GA4Admin.mobile.optimizeTouchTargets();
    }
    
    // Initialize components
    GA4Admin.components.initializeAll();
    
    // Initialize Lucide icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }
    
    // Emit ready event
    GA4Admin.events.dispatchEvent(new CustomEvent('ga4AdminReady', {
        detail: { timestamp: Date.now() }
    }));
    
    console.log('GA4Admin initialized successfully');
});

// Export for global access
window.GA4Admin = GA4Admin;
