// js/app.js
document.addEventListener('DOMContentLoaded', () => {
    // Estado del carrito
    let carrito = [];
    const numeroGeneralWhatsApp = "5217841234567"; // Reemplaza con tu número de Papantla/prueba

    // Elementos del DOM
    const botonesAgregar = document.querySelectorAll('.add-to-cart-btn');
    const badgeCarrito = document.querySelector('.cart-badge');
    const botonCarrito = document.getElementById('cart-btn');

    // 1. Lógica para agregar productos al pedido
    botonesAgregar.forEach(boton => {
        boton.addEventListener('click', (e) => {
            const tarjeta = e.target.closest('.producto-card');
            const titulo = tarjeta.querySelector('h3').innerText;
            const precioTexto = tarjeta.querySelector('.precio').innerText;
            const artesano = tarjeta.querySelector('.producto-autor').innerText;
            
            // Limpiar el precio para cálculos (quitar $ y MXN)
            const precio = parseFloat(precioTexto.replace(/[^0-9.-]+/g, ""));

            // Agregar al array del carrito
            carrito.push({
                producto: titulo,
                precio: precio,
                artesano: artesano
            });

            // Actualizar UI
            badgeCarrito.innerText = carrito.length;
            animarBotonCarrito();
            
            // Feedback visual rápido (estilo Emil Kowalski)
            const textoOriginal = boton.innerText;
            boton.innerText = "¡Añadido!";
            boton.style.backgroundColor = "#1EBE57";
            
            setTimeout(() => {
                boton.innerText = textoOriginal;
                boton.style.backgroundColor = ""; // Regresa al color original
            }, 800);
        });
    });

    // 2. Animación sutil de resorte al actualizar el carrito
    function animarBotonCarrito() {
        botonCarrito.style.transform = 'scale(1.1)';
        setTimeout(() => {
            botonCarrito.style.transform = 'scale(1)';
        }, 150);
    }

    // 3. Procesar el pedido hacia WhatsApp
    botonCarrito.addEventListener('click', () => {
        if (carrito.length === 0) {
            alert("Tu pedido está vacío. Explora nuestra galería de artesanías.");
            return;
        }

        // Construir el mensaje
        let mensaje = "Hola Vuelo y Tradición. Me interesa realizar el siguiente pedido de comercio justo:%0A%0A";
        let total = 0;

        carrito.forEach((item, index) => {
            mensaje += `${index + 1}. ${item.producto} (${item.artesano}) - $${item.precio}%0A`;
            total += item.precio;
        });

        mensaje += `%0A*Total estimado: $${total} MXN*%0A%0A¿Podrían indicarme los pasos para confirmar?`;

        // Abrir WhatsApp en una nueva pestaña
        const urlWhatsApp = `https://wa.me/${numeroGeneralWhatsApp}?text=${mensaje}`;
        window.open(urlWhatsApp, '_blank');
        
        // Opcional: Vaciar carrito después de enviar
        // carrito = [];
        // badgeCarrito.innerText = "0";
    });