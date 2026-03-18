/* ========================================
   RESPONSIVE BEHAVIOR - MOBILE FIRST
   ======================================== */

// Mobile Menu Toggle
document.addEventListener('DOMContentLoaded', function() {
  const mobileMenuToggle = document.querySelector('.mobile-menu-toggle');
  const mobileOverlay = document.querySelector('.mobile-overlay');
  const sidePanel = document.querySelector('.side-panel');
  const sidebarContainer = document.getElementById('sidebar-container');

  // Toggle mobile menu
  if (mobileMenuToggle) {
    mobileMenuToggle.addEventListener('click', function() {
      toggleMobileMenu();
    });
  }

  // Close menu when overlay is clicked
  if (mobileOverlay) {
    mobileOverlay.addEventListener('click', function() {
      closeMobileMenu();
    });
  }

  // Close menu when a nav link is clicked
  const navLinks = document.querySelectorAll('.side-panel .nav-links a, .side-panel .nav-links-account a');
  navLinks.forEach(link => {
    link.addEventListener('click', function() {
      if (window.innerWidth < 768) {
        closeMobileMenu();
      }
    });
  });

  // Handle window resize
  window.addEventListener('resize', function() {
    if (window.innerWidth >= 768) {
      closeMobileMenu();
    }
  });

  function toggleMobileMenu() {
    if (sidebarContainer) {
      sidebarContainer.classList.toggle('mobile-open');
    }
    if (sidePanel) {
      sidePanel.classList.toggle('mobile-open');
    }
    if (mobileOverlay) {
      mobileOverlay.classList.toggle('active');
    }
  }

  function closeMobileMenu() {
    if (sidebarContainer) {
      sidebarContainer.classList.remove('mobile-open');
    }
    if (sidePanel) {
      sidePanel.classList.remove('mobile-open');
    }
    if (mobileOverlay) {
      mobileOverlay.classList.remove('active');
    }
  }

  // Expose functions globally
  window.toggleMobileMenu = toggleMobileMenu;
  window.closeMobileMenu = closeMobileMenu;
});

/* ========================================
   RESPONSIVE TABLE HANDLING
   ======================================== */

// Make tables responsive on mobile
document.addEventListener('DOMContentLoaded', function() {
  const tables = document.querySelectorAll('table');
  
  tables.forEach(table => {
    // Add wrapper if not already wrapped
    if (!table.parentElement.classList.contains('table-wrap')) {
      const wrapper = document.createElement('div');
      wrapper.className = 'table-wrap';
      table.parentElement.insertBefore(wrapper, table);
      wrapper.appendChild(table);
    }
  });
});

/* ========================================
   RESPONSIVE MODAL HANDLING
   ======================================== */

// Handle modal responsiveness
document.addEventListener('DOMContentLoaded', function() {
  const modals = document.querySelectorAll('.modal-overlay');
  
  modals.forEach(modal => {
    // Close modal on overlay click
    modal.addEventListener('click', function(e) {
      if (e.target === this) {
        this.style.display = 'none';
      }
    });

    // Handle escape key
    document.addEventListener('keydown', function(e) {
      if (e.key === 'Escape' && modal.style.display !== 'none') {
        modal.style.display = 'none';
      }
    });
  });
});

/* ========================================
   RESPONSIVE FORM HANDLING
   ======================================== */

