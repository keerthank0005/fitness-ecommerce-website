// =====================================================
// ================= THEME CHANGE =======================
// =====================================================

document.querySelectorAll(".product-card").forEach(card => {
    card.addEventListener("click", function (e) {

        if (!e.target.classList.contains("buy-btn")) {

            const color = card.getAttribute("data-color");

            if (color) {
                document.body.style.background =
                    "linear-gradient(135deg, #0b0b0b," + color + ")";
            }
        }
    });
});


// =====================================================
// ================= HERO SCROLL =======================
// =====================================================

const heroBtn = document.querySelector(".hero-btn");

if (heroBtn) {
    heroBtn.addEventListener("click", () => {

        const gymSection = document.getElementById("gym-section");

        if (gymSection) {
            gymSection.scrollIntoView({
                behavior: "smooth"
            });
        }
    });
}


// =====================================================
// ================= AJAX ADD TO CART ==================
// =====================================================

document.addEventListener("DOMContentLoaded", function () {

    const forms = document.querySelectorAll(".add-to-cart-form");

    forms.forEach(form => {

        form.addEventListener("submit", function (e) {

            e.preventDefault();

            const formData = new FormData(form);

            fetch("/add_to_cart", {
                method: "POST",
                body: formData
            })
            .then(res => res.json())
            .then(data => {

                if (data.status === "success") {

                    updateCartCount(data.cart_count);
                    showPopup("Item added to cart 🛒");

                }

                if (data.status === "login_required") {
                    window.location.href = "/login";
                }

            })
            .catch(err => console.log(err));

        });

    });

});


// =====================================================
// ================= UPDATE CART COUNT =================
// =====================================================

function updateCartCount(count) {

    const cartCount = document.getElementById("cart-count");

    if (cartCount) {
        cartCount.innerText = count;

        cartCount.style.transform = "scale(1.3)";
        setTimeout(() => {
            cartCount.style.transform = "scale(1)";
        }, 200);
    }
}


// =====================================================
// ================= POPUP NOTIFICATION =================
// =====================================================

function showPopup(message) {

    const popup = document.createElement("div");
    popup.className = "cart-popup";
    popup.innerText = message;

    document.body.appendChild(popup);

    setTimeout(() => popup.classList.add("show"), 100);

    setTimeout(() => {
        popup.classList.remove("show");
        setTimeout(() => popup.remove(), 300);
    }, 2500);
}


// =====================================================
// ================= SUCCESS PAGE ANIMATION ============
// =====================================================

if (window.location.pathname.includes("success")) {

    const card = document.querySelector(".success-card");

    if (card) {

        card.style.transform = "scale(0)";
        card.style.transition = "0.4s ease";

        setTimeout(() => {
            card.style.transform = "scale(1)";
        }, 200);
    }
}


// =====================================================
// ================= PRODUCT FILTER ====================
// =====================================================

function showAll() {
    toggleSections(true, true);
}

function showGym() {
    toggleSections(true, false);
}

function showSports() {
    toggleSections(false, true);
}

function toggleSections(showGym, showSports) {

    const gym = document.getElementById("gym-section");
    const sports = document.getElementById("sports-section");

    if (gym) gym.style.display = showGym ? "block" : "none";
    if (sports) sports.style.display = showSports ? "block" : "none";
}
// Animate tracker when page loads
window.addEventListener("load", () => {

    document.querySelectorAll(".circle.active").forEach((el, index) => {

        el.style.opacity = 0;
        el.style.transform = "scale(0)";

        setTimeout(() => {
            el.style.opacity = 1;
            el.style.transform = "scale(1.2)";
        }, index * 200);

    });

});
function changeQty(name, change) {

    fetch("/update_quantity", {
        method: "POST",
        headers: {
            "Content-Type": "application/json"
        },
        body: JSON.stringify({
            name: name,
            change: change
        })
    })
    .then(res => res.json())
    .then(data => {

        if (data.status === "success") {
            location.reload(); // simple refresh (or we can do live update)
        }

    });
}


