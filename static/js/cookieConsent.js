
document.addEventListener("DOMContentLoaded", () => {
    const modal = document.getElementById("cookieConsentModal");
    
    if (!modal) return;

    if (!localStorage.getItem("cookieConsent")) {
        modal.style.display = "flex";
    }
});

function acceptCookies() {
	localStorage.setItem('cookieConsent', 'accepted');
	document.getElementById('cookieConsentModal').style.display = 'none';
	loadAnalytics(); // Función para cargar Google Analytics
}

function rejectCookies() {
	localStorage.setItem('cookieConsent', 'rejected');
	document.getElementById('cookieConsentModal').style.display = 'none';
}

function loadAnalytics() {
	if (localStorage.getItem('cookieConsent') === 'accepted') {
		    // Código de Google Analytics
		    var script = document.createElement('script');
		    script.async = true;
		    script.src = 'https://www.googletagmanager.com/gtag/js?id=G-8KDXTV9J8K';
		    document.head.appendChild(script);

		    script.onload = function() {
		    window.dataLayer = window.dataLayer || [];
		    function gtag() { dataLayer.push(arguments); }
			    gtag('js', new Date());
			    gtag('config', 'G-8KDXTV9J8K');
		    };
	}
}
