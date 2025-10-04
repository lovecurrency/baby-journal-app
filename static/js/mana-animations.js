/**
 * Baby Activity Journal - Mana-Style Animations
 * Advanced parallax, scroll reveals, and micro-interactions
 */

document.addEventListener('DOMContentLoaded', function() {

    // === DETECT MOBILE/TOUCH DEVICE ===
    const isMobile = window.innerWidth <= 768;
    const isTouchDevice = 'ontouchstart' in window || navigator.maxTouchPoints > 0;

    // === MOBILE NAVIGATION MENU ===
    function setupMobileNav() {
        // Create mobile menu toggle button
        const nav = document.querySelector('.navbar-custom');
        if (!nav) return;

        const toggleBtn = document.createElement('button');
        toggleBtn.className = 'mobile-menu-toggle';
        toggleBtn.innerHTML = '<i class="bi bi-list"></i>';
        toggleBtn.setAttribute('aria-label', 'Open menu');

        // Create mobile menu
        const mobileMenu = document.createElement('div');
        mobileMenu.className = 'mobile-nav-menu';
        const navLinks = document.querySelector('.nav-links-wrapper');
        mobileMenu.innerHTML = `
            <button class="mobile-nav-close" aria-label="Close menu">
                <i class="bi bi-x-lg"></i>
            </button>
            ${navLinks?.innerHTML || ''}
        `;

        // Create overlay
        const overlay = document.createElement('div');
        overlay.className = 'mobile-overlay';

        // Add to DOM - append toggle button next to nav-links-wrapper
        const navParent = nav.querySelector('.d-flex');
        navParent?.appendChild(toggleBtn);
        document.body.appendChild(mobileMenu);
        document.body.appendChild(overlay);

        // Toggle menu
        toggleBtn.addEventListener('click', () => {
            mobileMenu.classList.add('active');
            overlay.classList.add('active');
            document.body.style.overflow = 'hidden';
        });

        // Close menu
        const closeMenu = () => {
            mobileMenu.classList.remove('active');
            overlay.classList.remove('active');
            document.body.style.overflow = '';
        };

        mobileMenu.querySelector('.mobile-nav-close')?.addEventListener('click', closeMenu);
        overlay.addEventListener('click', closeMenu);

        // Close on link click
        mobileMenu.querySelectorAll('a').forEach(link => {
            link.addEventListener('click', closeMenu);
        });

        // Close on escape key
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && mobileMenu.classList.contains('active')) {
                closeMenu();
            }
        });
    }

    // Always setup mobile nav (CSS controls visibility)
    setupMobileNav();

    // ===  PARALLAX BACKGROUND SYSTEM ===
    function createParallaxBackground() {
        const parallaxContainer = document.createElement('div');
        parallaxContainer.className = 'parallax-background';

        // Create floating SVG elements (baby-themed with animals!)
        const svgs = [
            createFloatingCloud(),
            createFloatingStar(),
            createFloatingHeart(),
            createElephant(),
            createGiraffe(),
            createBunny(),
            createDuck(),
            createTeddyBear(),
            createOwl(),
            createButterfly(),
            createTurtle()
        ];

        svgs.forEach((svg, index) => {
            const floatingEl = document.createElement('div');
            floatingEl.className = 'floating-element';
            // Add animal-specific animation class
            if (index >= 3) {
                floatingEl.classList.add('floating-animal');
            }
            floatingEl.innerHTML = svg;
            parallaxContainer.appendChild(floatingEl);
        });

        document.body.prepend(parallaxContainer);
    }

    // Mobile-optimized animal background
    function createMobileAnimals() {
        const animalContainer = document.createElement('div');
        animalContainer.className = 'mobile-animals';

        // Fewer, larger animals for mobile
        const mobileAnimals = [
            createElephant(),
            createBunny(),
            createButterfly()
        ];

        mobileAnimals.forEach((svg, index) => {
            const animalEl = document.createElement('div');
            animalEl.className = 'mobile-floating-animal';
            animalEl.innerHTML = svg;
            animalContainer.appendChild(animalEl);
        });

        document.body.prepend(animalContainer);
    }

    function createFloatingCloud() {
        return `<svg width="120" height="80" viewBox="0 0 120 80" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M30 50c-10 0-18-8-18-18s8-18 18-18c2 0 4 0 6 1 3-8 11-14 20-14 12 0 22 10 22 22 0 1 0 2-1 3 9 1 16 9 16 18 0 10-8 18-18 18H30z" fill="#4A90E2" opacity="0.6"/>
        </svg>`;
    }

    function createFloatingStar() {
        return `<svg width="80" height="80" viewBox="0 0 80 80" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M40 5l8 24h25l-20 15 8 24-21-15-21 15 8-24-20-15h25z" fill="#F5A623" opacity="0.6"/>
        </svg>`;
    }

    function createFloatingHeart() {
        return `<svg width="100" height="100" viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M50 85c-1 0-2-1-3-1C20 65 10 55 10 40c0-10 7-17 17-17 6 0 12 3 16 8 4-5 10-8 16-8 10 0 17 7 17 17 0 15-10 25-37 44-1 0-2 1-3 1z" fill="#E72F63" opacity="0.6"/>
        </svg>`;
    }

    // === BABY ANIMAL SVGs ===
    function createElephant() {
        return `<svg width="140" height="120" viewBox="0 0 140 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <ellipse cx="70" cy="70" rx="45" ry="40" fill="#4A90E2" opacity="0.7"/>
            <ellipse cx="55" cy="60" rx="8" ry="10" fill="#2B3D73" opacity="0.8"/>
            <ellipse cx="85" cy="60" rx="8" ry="10" fill="#2B3D73" opacity="0.8"/>
            <path d="M45 85 Q40 100 35 110" stroke="#4A90E2" stroke-width="6" stroke-linecap="round" opacity="0.7"/>
            <path d="M95 85 Q100 100 105 110" stroke="#4A90E2" stroke-width="6" stroke-linecap="round" opacity="0.7"/>
            <path d="M60 45 Q50 25 45 10" stroke="#4A90E2" stroke-width="8" stroke-linecap="round" opacity="0.7"/>
            <circle cx="50" cy="65" r="3" fill="#0E0E0E" opacity="0.9"/>
            <circle cx="90" cy="65" r="3" fill="#0E0E0E" opacity="0.9"/>
        </svg>`;
    }

    function createGiraffe() {
        return `<svg width="100" height="160" viewBox="0 0 100 160" fill="none" xmlns="http://www.w3.org/2000/svg">
            <rect x="40" y="40" width="20" height="80" rx="10" fill="#F5A623" opacity="0.7"/>
            <circle cx="50" cy="30" r="20" fill="#F5A623" opacity="0.7"/>
            <circle cx="45" cy="25" r="3" fill="#0E0E0E" opacity="0.9"/>
            <circle cx="55" cy="25" r="3" fill="#0E0E0E" opacity="0.9"/>
            <rect x="43" y="10" width="4" height="8" rx="2" fill="#F5A623" opacity="0.7"/>
            <rect x="53" y="10" width="4" height="8" rx="2" fill="#F5A623" opacity="0.7"/>
            <circle cx="35" cy="20" r="4" fill="#F5A623" opacity="0.7"/>
            <circle cx="50" cy="60" r="5" fill="#F5A623" opacity="0.7"/>
            <circle cx="45" cy="90" r="4" fill="#F5A623" opacity="0.7"/>
        </svg>`;
    }

    function createBunny() {
        return `<svg width="100" height="120" viewBox="0 0 100 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <ellipse cx="50" cy="70" rx="30" ry="35" fill="#D4C5F9" opacity="0.7"/>
            <ellipse cx="35" cy="35" rx="8" ry="25" fill="#D4C5F9" opacity="0.7"/>
            <ellipse cx="65" cy="35" rx="8" ry="25" fill="#D4C5F9" opacity="0.7"/>
            <circle cx="45" cy="65" r="3" fill="#E72F63" opacity="0.9"/>
            <circle cx="55" cy="65" r="3" fill="#E72F63" opacity="0.9"/>
            <circle cx="50" cy="100" r="10" fill="#D4C5F9" opacity="0.7"/>
            <path d="M40 75 Q50 78 60 75" stroke="#E72F63" stroke-width="2" stroke-linecap="round" opacity="0.7"/>
        </svg>`;
    }

    function createDuck() {
        return `<svg width="120" height="100" viewBox="0 0 120 100" fill="none" xmlns="http://www.w3.org/2000/svg">
            <ellipse cx="70" cy="60" rx="35" ry="30" fill="#F5A623" opacity="0.7"/>
            <circle cx="55" cy="45" r="22" fill="#F5A623" opacity="0.7"/>
            <path d="M30 45 Q25 48 25 52 Q25 56 30 58" fill="#F15B40" opacity="0.8"/>
            <circle cx="50" cy="42" r="3" fill="#0E0E0E" opacity="0.9"/>
            <ellipse cx="90" cy="75" rx="15" ry="8" fill="#F5A623" opacity="0.7"/>
        </svg>`;
    }

    function createTeddyBear() {
        return `<svg width="110" height="120" viewBox="0 0 110 120" fill="none" xmlns="http://www.w3.org/2000/svg">
            <circle cx="30" cy="30" r="15" fill="#F15B40" opacity="0.7"/>
            <circle cx="80" cy="30" r="15" fill="#F15B40" opacity="0.7"/>
            <circle cx="55" cy="50" r="30" fill="#F15B40" opacity="0.7"/>
            <ellipse cx="55" cy="95" rx="25" ry="20" fill="#F15B40" opacity="0.7"/>
            <circle cx="48" cy="45" r="3" fill="#0E0E0E" opacity="0.9"/>
            <circle cx="62" cy="45" r="3" fill="#0E0E0E" opacity="0.9"/>
            <path d="M50 55 Q55 58 60 55" stroke="#0E0E0E" stroke-width="2" stroke-linecap="round" opacity="0.8"/>
            <circle cx="55" cy="52" r="4" fill="#0E0E0E" opacity="0.7"/>
        </svg>`;
    }

    function createOwl() {
        return `<svg width="100" height="110" viewBox="0 0 100 110" fill="none" xmlns="http://www.w3.org/2000/svg">
            <ellipse cx="50" cy="60" rx="35" ry="40" fill="#2C9BA3" opacity="0.7"/>
            <circle cx="35" cy="50" r="15" fill="#FAF8F5" opacity="0.8"/>
            <circle cx="65" cy="50" r="15" fill="#FAF8F5" opacity="0.8"/>
            <circle cx="35" cy="50" r="8" fill="#0E0E0E" opacity="0.9"/>
            <circle cx="65" cy="50" r="8" fill="#0E0E0E" opacity="0.9"/>
            <path d="M40 25 L30 15 M60 25 L70 15" stroke="#2C9BA3" stroke-width="4" stroke-linecap="round" opacity="0.7"/>
            <path d="M45 70 Q50 72 55 70" fill="#F5A623" opacity="0.7"/>
        </svg>`;
    }

    function createButterfly() {
        return `<svg width="100" height="80" viewBox="0 0 100 80" fill="none" xmlns="http://www.w3.org/2000/svg">
            <ellipse cx="30" cy="30" rx="20" ry="25" fill="#E72F63" opacity="0.7"/>
            <ellipse cx="70" cy="30" rx="20" ry="25" fill="#4A90E2" opacity="0.7"/>
            <ellipse cx="30" cy="55" rx="15" ry="20" fill="#F5A623" opacity="0.7"/>
            <ellipse cx="70" cy="55" rx="15" ry="20" fill="#2C9BA3" opacity="0.7"/>
            <rect x="48" y="20" width="4" height="50" rx="2" fill="#2B3D73" opacity="0.8"/>
            <path d="M50 20 L45 10 M50 20 L55 10" stroke="#2B3D73" stroke-width="2" opacity="0.7"/>
        </svg>`;
    }

    function createTurtle() {
        return `<svg width="120" height="90" viewBox="0 0 120 90" fill="none" xmlns="http://www.w3.org/2000/svg">
            <ellipse cx="60" cy="50" rx="40" ry="30" fill="#195E1C" opacity="0.7"/>
            <circle cx="45" cy="45" r="5" fill="#195E1C" opacity="0.7"/>
            <circle cx="60" cy="40" r="6" fill="#195E1C" opacity="0.7"/>
            <circle cx="75" cy="45" r="5" fill="#195E1C" opacity="0.7"/>
            <ellipse cx="35" cy="65" rx="10" ry="6" fill="#195E1C" opacity="0.7"/>
            <ellipse cx="85" cy="65" rx="10" ry="6" fill="#195E1C" opacity="0.7"/>
            <circle cx="95" cy="45" r="12" fill="#195E1C" opacity="0.7"/>
            <circle cx="93" cy="43" r="2" fill="#0E0E0E" opacity="0.9"/>
        </svg>`;
    }

    // Initialize parallax/animals based on device
    if (!isMobile) {
        createParallaxBackground();
    } else {
        createMobileAnimals();
    }

    // === TOUCH FEEDBACK FOR MOBILE ===
    if (isTouchDevice) {
        // Add touch ripple effect
        document.addEventListener('touchstart', function(e) {
            if (e.target.classList.contains('btn') ||
                e.target.closest('.btn') ||
                e.target.classList.contains('category-badge')) {
                const target = e.target.classList.contains('btn') ? e.target : e.target.closest('.btn');
                if (target) {
                    target.style.transform = 'scale(0.95)';
                    setTimeout(() => {
                        target.style.transform = '';
                    }, 150);
                }
            }
        }, { passive: true });

        // Add active class for touch feedback
        const touchTargets = document.querySelectorAll('.btn, .activity-card, .category-badge');
        touchTargets.forEach(target => {
            target.addEventListener('touchstart', function() {
                this.classList.add('touch-active');
            }, { passive: true });

            target.addEventListener('touchend', function() {
                setTimeout(() => {
                    this.classList.remove('touch-active');
                }, 300);
            }, { passive: true });
        });
    }

    // === SWIPE GESTURES FOR ACTIVITY CARDS (MOBILE) ===
    if (isTouchDevice) {
        const activityCards = document.querySelectorAll('.activity-card');
        activityCards.forEach(card => {
            let touchStartX = 0;
            let touchEndX = 0;

            card.addEventListener('touchstart', (e) => {
                touchStartX = e.changedTouches[0].screenX;
            }, { passive: true });

            card.addEventListener('touchend', (e) => {
                touchEndX = e.changedTouches[0].screenX;
                handleSwipe(card);
            }, { passive: true });

            function handleSwipe(element) {
                const swipeThreshold = 100;
                const swipeDistance = touchEndX - touchStartX;

                if (Math.abs(swipeDistance) > swipeThreshold) {
                    // Swipe detected
                    if (swipeDistance > 0) {
                        // Swipe right - could trigger edit
                        element.style.transform = 'translateX(20px)';
                        setTimeout(() => {
                            element.style.transform = '';
                        }, 300);
                    } else {
                        // Swipe left - could trigger delete
                        element.style.transform = 'translateX(-20px)';
                        setTimeout(() => {
                            element.style.transform = '';
                        }, 300);
                    }
                }
            }
        });
    }

    // === PARALLAX MOUSE MOVEMENT (DESKTOP ONLY) ===
    if (window.innerWidth > 768 && !isTouchDevice) {
        document.addEventListener('mousemove', function(e) {
            const moveX = (e.clientX / window.innerWidth - 0.5) * 30;
            const moveY = (e.clientY / window.innerHeight - 0.5) * 30;

            const floatingElements = document.querySelectorAll('.floating-element');
            floatingElements.forEach((el, index) => {
                const speed = (index + 1) * 0.3;
                el.style.transform = `translate(${moveX * speed}px, ${moveY * speed}px)`;
            });
        });
    }

    // === SCROLL REVEAL ANIMATIONS ===
    function setupScrollReveal() {
        const revealElements = document.querySelectorAll('.activity-card, .stat-card, .card');

        revealElements.forEach(el => {
            el.classList.add('scroll-reveal');
        });

        const observerOptions = {
            threshold: 0.1,
            rootMargin: '0px 0px -50px 0px'
        };

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('revealed');
                    observer.unobserve(entry.target);
                }
            });
        }, observerOptions);

        revealElements.forEach(el => observer.observe(el));
    }

    setupScrollReveal();

    // === ADVANCED BUTTON HOVER EFFECTS ===
    const buttons = document.querySelectorAll('.btn-custom, .btn');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function(e) {
            const rect = this.getBoundingClientRect();
            const x = e.clientX - rect.left;
            const y = e.clientY - rect.top;

            const ripple = document.createElement('span');
            ripple.style.cssText = `
                position: absolute;
                width: 4px;
                height: 4px;
                background: rgba(255, 255, 255, 0.5);
                border-radius: 50%;
                left: ${x}px;
                top: ${y}px;
                transform: translate(-50%, -50%) scale(0);
                animation: ripple-expand 0.6s ease-out;
                pointer-events: none;
            `;

            this.style.position = 'relative';
            this.appendChild(ripple);

            setTimeout(() => ripple.remove(), 600);
        });
    });

    // Add ripple animation CSS
    if (!document.querySelector('#ripple-animation')) {
        const style = document.createElement('style');
        style.id = 'ripple-animation';
        style.textContent = `
            @keyframes ripple-expand {
                to {
                    transform: translate(-50%, -50%) scale(50);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }

    // === COUNT-UP ANIMATION FOR STATS ===
    function animateNumber(element, target, duration = 1500) {
        const start = 0;
        const increment = target / (duration / 16);
        let current = start;

        const timer = setInterval(() => {
            current += increment;
            if (current >= target) {
                element.textContent = Math.round(target);
                clearInterval(timer);
            } else {
                element.textContent = Math.round(current);
            }
        }, 16);
    }

    const statNumbers = document.querySelectorAll('.stat-card h3');
    const numberObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const target = parseInt(entry.target.textContent);
                if (!isNaN(target) && target > 0) {
                    entry.target.textContent = '0';
                    setTimeout(() => {
                        animateNumber(entry.target, target);
                    }, 200);
                }
                numberObserver.unobserve(entry.target);
            }
        });
    }, { threshold: 0.5 });

    statNumbers.forEach(number => numberObserver.observe(number));

    // === FORM FOCUS EFFECTS ===
    const inputs = document.querySelectorAll('.form-control, .form-select');
    inputs.forEach(input => {
        input.addEventListener('focus', function() {
            this.style.transform = 'scale(1.01)';
            this.style.transition = 'transform 0.2s ease';
        });

        input.addEventListener('blur', function() {
            this.style.transform = 'scale(1)';
        });
    });

    // === CARD TILT EFFECT (3D) ===
    function setupCardTilt() {
        const cards = document.querySelectorAll('.stat-card, .card');

        cards.forEach(card => {
            card.addEventListener('mousemove', function(e) {
                if (window.innerWidth < 768) return;

                const rect = this.getBoundingClientRect();
                const x = e.clientX - rect.left;
                const y = e.clientY - rect.top;

                const centerX = rect.width / 2;
                const centerY = rect.height / 2;

                const rotateX = (y - centerY) / 20;
                const rotateY = (centerX - x) / 20;

                this.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) scale(1.02)`;
            });

            card.addEventListener('mouseleave', function() {
                this.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) scale(1)';
            });
        });
    }

    setupCardTilt();

    // === SMOOTH SCROLL FOR ANCHOR LINKS ===
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });

    // === LOADING ANIMATION FOR FORM SUBMISSIONS ===
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn && !submitBtn.disabled) {
                submitBtn.disabled = true;
                const originalText = submitBtn.innerHTML;
                submitBtn.innerHTML = '<span class="spinner-border spinner-border-sm me-2"></span>Processing...';

                // Re-enable after 5 seconds if something goes wrong
                setTimeout(() => {
                    if (submitBtn.disabled) {
                        submitBtn.disabled = false;
                        submitBtn.innerHTML = originalText;
                    }
                }, 5000);
            }
        });
    });

    // === CATEGORY BADGE HOVER EFFECT ===
    const badges = document.querySelectorAll('.category-badge');
    badges.forEach(badge => {
        badge.addEventListener('mouseenter', function() {
            this.style.transform = 'scale(1.1) rotate(2deg)';
        });

        badge.addEventListener('mouseleave', function() {
            this.style.transform = 'scale(1) rotate(0deg)';
        });
    });

    // === ACTIVITY CARD SEQUENTIAL ANIMATION ===
    const activityCards = document.querySelectorAll('.activity-card');
    activityCards.forEach((card, index) => {
        card.style.opacity = '0';
        card.style.transform = 'translateY(20px)';

        setTimeout(() => {
            card.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
            card.style.opacity = '1';
            card.style.transform = 'translateY(0)';
        }, index * 100);
    });

    // === IMAGE DUOTONE EFFECT ON HOVER ===
    const images = document.querySelectorAll('img');
    images.forEach(img => {
        img.addEventListener('mouseenter', function() {
            this.style.filter = 'contrast(1.1) saturate(1.2)';
            this.style.transition = 'filter 0.3s ease';
        });

        img.addEventListener('mouseleave', function() {
            this.style.filter = 'contrast(1) saturate(1)';
        });
    });

    // === PAGE TRANSITION EFFECT ===
    window.addEventListener('beforeunload', function() {
        document.body.style.opacity = '0';
        document.body.style.transition = 'opacity 0.3s ease';
    });

    // Fade in on load
    document.body.style.opacity = '0';
    setTimeout(() => {
        document.body.style.transition = 'opacity 0.5s ease';
        document.body.style.opacity = '1';
    }, 100);

    // === PARALLAX SCROLL EFFECT ===
    window.addEventListener('scroll', function() {
        const scrolled = window.pageYOffset;
        const parallaxElements = document.querySelectorAll('.floating-element');

        parallaxElements.forEach((el, index) => {
            const speed = (index + 1) * 0.5;
            el.style.transform = `translateY(${scrolled * speed}px)`;
        });
    });

    // === CONFETTI EFFECT ===
    function createConfetti(x, y) {
        const colors = ['#4A90E2', '#E72F63', '#F5A623', '#2C9BA3', '#F15B40', '#D4C5F9'];
        const confettiCount = isMobile ? 30 : 50;

        for (let i = 0; i < confettiCount; i++) {
            const confetti = document.createElement('div');
            confetti.className = 'confetti';
            confetti.style.cssText = `
                position: fixed;
                width: ${Math.random() * 10 + 5}px;
                height: ${Math.random() * 10 + 5}px;
                background: ${colors[Math.floor(Math.random() * colors.length)]};
                left: ${x}px;
                top: ${y}px;
                border-radius: ${Math.random() > 0.5 ? '50%' : '0'};
                pointer-events: none;
                z-index: 9999;
                opacity: 1;
                transform: rotate(${Math.random() * 360}deg);
            `;

            document.body.appendChild(confetti);

            const angle = Math.random() * Math.PI * 2;
            const velocity = Math.random() * 200 + 100;
            const vx = Math.cos(angle) * velocity;
            const vy = Math.sin(angle) * velocity - 200;

            animateConfetti(confetti, vx, vy);
        }
    }

    function animateConfetti(element, vx, vy) {
        let x = parseFloat(element.style.left);
        let y = parseFloat(element.style.top);
        let opacity = 1;
        const gravity = 500;
        let rotation = Math.random() * 360;
        const rotationSpeed = Math.random() * 10 - 5;

        const startTime = Date.now();

        function update() {
            const elapsed = (Date.now() - startTime) / 1000;

            x += vx * elapsed / 10;
            y += (vy + gravity * elapsed) * elapsed / 10;
            rotation += rotationSpeed;
            opacity = Math.max(0, 1 - elapsed);

            element.style.left = x + 'px';
            element.style.top = y + 'px';
            element.style.opacity = opacity;
            element.style.transform = `rotate(${rotation}deg)`;

            if (opacity > 0 && y < window.innerHeight + 100) {
                requestAnimationFrame(update);
            } else {
                element.remove();
            }
        }

        requestAnimationFrame(update);
    }

    // === SPARKLE EFFECT ===
    function createSparkle(x, y) {
        const sparkle = document.createElement('div');
        sparkle.className = 'sparkle';
        sparkle.innerHTML = '✨';
        sparkle.style.cssText = `
            position: fixed;
            left: ${x}px;
            top: ${y}px;
            font-size: 20px;
            pointer-events: none;
            z-index: 9999;
            animation: sparkle-burst 0.8s ease-out forwards;
        `;

        document.body.appendChild(sparkle);
        setTimeout(() => sparkle.remove(), 800);
    }

    // Add sparkle animation CSS
    if (!document.querySelector('#sparkle-animation')) {
        const style = document.createElement('style');
        style.id = 'sparkle-animation';
        style.textContent = `
            @keyframes sparkle-burst {
                0% {
                    transform: scale(0) rotate(0deg);
                    opacity: 1;
                }
                50% {
                    transform: scale(1.5) rotate(180deg);
                    opacity: 1;
                }
                100% {
                    transform: scale(0) rotate(360deg);
                    opacity: 0;
                }
            }
        `;
        document.head.appendChild(style);
    }

    // Add confetti on successful form submissions
    const originalFetch = window.fetch;
    window.fetch = function(...args) {
        return originalFetch.apply(this, args).then(response => {
            if (response.ok && args[0].includes('/api/')) {
                // Success! Show confetti
                setTimeout(() => {
                    createConfetti(window.innerWidth / 2, window.innerHeight / 2);
                }, 100);
            }
            return response;
        });
    };

    // Add sparkle trail on mousemove (desktop only)
    if (!isMobile && !isTouchDevice) {
        let sparkleTimeout;
        document.addEventListener('mousemove', (e) => {
            clearTimeout(sparkleTimeout);
            sparkleTimeout = setTimeout(() => {
                if (Math.random() > 0.95) { // 5% chance
                    createSparkle(e.clientX, e.clientY);
                }
            }, 50);
        });
    }

    // Add confetti to quick action buttons
    document.querySelectorAll('.btn-custom, .btn-outline-primary, .btn-outline-success').forEach(btn => {
        btn.addEventListener('click', function(e) {
            if (this.textContent.includes('Add') || this.textContent.includes('Log') || this.textContent.includes('Import')) {
                createSparkle(e.clientX, e.clientY);
            }
        });
    });

    console.log('🎨 Mana-style animations with animals initialized! 🐘🦒🐰');
});