function removeItem(name) {

    fetch("/remove_from_cart", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `name=${name}`
    })
    .then(() => location.reload());
}

// ================= TOGGLE CART =================

function toggleCart() {

    document.getElementById("side-cart").classList.toggle("open");
    document.getElementById("cart-overlay").classList.toggle("show");

    loadCart(); // load items
}


// ================= LOAD CART =================

function loadCart() {

    fetch("/get_cart")
    .then(res => res.json())
    .then(data => {

        let container = document.getElementById("cart-items");
        let total = 0;

        container.innerHTML = "";

        data.cart.forEach(item => {

            total += item.price * item.quantity;

            container.innerHTML += `
                <div class="cart-item">
                    <div>
                        <h4>${item.name}</h4>
                        <p>₹${item.price} × ${item.quantity}</p>
                    </div>
                    <button onclick="removeItem('${item.name}')">❌</button>
                </div>
            `;
        });

        document.getElementById("cart-total").innerText = total;

    });
}


// ================= REMOVE ITEM =================

function removeItem(name) {

    fetch("/remove_from_cart", {
        method: "POST",
        headers: {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        body: `name=${name}`
    })
    .then(() => loadCart());
}

function payNow() {

    fetch("/create_order")
    .then(res => res.json())
    .then(data => {

        var options = {
            "key": data.key,
            "amount": data.amount,
            "currency": "INR",
            "name": "Fitness AI",
            "description": "Instant Checkout",
            "order_id": data.order_id,

            "handler": function (response){

                fetch("/payment_success", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json"
                    },
                    body: JSON.stringify(response)
                })
                .then(() => {
                    window.location.href = "/success";
                });

            }
        };

        var rzp = new Razorpay(options);
        rzp.open();

    });
}
function toggleCart() {

    document.getElementById("side-cart").classList.toggle("open");
    document.getElementById("cart-overlay").classList.toggle("show");

    loadCart();
    loadAIProducts(); // 🔥 ADD THIS
}

// Page Loaded Animation
document.addEventListener("DOMContentLoaded", () => {
    document.body.style.opacity = 0;
    setTimeout(() => {
        document.body.style.transition = "opacity 0.8s ease";
        document.body.style.opacity = 1;
    }, 100);
});


// WhatsApp Button Logic
const whatsappBtn = document.querySelector("a[href='https://whatsapp.com/']");

if (whatsappBtn) {
    whatsappBtn.addEventListener("click", (e) => {
        e.preventDefault();

        const phoneNumber = "917647709055"; // add country code
        const message = encodeURIComponent(
            "Hello FitAI, I want to become a seller on your platform."
        );

        const url = `https://wa.me/${phoneNumber}?text=${message}`;
        window.open(url, "_blank");
    });
}


// Email Button Logic
const emailBtn = document.querySelector("a[href*='mail.google.com']");

if (emailBtn) {
    emailBtn.addEventListener("click", (e) => {
        e.preventDefault();

        const email = "support@fitai.com";
        const subject = encodeURIComponent("Seller Registration - FitAI");
        const body = encodeURIComponent(
            "Hello,\n\nI am interested in selling on FitAI. Please guide me through the process.\n\nThank you."
        );

        const mailUrl = `mailto:${email}?subject=${subject}&body=${body}`;
        window.location.href = mailUrl;
    });
}


// Button Click Animation
const buttons = document.querySelectorAll("a");

buttons.forEach(btn => {
    btn.addEventListener("click", () => {
        btn.style.transform = "scale(0.95)";
        setTimeout(() => {
            btn.style.transform = "scale(1)";
        }, 150);
    });
});


// Scroll Reveal Animation
const elements = document.querySelectorAll("h1, h2, h3, p, li");

const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
        if (entry.isIntersecting) {
            entry.target.style.opacity = 1;
            entry.target.style.transform = "translateY(0)";
        }
    });
}, { threshold: 0.1 });

elements.forEach(el => {
    el.style.opacity = 0;
    el.style.transform = "translateY(20px)";
    el.style.transition = "all 0.6s ease";
    observer.observe(el);
});