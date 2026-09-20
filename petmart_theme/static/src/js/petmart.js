/* PETSMART homepage: "Add to Cart" on product cards (uses the standard shop route). */
document.addEventListener('click', async (ev) => {
    const btn = ev.target.closest('.pm-add');
    if (!btn || btn.disabled) {
        return;
    }
    btn.disabled = true;
    const label = btn.textContent;
    btn.textContent = 'Adding…';
    try {
        const response = await fetch('/shop/cart/add', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                jsonrpc: '2.0',
                method: 'call',
                params: {
                    product_template_id: parseInt(btn.dataset.productTemplateId, 10),
                    product_id: parseInt(btn.dataset.productId, 10),
                    quantity: 1,
                },
            }),
        });
        const data = await response.json();
        if (data.error) {
            throw new Error(data.error.data ? data.error.data.message : 'error');
        }
        window.location.href = '/shop/cart';
    } catch (e) {
        btn.textContent = label;
        btn.disabled = false;
    }
});
