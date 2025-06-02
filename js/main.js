/**
 * Datash - Cyberpunk Theme
 * Main JavaScript
 * Handles all interactive elements and animations
 */

document.addEventListener('DOMContentLoaded', () => {
    // Initialize all components
    initMobileMenu();
    initSmoothScrolling();
    initFaqAccordion();
    initHeaderScroll();
    initAnimations();
    initParallaxEffects();
    initGlitchEffects();
});

/**
 * Mobile Menu Toggle
 * Handles the mobile menu open/close functionality
 */
function initMobileMenu() {
    const menuBtn = document.querySelector('.menu-btn');
    const navLinks = document.querySelector('.nav-links');
    
    if (!menuBtn || !navLinks) return;
    
    menuBtn.addEventListener('click', () => {
        // Toggle active class for menu button and nav links
        navLinks.classList.toggle('active');
        
        // Add glitch animation when opening/closing
        document.body.classList.add('page-transition');
        setTimeout(() => {
            document.body.classList.remove('page-transition');
        }, 500);
    });
    
    // Close menu when clicking on a link
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            navLinks.classList.remove('active');
        });
    });
    
    // Close menu when clicking outside
    document.addEventListener('click', (e) => {
        if (!e.target.closest('nav') && navLinks.classList.contains('active')) {
            navLinks.classList.remove('active');
        }
    });
}

/**
 * Smooth Scrolling
 * Enables smooth scrolling to anchor links
 */
function initSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            
            const target = document.querySelector(this.getAttribute('href'));
            if (!target) return;
            
            // Add glitch animation when navigating
            document.body.classList.add('page-transition');
            
            // Scroll to target with smooth behavior
            window.scrollTo({
                top: target.offsetTop - 70, // Adjust for header
                behavior: 'smooth'
            });
            
            // Update active nav link
            updateActiveNavLink(this.getAttribute('href'));
            
            setTimeout(() => {
                document.body.classList.remove('page-transition');
            }, 500);
        });
    });
    
    // Update active nav link on scroll
    window.addEventListener('scroll', () => {
        const scrollPosition = window.scrollY;
        
        document.querySelectorAll('section').forEach(section => {
            const sectionTop = section.offsetTop - 100;
            const sectionBottom = sectionTop + section.offsetHeight;
            
            if (scrollPosition >= sectionTop && scrollPosition < sectionBottom) {
                updateActiveNavLink(`#${section.id}`);
            }
        });
    });
}

/**
 * Updates the active navigation link
 * @param {string} href - The href of the active link
 */
function updateActiveNavLink(href) {
    document.querySelectorAll('.nav-link').forEach(link => {
        link.classList.remove('active');
        if (link.getAttribute('href') === href) {
            link.classList.add('active');
        }
    });
}

/**
 * FAQ Accordion
 * Handles the expand/collapse functionality of FAQ items
 */
function initFaqAccordion() {
    const faqItems = document.querySelectorAll('.faq-item');
    
    faqItems.forEach(item => {
        const question = item.querySelector('.faq-question');
        
        question.addEventListener('click', () => {
            // Toggle active class on the current item
            item.classList.toggle('active');
            
            // Add glitch effect when toggling
            item.classList.add('page-transition');
            setTimeout(() => {
                item.classList.remove('page-transition');
            }, 300);
            
            // Close other items
            faqItems.forEach(otherItem => {
                if (otherItem !== item && otherItem.classList.contains('active')) {
                    otherItem.classList.remove('active');
                }
            });
        });
    });
}

/**
 * Header Scroll Effect
 * Changes header appearance on scroll
 */
function initHeaderScroll() {
    const header = document.querySelector('header');
    if (!header) return;
    
    window.addEventListener('scroll', () => {
        if (window.scrollY > 50) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
    });
}

/**
 * Animations
 * Initializes animations for elements as they come into view
 */
function initAnimations() {
    // Create intersection observer
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.classList.add('animated');
                
                // For specific animation types
                if (entry.target.classList.contains('animate-in')) {
                    entry.target.style.opacity = '1';
                    entry.target.style.transform = 'translateY(0)';
                }
            }
        });
    }, {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    });
    
    // Observe elements with animation classes
    document.querySelectorAll('.animate-in, .feature-card, .download-card, .faq-item').forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(el);
    });
    
    // Staggered animation for lists
    document.querySelectorAll('.staggered-list').forEach(list => {
        const items = list.querySelectorAll('li, .item');
        items.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.transform = 'translateY(20px)';
            item.style.transition = `opacity 0.5s ease ${index * 0.1}s, transform 0.5s ease ${index * 0.1}s`;
            observer.observe(item);
        });
    });
}

/**
 * Parallax Effects
 * Creates parallax scrolling effects for background elements
 */
function initParallaxEffects() {
    const parallaxElements = document.querySelectorAll('.parallax');
    
    window.addEventListener('mousemove', (e) => {
        const mouseX = e.clientX / window.innerWidth;
        const mouseY = e.clientY / window.innerHeight;
        
        parallaxElements.forEach(el => {
            const speed = el.getAttribute('data-speed') || 0.05;
            const x = (mouseX - 0.5) * speed * 100;
            const y = (mouseY - 0.5) * speed * 100;
            
            el.style.transform = `translate(${x}px, ${y}px)`;
        });
    });
    
    // Hologram parallax on scroll
    const hologram = document.querySelector('.hologram-container');
    if (hologram) {
        window.addEventListener('scroll', () => {
            const scrollY = window.scrollY;
            hologram.style.transform = `translateY(${scrollY * 0.05}px) rotate(${scrollY * 0.02}deg)`;
        });
    }
}

/**
 * Glitch Effects
 * Adds random glitch effects to elements
 */
function initGlitchEffects() {
    const glitchElements = document.querySelectorAll('.glitch-text');
    
    // Set data-text attribute for glitch effect
    glitchElements.forEach(el => {
        if (!el.getAttribute('data-text')) {
            el.setAttribute('data-text', el.textContent);
        }
    });
    
    // Random glitch effect on hover
    document.querySelectorAll('.download-card, .feature-card').forEach(card => {
        card.addEventListener('mouseenter', () => {
            card.classList.add('page-transition');
            setTimeout(() => {
                card.classList.remove('page-transition');
            }, 300);
        });
    });
    
    // Random glitch effect throughout the page
    setInterval(() => {
        const randomEl = glitchElements[Math.floor(Math.random() * glitchElements.length)];
        if (randomEl) {
            randomEl.classList.add('hard-glitch');
            setTimeout(() => {
                randomEl.classList.remove('hard-glitch');
            }, 200);
        }
    }, 5000);
}

/**
 * Theme Utilities
 * Helper functions for theme elements
 */
const ThemeUtils = {
    // Add cyberpunk glitch effect to any element
    addGlitchEffect: (element, duration = 500) => {
        element.classList.add('page-transition');
        setTimeout(() => {
            element.classList.remove('page-transition');
        }, duration);
    },
    
    // Create holographic overlay for an element
    createHolographicOverlay: (element) => {
        const overlay = document.createElement('div');
        overlay.classList.add('hologram-overlay');
        element.appendChild(overlay);
        return overlay;
    },
    
    // Create typing animation
    typeText: (element, text, speed = 50) => {
        element.textContent = '';
        element.classList.add('typing');
        
        let i = 0;
        const typeInterval = setInterval(() => {
            if (i < text.length) {
                element.textContent += text.charAt(i);
                i++;
            } else {
                clearInterval(typeInterval);
                element.classList.remove('typing');
            }
        }, speed);
    }
};

// Export ThemeUtils for use in other scripts
window.ThemeUtils = ThemeUtils;