// Improve form input handling on mobile
document.addEventListener('DOMContentLoaded', function() {
  const inputs = document.querySelectorAll('input, select, textarea');
  
  inputs.forEach(input => {
    // Prevent zoom on iOS when focusing input
    input.addEventListener('focus', function() {
      if (window.innerWidth < 768) {
        // Scroll input into view
        setTimeout(() => {
          this.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 300);
      }
    });
  });
});

/* ========================================
   RESPONSIVE IMAGE HANDLING
   ======================================== */

// Make images responsive
document.addEventListener('DOMContentLoaded', function() {
  const images = document.querySelectorAll('img');
  
  images.forEach(img => {
    if (!img.style.maxWidth) {
      img.style.maxWidth = '100%';
      img.style.height = 'auto';
      img.style.display = 'block';
    }
  });
});

/* ========================================
   RESPONSIVE VIDEO HANDLING
   ======================================== */

// Make videos responsive
document.addEventListener('DOMContentLoaded', function() {
  const videos = document.querySelectorAll('video');
  
  videos.forEach(video => {
    if (!video.style.maxWidth) {
      video.style.maxWidth = '100%';
      video.style.height = 'auto';
      video.style.display = 'block';
    }
  });
});

/* ========================================
   RESPONSIVE BUTTON HANDLING
   ======================================== */

// Handle button responsiveness
document.addEventListener('DOMContentLoaded', function() {
  const buttons = document.querySelectorAll('.btn');
  
  buttons.forEach(btn => {
    // Ensure buttons are touch-friendly
    if (window.innerWidth < 768) {
      const height = window.getComputedStyle(btn).height;
      if (parseInt(height) < 44) {
        btn.style.minHeight = '44px';
      }
    }
  });
});

/* ========================================
   RESPONSIVE GRID HANDLING
   ======================================== */

// Handle grid responsiveness
document.addEventListener('DOMContentLoaded', function() {
  const grids = document.querySelectorAll('.grid, .grid-2, .grid-3, .grid-4');
  
  grids.forEach(grid => {
    // Ensure grids are responsive
    if (window.innerWidth < 768) {
      grid.style.gridTemplateColumns = '1fr';
    }
  });

  // Re-check on resize
  window.addEventListener('resize', function() {
    grids.forEach(grid => {
      if (window.innerWidth < 768) {
        grid.style.gridTemplateColumns = '1fr';
      } else if (grid.classList.contains('grid-2')) {
        grid.style.gridTemplateColumns = 'repeat(2, 1fr)';
      } else if (grid.classList.contains('grid-3')) {
        grid.style.gridTemplateColumns = 'repeat(3, 1fr)';
      } else if (grid.classList.contains('grid-4')) {
        grid.style.gridTemplateColumns = 'repeat(4, 1fr)';
      }
    });
  });
});

/* ========================================
   RESPONSIVE OVERFLOW HANDLING
   ======================================== */

// Prevent horizontal scrolling
document.addEventListener('DOMContentLoaded', function() {
  let overflowCheckTimeout;
  
  // Check for horizontal overflow
  function checkHorizontalOverflow() {
    clearTimeout(overflowCheckTimeout);
    
    overflowCheckTimeout = setTimeout(() => {
      const body = document.body;
      const html = document.documentElement;
      
      // Force overflow-x: hidden on body/html
      body.style.overflowX = 'hidden';
      html.style.overflowX = 'hidden';
      
      // Ensure table wrappers are scrollable
      const tableWraps = document.querySelectorAll('.table-wrap');
      tableWraps.forEach(wrap => {
        wrap.style.overflowX = 'auto';
        wrap.style.webkitOverflowScrolling = 'touch';
      });
    }, 100);
  }

  checkHorizontalOverflow();
  window.addEventListener('resize', checkHorizontalOverflow);
  window.addEventListener('load', checkHorizontalOverflow);
});

/* ========================================
   RESPONSIVE FONT SIZE ADJUSTMENT
   ======================================== */

// Adjust font sizes for readability on mobile
document.addEventListener('DOMContentLoaded', function() {
  function adjustFontSizes() {
    const width = window.innerWidth;
    const root = document.documentElement;
    
    if (width < 480) {
      // Extra small mobile
      root.style.setProperty('--font-size-4xl', '24px');
      root.style.setProperty('--font-size-3xl', '20px');
      root.style.setProperty('--font-size-2xl', '18px');
    } else if (width < 768) {
      // Mobile
      root.style.setProperty('--font-size-4xl', '28px');
      root.style.setProperty('--font-size-3xl', '24px');
      root.style.setProperty('--font-size-2xl', '20px');
    } else if (width < 992) {
      // Tablet
      root.style.setProperty('--font-size-4xl', '32px');
      root.style.setProperty('--font-size-3xl', '28px');
      root.style.setProperty('--font-size-2xl', '24px');
    } else {
      // Desktop
      root.style.setProperty('--font-size-4xl', '36px');
      root.style.setProperty('--font-size-3xl', '30px');
      root.style.setProperty('--font-size-2xl', '24px');
    }
  }

  adjustFontSizes();
  window.addEventListener('resize', adjustFontSizes);
});

/* ========================================
   RESPONSIVE SPACING ADJUSTMENT
   ======================================== */

// Adjust spacing for different screen sizes
document.addEventListener('DOMContentLoaded', function() {
  function adjustSpacing() {
    const width = window.innerWidth;
    const root = document.documentElement;
    
    if (width < 480) {
      // Extra small mobile
      root.style.setProperty('--space-lg', '12px');
      root.style.setProperty('--space-xl', '16px');
      root.style.setProperty('--space-2xl', '20px');
    } else if (width < 768) {
      // Mobile
      root.style.setProperty('--space-lg', '16px');
      root.style.setProperty('--space-xl', '20px');
      root.style.setProperty('--space-2xl', '24px');
    } else if (width < 992) {
      // Tablet
      root.style.setProperty('--space-lg', '20px');
      root.style.setProperty('--space-xl', '24px');
      root.style.setProperty('--space-2xl', '32px');
    } else {
      // Desktop
      root.style.setProperty('--space-lg', '24px');
      root.style.setProperty('--space-xl', '32px');
      root.style.setProperty('--space-2xl', '48px');
    }
  }

  adjustSpacing();
  window.addEventListener('resize', adjustSpacing);
});

/* ========================================
   RESPONSIVE CONTAINER PADDING
   ======================================== */

// Adjust container padding for different screen sizes
document.addEventListener('DOMContentLoaded', function() {
  function adjustContainerPadding() {
    const width = window.innerWidth;
    const root = document.documentElement;
    
    if (width < 480) {
      root.style.setProperty('--container-padding', '8px');
    } else if (width < 768) {
      root.style.setProperty('--container-padding', '12px');
    } else if (width < 992) {
      root.style.setProperty('--container-padding', '16px');
    } else {
      root.style.setProperty('--container-padding', '24px');
    }
  }

  adjustContainerPadding();
  window.addEventListener('resize', adjustContainerPadding);
});

/* ========================================
   RESPONSIVE TOUCH HANDLING
   ======================================== */

// Improve touch handling on mobile
document.addEventListener('DOMContentLoaded', function() {
  if ('ontouchstart' in window) {
    // Add touch-friendly class to body
    document.body.classList.add('touch-device');
    
    // Increase touch target sizes
    const buttons = document.querySelectorAll('button, a, input[type="button"], input[type="submit"]');
    buttons.forEach(btn => {
      btn.style.minHeight = '44px';
      btn.style.minWidth = '44px';
    });
  }
});

/* ========================================
   RESPONSIVE VIEWPORT HANDLING
   ======================================== */

// Handle viewport changes
window.addEventListener('orientationchange', function() {
  // Reload or adjust layout on orientation change
  setTimeout(() => {
    window.scrollTo(0, 0);
  }, 100);
});

/* ========================================
   RESPONSIVE ACCESSIBILITY
   ======================================== */

// Improve accessibility on mobile
document.addEventListener('DOMContentLoaded', function() {
  // Ensure focus is visible
  document.addEventListener('keydown', function(e) {
    if (e.key === 'Tab') {
      document.body.classList.add('keyboard-nav');
    }
  });

  document.addEventListener('mousedown', function() {
    document.body.classList.remove('keyboard-nav');
  });
});

/* ========================================
   RESPONSIVE PERFORMANCE
   ======================================== */

// Optimize performance on mobile
document.addEventListener('DOMContentLoaded', function() {
  // Lazy load images on mobile
  if ('IntersectionObserver' in window) {
    const images = document.querySelectorAll('img[data-src]');
    const imageObserver = new IntersectionObserver((entries, observer) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          const img = entry.target;
          img.src = img.dataset.src;
          img.removeAttribute('data-src');
          observer.unobserve(img);
        }
      });
    });

    images.forEach(img => imageObserver.observe(img));
  }
});

/* ========================================
   RESPONSIVE DEBUG MODE
   ======================================== */

// Debug responsive behavior (optional)
window.debugResponsive = function() {
  console.log('Window width:', window.innerWidth);
  console.log('Window height:', window.innerHeight);
  console.log('Device pixel ratio:', window.devicePixelRatio);
  console.log('Is mobile:', window.innerWidth < 768);
  console.log('Is tablet:', window.innerWidth >= 768 && window.innerWidth < 992);
  console.log('Is desktop:', window.innerWidth >= 992);
};

// Export for use in console
window.debugResponsive();
