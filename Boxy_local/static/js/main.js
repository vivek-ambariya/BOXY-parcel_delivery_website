// Boxy - Main JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Smooth scroll for anchor links
    initSmoothScroll();
    
    // Navbar active link highlight
    initNavbarActiveLinks();
    
    // Button hover effects
    initButtonHoverEffects();
    
    // Navbar scroll effect
    initNavbarScroll();
    
    // Hero scroll indicator
    initHeroScrollIndicator();
});

/**
 * Smooth scroll for anchor links
 */
function initSmoothScroll() {
    const links = document.querySelectorAll('a[href^="#"]');
    
    links.forEach(link => {
        link.addEventListener('click', function(e) {
            const href = this.getAttribute('href');
            
            // Skip empty hash or just #
            if (href === '#' || href === '') {
                return;
            }
            
            const target = document.querySelector(href);
            
            if (target) {
                e.preventDefault();
                
                const offsetTop = target.offsetTop - 80; // Account for sticky navbar
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
                
                // Update active nav link
                updateActiveNavLink(href);
            }
        });
    });
}

/**
 * Navbar active link highlight
 */
function initNavbarActiveLinks() {
    // Set initial active link based on current hash
    if (window.location.hash) {
        updateActiveNavLink(window.location.hash);
    } else {
        updateActiveNavLink('#home');
    }
    
    // Update active link on scroll
    window.addEventListener('scroll', function() {
        const sections = document.querySelectorAll('section[id]');
        const scrollPosition = window.scrollY + 100;
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.offsetHeight;
            const sectionId = section.getAttribute('id');
            
            if (scrollPosition >= sectionTop && scrollPosition < sectionTop + sectionHeight) {
                updateActiveNavLink('#' + sectionId);
            }
        });
    });
}

/**
 * Update active nav link
 */
function updateActiveNavLink(hash) {
    const navLinks = document.querySelectorAll('.nav-link');
    
    navLinks.forEach(link => {
        link.classList.remove('active');
        
        if (link.getAttribute('href') === hash) {
            link.classList.add('active');
        }
    });
}

/**
 * Button hover effects
 */
function initButtonHoverEffects() {
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-2px)';
        });
        
        button.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0)';
        });
    });
}

/**
 * Navbar scroll effect
 */
function initNavbarScroll() {
    const navbar = document.querySelector('.navbar');
    let lastScroll = 0;
    
    window.addEventListener('scroll', function() {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            navbar.style.boxShadow = '0 2px 10px rgba(0,0,0,0.1)';
        } else {
            navbar.style.boxShadow = 'none';
        }
        
        lastScroll = currentScroll;
    });
}

/**
 * Hero scroll indicator - smooth scroll to next section
 */
function initHeroScrollIndicator() {
    const scrollIndicator = document.querySelector('.hero-scroll-indicator');
    
    if (scrollIndicator) {
        scrollIndicator.addEventListener('click', function() {
            // Find the next section after hero
            const heroSection = document.querySelector('.hero-section-modern');
            if (heroSection) {
                const nextSection = heroSection.nextElementSibling;
                if (nextSection) {
                    const offsetTop = nextSection.offsetTop - 80; // Account for sticky navbar
                    window.scrollTo({
                        top: offsetTop,
                        behavior: 'smooth'
                    });
                } else {
                    // If no next section, scroll to top of page
                    window.scrollTo({
                        top: 0,
                        behavior: 'smooth'
                    });
                }
            }
        });
        
        // Hide scroll indicator when scrolled past hero section
        window.addEventListener('scroll', function() {
            const heroSection = document.querySelector('.hero-section-modern');
            if (heroSection) {
                const heroBottom = heroSection.offsetTop + heroSection.offsetHeight;
                if (window.pageYOffset > heroBottom - 100) {
                    scrollIndicator.style.opacity = '0';
                    scrollIndicator.style.pointerEvents = 'none';
                } else {
                    scrollIndicator.style.opacity = '1';
                    scrollIndicator.style.pointerEvents = 'auto';
                }
            }
        });
    }
}

/**
 * Intersection Observer for fade-in animations
 */
function initScrollAnimations() {
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    const animatedElements = document.querySelectorAll('.feature-card, .step-card, .stat-card, .service-item');
    
    animatedElements.forEach(el => {
        el.style.opacity = '0';
        el.style.transform = 'translateY(30px)';
        el.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(el);
    });
}

// Initialize scroll animations
document.addEventListener('DOMContentLoaded', function() {
    initScrollAnimations();
    initSplineScene();
});

/**
 * Initialize Spline 3D Scene
 * Replace the placeholder with your Spline embed URL
 */
function initSplineScene() {
    const splineContainer = document.getElementById('spline-container');
    const splineIframe = document.getElementById('spline-embed');
    const splinePlaceholder = splineContainer?.querySelector('.spline-placeholder');
    
    if (!splineContainer || !splineIframe) return;
    
    // TODO: Replace this URL with your Spline scene URL
    // You can get this from Spline by:
    // 1. Export your scene from Spline
    // 2. Get the embed URL or use Spline's runtime
    // 3. Replace the src below with your Spline scene URL
    const splineSceneUrl = ''; // Add your Spline scene URL here
    
    // If you're using Spline's runtime library instead of iframe:
    // Uncomment and use the code below
    
    /*
    // Load Spline runtime
    const script = document.createElement('script');
    script.type = 'module';
    script.src = 'https://unpkg.com/@splinetool/runtime@1.0.0/build/runtime.js';
    document.head.appendChild(script);
    
    script.onload = function() {
        // Import and load your Spline scene
        import('https://unpkg.com/@splinetool/runtime@1.0.0/build/runtime.js').then((SplineRuntime) => {
            const app = new SplineRuntime.Application();
            app.load('YOUR_SPLINE_SCENE_URL.splinecode').then(() => {
                splineContainer.appendChild(app.canvas);
                if (splinePlaceholder) {
                    splinePlaceholder.style.display = 'none';
                }
            });
        });
    };
    */
    
    // Iframe method (simpler, recommended)
    if (splineSceneUrl) {
        splineIframe.src = splineSceneUrl;
        splineIframe.onload = function() {
            if (splinePlaceholder) {
                splinePlaceholder.style.display = 'none';
            }
        };
    } else {
        // Show placeholder if no URL is provided
        console.log('Spline scene URL not configured. Please add your Spline scene URL in main.js');
    }
}
