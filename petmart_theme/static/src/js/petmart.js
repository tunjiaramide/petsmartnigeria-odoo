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

/* Shop brand filter: "Find a brand" box and the "+ N more" link. */
document.addEventListener('input', (ev) => {
    const body = ev.target.closest('[data-pm-brandfilter]');
    if (!body || !ev.target.matches('input[type="search"]')) {
        return;
    }
    const term = ev.target.value.trim().toLowerCase();
    let shown = 0;
    body.querySelectorAll('.pm-brandlist > li').forEach((item) => {
        const match = item.querySelector('span').textContent.toLowerCase().includes(term);
        item.classList.toggle('d-none', !match);
        shown += match ? 1 : 0;
    });
    body.classList.toggle('is-searching', Boolean(term));
    body.querySelector('.pm-brandfilter__none').classList.toggle('d-none', shown > 0);
});
document.addEventListener('click', (ev) => {
    const more = ev.target.closest('.pm-brandfilter__more');
    if (!more) {
        return;
    }
    const open = more.closest('[data-pm-brandfilter]').classList.toggle('is-open');
    more.textContent = open ? more.dataset.less : more.dataset.more;
});
